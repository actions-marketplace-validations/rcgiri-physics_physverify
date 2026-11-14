"""Regenerate every table of the 100-repository three-way study from claims.csv.

    python scripts/study100.py PATH/TO/claims.csv [--out TABLES.md] [--open OPEN_ITEMS.csv]

The study compares AI code reviewers, per-repository test scripts and `physverify scan` on 100 physics
repositories. claims.csv has one row per claim (columns: claim_id, repo_id, repo_set, method, model,
defect_id, label, ...); the data are kept private until the study is published. Scoring rules, fixed in
the study's analysis plan: a claim is 'confirmed' only by a run against a reference written from the
physics; a repository has a false alarm for a method when that method raised at least one 'rejected'
claim on it. Counts hold within the sample only. Uses only the standard library.
"""
import argparse
import collections
import csv
import math
import sys

LABELS = ['confirmed', 'rejected', 'not_decidable', 'not_physics', 'unadjudicated', 'not_a_claim']
Z = 1.959963984540054  # 95 % two-sided


def wilson(k, n):
    """95 % Wilson score interval for k successes in n trials (Wilson 1927)."""
    if n == 0:
        return (float('nan'), float('nan'))
    p = k / n; d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def frac(k, n):
    if n == 0:
        return f'{k}/0'
    lo, hi = wilson(k, n)
    return f'{k}/{n} ({100 * k / n:.0f}%, {100 * lo:.0f}-{100 * hi:.0f}%)'


def method_key(r):
    return r['model'] if r['method'] == 'A_ai' else r['method']


def table(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    out += ['| ' + ' | '.join(str(x) for x in r) + ' |' for r in rows]
    return '\n'.join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('claims'); ap.add_argument('--out')
    ap.add_argument('--open', help='write every unadjudicated or not-decidable claim to this CSV')
    a = ap.parse_args(argv)
    rows = list(csv.DictReader(open(a.claims, encoding='utf-8')))
    repos = {}
    for r in rows:
        repos[r['repo_id']] = r['repo_set']
    sets = collections.Counter(repos.values())
    methods = sorted({method_key(r) for r in rows}, key=lambda m: (m.startswith(('B_', 'C_', 'C2_')), m))
    by = collections.defaultdict(list)
    for r in rows:
        by[method_key(r)].append(r)
    S = []
    S.append(f'Sample: {len(repos)} repositories ({sets["defect"]} with a posted defect, {sets["clean"]} "clean"); '
             f'{len(rows)} claims. Counts within this sample only; 95% Wilson intervals in brackets.\n')

    # 1. Claims by label.
    t = []
    for m in methods:
        c = collections.Counter(r['label'] for r in by[m]); n = len(by[m])
        t.append([m, n] + [c[l] for l in LABELS])
    S.append('## 1. Claims raised, by label\n\n' + table(['method', 'claims'] + LABELS, t))

    # 1b. Precision among adjudicated confirmed/rejected.
    t = []
    for m in methods:
        c = collections.Counter(r['label'] for r in by[m])
        t.append([m, frac(c['confirmed'], c['confirmed'] + c['rejected'])])
    S.append('## 1b. Precision: confirmed / (confirmed + rejected)\n\n' + table(['method', 'precision'], t))

    # 2. Repositories with >= 1 confirmed / >= 1 false alarm.
    t = []
    for m in methods:
        conf = {r['repo_id'] for r in by[m] if r['label'] == 'confirmed'}
        fa = {r['repo_id'] for r in by[m] if r['label'] == 'rejected'}
        row = [m]
        for s in ('all', 'defect', 'clean'):
            ids = [i for i, v in repos.items() if s == 'all' or v == s]
            row += [frac(len(conf & set(ids)), len(ids))]
        for s in ('all', 'clean'):
            ids = [i for i, v in repos.items() if s == 'all' or v == s]
            row += [frac(len(fa & set(ids)), len(ids))]
        t.append(row)
    S.append('## 2. Repositories with at least one confirmed defect / at least one false alarm\n\n'
             + table(['method', 'confirmed: all', 'confirmed: defect set', 'confirmed: clean set',
                      'false alarm: all', 'false alarm: clean set'], t))

    # 3. Posted defects recovered (any label; defect_id from the B_script rows).
    posted = {r['defect_id']: r['label'] for r in rows if r['method'] == 'B_script'}
    t = []
    for m in methods:
        got = {r['defect_id'] for r in by[m] if r['defect_id'] in posted}
        phys = [d for d in posted if posted[d] == 'confirmed']
        reps = {r['repo_id'] for r in by[m] if r['defect_id'] in posted}
        t.append([m, frac(len(got), len(posted)), frac(len(got & set(phys)), len(phys)),
                  frac(len(reps), sets['defect'])])
    S.append('## 3. Posted (known) defects recovered\n\n'
             + table(['method', 'all posted defects', 'physics defects only', 'defect repos with >=1 recovered'], t))

    # 4. Overlap of confirmed defects between the three ways.
    way = lambda r: 'AI' if r['method'] == 'A_ai' else 'script' if r['method'] == 'B_script' else 'scan'
    found = collections.defaultdict(set)
    for r in rows:
        if r['label'] == 'confirmed' and r['defect_id']:
            found[r['defect_id']].add(way(r))
    cnt = collections.Counter(len(v) for v in found.values())
    combos = collections.Counter(' + '.join(sorted(v)) for v in found.values())
    S.append('## 4. Overlap of confirmed defects (AI = any model; scan = scan or scan --run)\n\n'
             + table(['found by', 'defects'], [['one way only', cnt[1]], ['two ways', cnt[2]], ['all three', cnt[3]],
                                               ['total', len(found)]])
             + '\n\n' + table(['combination', 'defects'], sorted(combos.items(), key=lambda x: -x[1])))
    unid = sum(1 for r in rows if r['label'] == 'confirmed' and not r['defect_id'])
    if unid:
        S.append(f'{unid} confirmed claims have no defect ID and are left out of the overlap.')

    # 5. Paired comparison on the same posted defects: every method against every other one. Each method
    #    is scored on the same defects, so the pairs show which defects one finds and the other misses.
    others = [m for m in methods if m != 'B_script']
    got = {m: {r['defect_id'] for r in by[m] if r['defect_id'] in posted} for m in others}
    t = []
    for i, m1 in enumerate(others):
        for m2 in others[i + 1:]:
            A, B = got[m1], got[m2]
            t.append([m1, m2, len(A & B), len(A - B), len(B - A), len(posted) - len(A | B)])
    S.append(f'## 5. Paired comparison on the same {len(posted)} posted defects\n\n'
             + table(['first', 'second', 'both found', 'first only', 'second only', 'neither'], t))

    # 6. Repeated runs.
    runs = collections.defaultdict(set)
    for r in rows:
        runs[method_key(r)].add(r['run'])
    rep = [m for m, v in runs.items() if len(v) > 1]
    S.append('## 6. Repeated runs of the same model\n\n' + (
        'Methods with more than one run: ' + ', '.join(rep) if rep else
        'Not available: every method has one run per repository in claims.csv.'))

    # 7. What is not settled.
    open_rows = [r for r in rows if r['label'] in ('unadjudicated', 'not_decidable')]
    t = collections.Counter((method_key(r), r['repo_set'], r['label']) for r in open_rows)
    S.append('## 7. Not settled (unadjudicated or not decidable)\n\n'
             + table(['method', 'set', 'label', 'claims'], [list(k) + [v] for k, v in sorted(t.items())]))
    if a.open:
        with open(a.open, 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(['claim_id', 'repo_id', 'repo_set', 'method', 'model', 'file', 'line', 'confidence', 'label',
                        'reason', 'claim_text'])
            for r in open_rows:
                reason = (r.get('note') or 'not decidable') if r['label'] == 'not_decidable' else \
                    'no run against a reference written from the physics yet'
                w.writerow([r['claim_id'], r['repo_id'], r['repo_set'], r['method'], r['model'], r.get('file', ''),
                            r.get('line', ''), r.get('confidence', ''), r['label'], reason, r['claim_text']])

    text = '\n\n'.join(S) + '\n'
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(text)
    else:
        sys.stdout.write(text)


if __name__ == '__main__':
    main()
