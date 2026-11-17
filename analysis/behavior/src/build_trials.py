import json

import pandas as pd

from common import LOGFILES_DIR, TRIALS_CSV

rows = []
for path in sorted(LOGFILES_DIR.rglob("log_p*.json"), key=lambda p: p.name):
    _, participant, stamp = path.stem.split("_")
    for t in json.loads(path.read_text())["trials"]:
        if t["trial_role"] != "decision" or not isinstance(t["is_correct"], bool):
            continue
        rows.append({
            "participant": participant,
            "timestamp": pd.to_datetime(stamp, format="%Y%m%dT%H%M%S"),
            "logfile": path.name,
            "block": t["block_index"],
            "family": t["block_family"],
            "rule": t["rule"],
            "context": t["context"],
            "trial_index": t["trial_index"],
            "correct_answer": t["correct"],
            "response": t["resp"],
            "is_correct": t["is_correct"],
            "timeout": t["resp"] == "timeout",
            "rt": t["rt"] if t["resp"] != "timeout" else None,
        })

df = pd.DataFrame(rows)
df.insert(1, "session", df.groupby("participant")["timestamp"].rank(method="dense").astype(int))
df = df.sort_values(["participant", "session", "block", "trial_index"])
df.to_csv(TRIALS_CSV, index=False)
print(f"{len(df)} trials -> {TRIALS_CSV}")