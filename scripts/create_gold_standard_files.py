import os
import csv
from pathlib import Path

import pandas as pd


def main() -> None:
    """Create gold_standard_preliminary.csv and gold_standard_ties.csv.

    1. gold_standard_preliminary.csv
       • Start with rows from data/gold_standard.csv
       • Append rows from majority_vote_comparison.csv where Majority_Label != 'LABEL_TIE'
         – Use Majority_Label as Gold Standard
         – Fill ArticleID and Statement Text via segmented_statements.csv (matched on StatementID)

    2. gold_standard_ties.csv
       • Rows from majority_vote_comparison.csv where Majority_Label == 'LABEL_TIE'
         – Fill ArticleID and Statement Text via segmented_statements.csv (matched on StatementID)
    """

    # Base paths inside the repository ---------------------------------------------------------
    repo_root = Path(__file__).resolve().parent.parent

    data_dir = repo_root / "multi_coder_analysis" / "data"
    gold_standard_path = data_dir / "gold_standard.csv"
    segmented_path = data_dir / "segmented_statements.csv"

    mvc_path = (
        repo_root
        / "multi_coder_analysis"
        / "output"
        / "test"
        / "framing"
        / "permutations_20250621_193841"
        / "majority_vote_comparison.csv"
    )

    prelim_output_path = data_dir / "gold_standard_preliminary.csv"
    ties_output_path = data_dir / "gold_standard_ties.csv"

    # Validate that all input files exist ------------------------------------------------------
    for f in (gold_standard_path, segmented_path, mvc_path):
        if not f.exists():
            raise FileNotFoundError(f"Required input file not found: {f}")

    # 1. Load gold_standard.csv ----------------------------------------------------------------
    gold_standard_df = pd.read_csv(gold_standard_path)

    # 2. Load segmented_statements.csv ---------------------------------------------------------
    #    This file lacks a header row and uses quotes around every field.
    seg_cols = [
        "ArticleID",
        "StatementID",
        "StartCharIdx",
        "EndCharIdx",
        "Statement Text",
    ]
    segmented_df = pd.read_csv(
        segmented_path,
        header=None,
        names=seg_cols,
        quoting=csv.QUOTE_ALL,
        engine="python",
    )
    # We only need the three columns required for output
    segmented_df = segmented_df[["ArticleID", "StatementID", "Statement Text"]]

    # 3. Load majority_vote_comparison.csv -----------------------------------------------------
    mvc_df = pd.read_csv(mvc_path)

    # Split into ties and non-ties
    non_ties_df = mvc_df[mvc_df["Majority_Label"] != "LABEL_TIE"].copy()
    ties_df = mvc_df[mvc_df["Majority_Label"] == "LABEL_TIE"].copy()

    def enrich(df: pd.DataFrame) -> pd.DataFrame:
        """Attach ArticleID and Statement Text and rename Majority_Label."""
        enriched = df.merge(segmented_df, on="StatementID", how="left")
        enriched = enriched[
            ["ArticleID", "StatementID", "Statement Text", "Majority_Label"]
        ]
        enriched = enriched.rename(columns={"Majority_Label": "Gold Standard"})
        return enriched

    non_ties_ready = enrich(non_ties_df)
    ties_ready = enrich(ties_df)

    # ------------------------------------------------------------------
    # Avoid adding duplicates already present in the original gold standard
    # ------------------------------------------------------------------
    existing_statement_ids = set(gold_standard_df["StatementID"].astype(str))
    non_ties_ready = non_ties_ready[
        ~non_ties_ready["StatementID"].astype(str).isin(existing_statement_ids)
    ]

    # 4. Combine for preliminary file ----------------------------------------------------------
    prelim_df = pd.concat([gold_standard_df, non_ties_ready], ignore_index=True)

    # Final safety: ensure no duplicate StatementID rows remain (keeps first)
    prelim_df = prelim_df.drop_duplicates(subset=["StatementID"], keep="first")

    # 5. Save outputs -------------------------------------------------------------------------
    prelim_df.to_csv(prelim_output_path, index=False)
    ties_ready.to_csv(ties_output_path, index=False)

    print(f"Created {prelim_output_path} (rows: {len(prelim_df)})")
    print(f"Created {ties_output_path} (rows: {len(ties_ready)})")


if __name__ == "__main__":
    main() 