import pandas as pd
import pathlib

# ----- CONFIG -----
csv_path  = pathlib.Path(r"C:\Users\Kevin\tot_branch\multi_coder_analysis\data\gold_standard.csv")
frame_col = "gold_frame"          # change if your column name differs
# -------------------

# rows to fix:  {StatementID : correct_label}
patch = {
    "seg_v5_28_1005_chunk0": "Neutral",   # was Reassuring
    "seg_v5_14_101_chunk0": "Neutral"     # was Reassuring
}

# --- load, patch, save ---
df = pd.read_csv(csv_path)

for sid, new_label in patch.items():
    mask = df["StatementID"] == sid
    if mask.any():
        df.loc[mask, frame_col] = new_label
        print(f"Updated {sid} → {new_label}")
    else:
        print(f"Warning: {sid} not found – check spelling or file.")

df.to_csv(csv_path, index=False)
print("✅  Gold-standard file saved with corrections.") 