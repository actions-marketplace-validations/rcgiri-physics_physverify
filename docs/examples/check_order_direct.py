"""Already have step sizes and errors from your own study? Hand them to check_order."""
from physverify import check_order

hs = [0.1, 0.05, 0.025, 0.0125]
errors = [3.1e-3, 7.9e-4, 2.0e-4, 5.0e-5]
print("claimed 2:", check_order(hs, errors, 2).message)
print("claimed 4:", check_order(hs, errors, 4).status)
print("at round-off:", check_order(hs, [1e-14, 1e-14, 2e-14, 1e-14], 2).message)
