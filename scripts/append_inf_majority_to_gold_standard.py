import argparse
import sys
from pathlib import Path
import pandas as pd


DEFAULT_MAJORITY_VOTE_CSV = (
    r"multi_coder_analysis/output/test/framing/permutations_20250618_094310/majority_vote_comparison.csv"
)
DEFAULT_SEGMENTED_CSV = r"multi_coder_analysis/data/segmented_statements.csv"
DEFAULT_GOLD_STANDARD_CSV = r"multi_coder_analysis/data/gold_standard_modified.csv"
DEFAULT_SOURCE_GOLD_CSV = r"multi_coder_analysis/data/gold_standard.csv"


def load_dataframe(path: Path, **kwargs) -> pd.DataFrame:
    """Load a CSV into a DataFrame with basic error handling."""
    try:
        return pd.read_csv(path, **kwargs)
    except FileNotFoundError:
        sys.exit(f"❌ File not found: {path}")
    except Exception as exc:
        sys.exit(f"❌ Failed to read {path}: {exc}")


def filter_inf_majority(df: pd.DataFrame) -> pd.DataFrame:
    """Return only rows whose Majority_Label_Ratio value is 'inf' (case-insensitive)."""
    if "Majority_Label_Ratio" not in df.columns:
        sys.exit("❌ Column 'Majority_Label_Ratio' not found in majority-vote CSV.")

    return df[df["Majority_Label_Ratio"].astype(str).str.lower() == "inf"].copy()


def join_with_segments(maj_df: pd.DataFrame, seg_df: pd.DataFrame) -> pd.DataFrame:
    """Add ArticleID and Statement Text to maj_df by joining with seg_df on StatementID."""
    required_seg_cols = {"StatementID", "ArticleID", "Statement Text"}
    if not required_seg_cols.issubset(seg_df.columns):
        missing = required_seg_cols - set(seg_df.columns)
        sys.exit(
            f"❌ Segmented statements CSV missing required columns: {', '.join(sorted(missing))}"
        )

    merged = maj_df.merge(
        seg_df[list(required_seg_cols)], on="StatementID", how="left", validate="many_to_one"
    )

    if merged["ArticleID"].isna().any():
        missing_ids = merged.loc[merged["ArticleID"].isna(), "StatementID"].tolist()[:10]
        print(
            f"⚠ Warning: {merged['ArticleID'].isna().sum()} StatementID(s) not found in segmented_statements.csv."
            f" Examples: {missing_ids}",
            file=sys.stderr,
        )
        merged = merged.dropna(subset=["ArticleID"])

    return merged


def build_gold_rows(merged_df: pd.DataFrame) -> pd.DataFrame:
    """Shape merged_df into the schema of gold_standard.csv."""
    gold_rows = merged_df[
        ["ArticleID", "StatementID", "Statement Text", "Majority_Label"]
    ].rename(columns={"Majority_Label": "Gold Standard"})
    return gold_rows


def write_modified_gold_standard(new_rows: pd.DataFrame, gold_path: Path, source_path: Path):
    """Create or update *gold_path* so that it contains:

    1. All rows from *source_path* (if present).
    2. Any existing rows already in *gold_path*.
    3. *new_rows* (inf-majority rows).

    Duplicate `StatementID`s are removed, keeping the first encountered instance.
    """
    dataframes = []

    if source_path.exists():
        dataframes.append(pd.read_csv(source_path))

    if gold_path.exists():
        dataframes.append(pd.read_csv(gold_path))

    dataframes.append(new_rows)

    combined = pd.concat(dataframes, ignore_index=True)

    before = len(combined)
    combined = combined.drop_duplicates(subset=["StatementID"], keep="first")
    dupes = before - len(combined)
    if dupes:
        print(
            f"ℹ Removed {dupes} duplicate StatementID(s) while merging.",
            file=sys.stderr,
        )

    combined.to_csv(gold_path, index=False)
    print(
        f"✅ Modified gold standard written → {gold_path} (total rows: {len(combined)}).",
        file=sys.stderr,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Append segments with infinite Majority_Label_Ratio to gold_standard_modified.csv"
    )
    parser.add_argument(
        "--majority",
        default=DEFAULT_MAJORITY_VOTE_CSV,
        help="Path to majority_vote_comparison.csv (default: %(default)s)",
    )
    parser.add_argument(
        "--segments",
        default=DEFAULT_SEGMENTED_CSV,
        help="Path to segmented_statements.csv (default: %(default)s)",
    )
    parser.add_argument(
        "--gold",
        default=DEFAULT_GOLD_STANDARD_CSV,
        help="Path to output gold_standard_modified.csv (default: %(default)s)",
    )
    parser.add_argument(
        "--source-gold",
        default=DEFAULT_SOURCE_GOLD_CSV,
        help="Path to original gold_standard.csv whose rows should also be retained (default: %(default)s)",
    )

    args = parser.parse_args()

    maj_df = load_dataframe(Path(args.majority))
    seg_df = load_dataframe(Path(args.segments), dtype={"StatementID": str})

    inf_df = filter_inf_majority(maj_df)
    if inf_df.empty:
        print("No Majority_Label_Ratio == inf rows found. Nothing to append.", file=sys.stderr)
        return

    merged_df = join_with_segments(inf_df, seg_df)
    if merged_df.empty:
        print("No matching rows after join. Nothing to append.", file=sys.stderr)
        return

    gold_rows = build_gold_rows(merged_df)
    write_modified_gold_standard(gold_rows, Path(args.gold), Path(args.source_gold))


if __name__ == "__main__":
    main() 