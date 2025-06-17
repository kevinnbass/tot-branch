import sys
from pathlib import Path
import pandas as pd


def compute_majority_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """Append a Majority_Label_Ratio column to *df* and return it.

    The ratio is defined as:
        (# occurrences of Majority_Label across permutation columns) /
        (total permutation count - # occurrences of Majority_Label)

    If all permutation labels already match the majority label (denominator
    zero) the ratio is treated as **infinite** (represented by ``float('inf')``).
    """

    # Heuristically detect permutation columns (those starting with 'P' and
    # containing an underscore, e.g. P1_AB, P2_BA, ...).  This avoids hard-
    # coding column names so the script works with future changes.
    perm_cols = [c for c in df.columns if c.startswith("P") and "_" in c]

    if not perm_cols:
        raise ValueError(
            "No permutation label columns found. Expected columns like 'P1_AB', 'P2_BA', …"
        )

    def _ratio(row):
        maj_label = row["Majority_Label"]
        maj_count = sum(row[col] == maj_label for col in perm_cols)
        other = len(perm_cols) - maj_count
        return maj_count / other if other else float("inf")

    df["Majority_Label_Ratio"] = df.apply(_ratio, axis=1)
    return df


def main():
    if len(sys.argv) < 2:
        print("Usage: python add_majority_ratio.py <csv_path> [<csv_path> …]", file=sys.stderr)
        sys.exit(1)

    for path_str in sys.argv[1:]:
        path = Path(path_str)
        if not path.exists():
            print(f"⚠ File not found: {path}", file=sys.stderr)
            continue

        try:
            df = pd.read_csv(path)
        except Exception as exc:
            print(f"⚠ Could not read {path}: {exc}", file=sys.stderr)
            continue

        try:
            df = compute_majority_ratio(df)
        except Exception as exc:
            print(f"⚠ Failed to compute ratio for {path}: {exc}", file=sys.stderr)
            continue

        # Overwrite the original file (no rename)
        try:
            df.to_csv(path, index=False)
            print(f"✅ Updated {path} with Majority_Label_Ratio column.")
        except Exception as exc:
            print(f"⚠ Could not write {path}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main() 