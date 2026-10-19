| Bug | mms: FTCS coupled dt ~ dx^2 | mms: FTCS time-only refinement | mms: FTCS space-only refinement | reference: FTCS eigenmode decay | patch: FTCS cubic in x, linear in t |
|---|---|---|---|---|---|
| (none) | ok | ok | ok | ok | ok |
| dx_off_by_one | FLAGGED | FLAGGED | FLAGGED | FLAGGED | FLAGGED |
| alpha_ignored | FLAGGED | FLAGGED | FLAGGED | FLAGGED | FLAGGED |
| extra_time_step | no | no | no | no | FLAGGED |
| unstable_dt | FLAGGED | no | FLAGGED | FLAGGED | FLAGGED |
| source_time_shift | no | no | no | no | FLAGGED |
