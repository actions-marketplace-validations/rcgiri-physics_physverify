# Reference solutions

**Question:** does the code agree with an independent, more accurate solution of the same problem?

When there is no closed form, compare with a reference: physverify integrates your reference right-hand side with classical RK4 at a much finer step (16 times by default) and measures your code's error against it at several step sizes.

## Example: a pendulum

```python
--8<-- "docs/examples/reference_pendulum.py"
```

Output:

```text
--8<-- "docs/examples/output/reference_pendulum.txt"
```

The code here is plain RK4, so the expected order is 4. The `source` argument is passed as zero, so the same `integrate` function also serves the manufactured-solution check.

## Notes

- The reference is only as independent as the right-hand side you write. Type it from the equations, with the constants written out, not imported from the code under test.
- For orders above 4, raise `ref_factor` so that the reference error stays well below the code's.
- If the code and your reference contain the same mistake, a reference study cannot see it. The [manufactured-solution check](manufactured-solutions.md) and an [exact reference](exact-references.md) guard against that.
