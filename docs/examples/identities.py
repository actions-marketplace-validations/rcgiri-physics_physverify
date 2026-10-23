"""Checks with no exact solution: sibling agreement, a round trip and an analytic derivative."""

import math

import numpy as np

from physverify.identities import check_agree, check_derivative, check_roundtrip

C = 343.0  # speed of sound, m/s


def rt60_sabine(S, V, a, m):
    return 24 * math.log(10) / C * V / (a * S + 4 * m * V)


def rt60_eyring(S, V, a, m):  # bug: the air term has the wrong sign
    return -(24 * math.log(10) / C) * V / (S * math.log(1 - a) + 4 * m * V)


# Eyring's formula reduces to Sabine's for small wall absorption, with or without air absorption.
cases = [(94.0, 60.0, 1e-4, m) for m in (0.0, 0.005, 0.05)]
print(check_agree(rt60_eyring, rt60_sabine, cases, rtol=1e-3, names=("eyring", "sabine")).status, "sibling agreement")


# A reference pixel written as 1 + n/2 instead of (n + 1)/2: pixel -> sky -> pixel is off by half a pixel.
n = 20
to_sky = lambda p: (p + 1 - (1 + n / 2)) * 2.0  # noqa: E731
to_pixel = lambda s: s / 2.0 + (n + 1) / 2 - 1  # noqa: E731
r = check_roundtrip(to_sky, to_pixel, [(n - 1) / 2])
print(r.status, "round trip:", r.message.split("; ")[1].split(" (")[0])


# An analytic derivative against finite differences of the function itself.
f = lambda x: np.exp(-x) * np.sin(3 * x)  # noqa: E731
df = lambda x: np.exp(-x) * (3 * np.cos(3 * x) - np.sin(3 * x))  # noqa: E731
print(check_derivative(f, df, [0.0, 0.4, 2.0]).status, "derivative")
