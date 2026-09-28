from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAHIER_PATH = ROOT / "cahier.txt"
PEDAGOGIE_PATH = ROOT / "PEDAGOGIE.md"
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def pytest_addoption(parser):
    parser.addoption("--regenerer-golden", action="store_true", default=False, help="réécrit tests/golden/exemple.ly")
