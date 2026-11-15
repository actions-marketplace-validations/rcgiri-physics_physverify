"""Arm C sandbox entry: run `physverify confirm` from the frozen copy in /work; the ledger goes to /out."""
import sys

sys.path.insert(0, "/work")
import physverify  # noqa: E402
from physverify.cli import main  # noqa: E402

print("physverify", physverify.__version__, physverify.__file__, flush=True)
claim = sys.argv[1]
sys.exit(main(["confirm", f"/work/{claim}", "--ledger", "/out/confirm_ledger.jsonl",
               "--json", f"/out/{claim}.json", "--timeout", "600"]))
