## S

- Before running `done`, write your reply (the reason, the script name and the VERDICT line) to {WORK}/answer.md as well.

## C

- Use `physverify confirm`. Its specification is {WORK}/confirm.md and the package is in {WORK}/physverify; read the specification before writing anything. Write one claim file in {WORK} and run it with
  `{PY} -I {HARNESS}/session.py confirm {SESSION} CLAIM_FILE.py`
  (each confirm counts as one of your 6 runs; your own scripts may `import physverify` if they put `/work` on `sys.path`). The verdict that counts is the one `confirm` records, not the one you state, so fix the claim file and run again if it records something you think is wrong.
