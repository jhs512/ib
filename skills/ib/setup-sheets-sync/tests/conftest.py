import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (str(HERE.parent), str(HERE)):  # sheets-sync(=sync.py), tests(=fakes.py)
    if p not in sys.path:
        sys.path.insert(0, p)
