import argparse
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

parser = argparse.ArgumentParser()
parser.add_argument("--start-from", type=int, default=5)
args = parser.parse_args()

load_dotenv()
src_root = Path(os.environ["MBANNERT_BIDS_ROOT_DIR"]) / "sourcedata" / "experimental_logfiles"
out_root = Path(os.environ["BEHAVIORAL_DATA_DIR"])

for src in src_root.glob("sub-*/**/log_p*.json"):
    if int(src.name.split("_")[1][1:]) < args.start_from:
        continue
    sub = src.relative_to(src_root).parts[0]
    (out_root / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, out_root / sub / src.name)
    print(f"{sub}/{src.name}")