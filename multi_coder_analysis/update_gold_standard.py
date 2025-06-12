#!/usr/bin/env python3
"""
update_gold_standard.py

Fixes miscoded frame labels identified in the June-10 audit.
Overwrites the original gold_standard.csv file.
Run from the same directory that contains gold_standard.csv.
"""

import csv
import tempfile
import shutil
from pathlib import Path

# ── 1.  StatementIDs whose gold label must change  ──────────────────────────────
CORRECTIONS = {
    # --------------  StatementID ---------------------  ->  new Gold label
    "seg_v5_4_101_chunk0" : "Alarmist",    # "highly contagious … deadly virus"
    "seg_v5_41_101_chunk0": "Neutral",     # "seeing more geographic spread …"
    "seg_v5_48_101_chunk0": "Neutral",     # "has to be considering biosecurity"
    # the next one is a no-op if already Neutral in your file,
    # but keeps the script idempotent across older versions.
    "seg_v5_11_101_chunk0": "Neutral",
}

# ── 2.  I/O paths  ─────────────────────────────────────────────────────────────
INFILE = Path("data/gold_standard.csv")

if not INFILE.exists():
    print(f"❌ Error: {INFILE} not found in current directory.")
    exit(1)

# ── 3.  Patch the file using temporary file for safety  ───────────────────────
changed = 0
processed_sids = set()

# Create temporary file in the same directory to ensure atomic operation
temp_file = tempfile.NamedTemporaryFile(mode='w', 
                                        dir=INFILE.parent, 
                                        suffix='.tmp', 
                                        delete=False, 
                                        newline="", 
                                        encoding="utf-8")
temp_path = Path(temp_file.name)

try:
    with INFILE.open(newline="", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(temp_file, fieldnames=reader.fieldnames)
        writer.writeheader()

        for row in reader:
            sid = row["StatementID"]
            processed_sids.add(sid)
            
            if sid in CORRECTIONS:
                # Update only if the label is actually different
                new_label = CORRECTIONS[sid]
                old_label = row["Gold Standard"].strip()
                if old_label != new_label:
                    print(f"📝 Updating {sid}: '{old_label}' → '{new_label}'")
                    row["Gold Standard"] = new_label
                    changed += 1
                else:
                    print(f"✓  {sid}: Already correct ('{new_label}')")
            
            writer.writerow(row)
    
    # Close the temporary file
    temp_file.close()
    
    # On Windows, we need to remove the target file first
    if INFILE.exists():
        INFILE.unlink()
    
    # Now move the temporary file to replace the original
    shutil.move(str(temp_path), str(INFILE))
    
except Exception as e:
    # Clean up temporary file if something went wrong
    temp_file.close()
    if temp_path.exists():
        temp_path.unlink()
    raise e

# ── 4.  Quick confirmation  ────────────────────────────────────────────────────
print(f"\n✅ Finished. {changed} row(s) updated in {INFILE}")

# Check for missing StatementIDs
missing = [sid for sid in CORRECTIONS if sid not in processed_sids]
if missing:
    print(f"⚠️  Warning: the following StatementID(s) were not found: {missing}")
else:
    print(f"✓  All {len(CORRECTIONS)} target StatementIDs were found and processed.")

print(f"\n📁 Updated file: {INFILE.resolve()}") 