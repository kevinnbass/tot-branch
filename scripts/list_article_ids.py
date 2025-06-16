import csv
import argparse
import sys
from pathlib import Path


def extract_article_ids(csv_path: Path):
    """Read a CSV file and return a sorted list of unique ArticleID values (as integers)."""
    ids = set()
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "ArticleID" not in reader.fieldnames:
            raise ValueError("'ArticleID' column not found in the CSV file.")
        for row in reader:
            raw_val = row["ArticleID"].strip()
            if raw_val == "":
                continue
            try:
                ids.add(int(raw_val))
            except ValueError:
                # Skip non-numeric identifiers gracefully
                continue
    return sorted(ids)


def main():
    parser = argparse.ArgumentParser(
        description="Print all unique numeric values found in the ArticleID column of a CSV file.")
    parser.add_argument(
        "csv_file",
        nargs="?",
        default="multi_coder_analysis/data/gold_standard.csv",
        help="Path to the CSV file to inspect (default: multi_coder_analysis/data/gold_standard.csv)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.is_file():
        print(f"Error: File not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    try:
        article_ids = extract_article_ids(csv_path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    for aid in article_ids:
        print(aid)

    # Optionally, print a summary to stderr so that it doesn't interfere with stdout piping.
    print(f"Total unique ArticleID values: {len(article_ids)}", file=sys.stderr)


if __name__ == "__main__":
    main() 