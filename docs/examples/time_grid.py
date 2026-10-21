"""`while t < t_end: t += h` can take one step too many, depending on rounding."""
from physverify.studies import time_grid_check


def times_while_loop(n, t_end=1.0):
    h, t, out = t_end / n, 0.0, [0.0]
    while t < t_end:  # the common loop
        t += h
        out.append(t)
    return out


def times_counted(n, t_end=1.0):
    h = t_end / n
    return [k * h for k in range(n + 1)]  # exactly n steps


ns = [4, 8, 10, 3]
print("while loop:", time_grid_check(times_while_loop, 0.0, 1.0, ns).message)
print("counted:   ", time_grid_check(times_counted, 0.0, 1.0, ns).message)
