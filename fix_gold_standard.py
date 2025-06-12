import pandas as pd
from pathlib import Path

# ---------- config ----------
csv_path = Path(r"C:\Users\Kevin\tot_branch\multi_coder_analysis\data\gold_standard.csv")
# ----------------------------

# 1. load
df = pd.read_csv(csv_path)

# 2. authoritative corrections  {StatementID: correct Dim1_Frame}
fixes = {
    "seg_v5_5_100_chunk0":   "Neutral",
    "seg_v5_20_1005_chunk0": "Neutral",
    "seg_v5_2_1005_chunk0":  "Neutral",
    "seg_v5_6_1004_chunk0":  "Alarmist",
    "seg_v5_14_101_chunk0":  "Neutral",
}

# 3. apply
mask = df["StatementID"].isin(fixes.keys())
df.loc[mask, "Dim1_Frame"] = df.loc[mask, "StatementID"].map(fixes)

# 4. overwrite (or back-up + overwrite)
# csv_path.rename(csv_path.with_suffix(".bak"))          # OPTIONAL BACK-UP
# df.to_csv(csv_path, index=False)                       # save corrected version
df.to_csv(csv_path, index=False)                         # overwrite directly
print(f"Patched {mask.sum()} rows in {csv_path}") 