"""Exact references: compare a finite-difference Schroedinger solver with the Morse levels."""
import numpy as np

from physverify import references as R

D, a = 12.0, 1.0  # hbar = m = 1
x = np.linspace(-2.5, 14.0, 3000)
h = x[1] - x[0]
V = D * (1 - np.exp(-a * x)) ** 2
off = np.full(len(x) - 1, 0.5 / h**2)
H = np.diag(1 / h**2 + V) - np.diag(off, 1) - np.diag(off, -1)
E = np.linalg.eigvalsh(H)[:4]
exact = R.morse_levels(np.arange(4), a * np.sqrt(2 * D), a * a / 2)
for v in range(4):
    print(f"v={v}: solver {E[v]:.5f}  exact {exact[v]:.5f}  difference {abs(E[v] - exact[v]):.1e}")
