import csv
import random
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Set


DEFAULT_EXCLUDE_IDS = {
    1, 10, 100, 101,
    1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010,
}


def read_segments(csv_path: Path, exclude_ids: Set[int]) -> Dict[int, List[Dict[str, Any]]]:
    """Load rows from the CSV, grouped by ArticleID, skipping excluded IDs."""
    segments_by_article: Dict[int, List[Dict[str, Any]]] = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required_cols = {"ArticleID", "StatementID", "Statement Text"}
        missing = required_cols - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV file missing required columns: {', '.join(sorted(missing))}")
        for row in reader:
            try:
                aid = int(row["ArticleID"].strip())
            except ValueError:
                # Skip rows with non-numeric ArticleID values
                continue
            if aid in exclude_ids:
                continue
            segments_by_article.setdefault(aid, []).append(row)
    return segments_by_article


def sample_articles(
    segments_by_article: Dict[int, List[Dict[str, Any]]],
    target_segment_count: int,
    rng: random.Random,
):
    """Randomly pick articles until at least target_segment_count rows collected."""
    available_article_ids = list(segments_by_article.keys())
    rng.shuffle(available_article_ids)

    collected_rows: List[Dict[str, Any]] = []
    selected_ids: List[int] = []

    for aid in available_article_ids:
        collected_rows.extend(segments_by_article[aid])
        selected_ids.append(aid)
        if len(collected_rows) >= target_segment_count:
            break

    return collected_rows, selected_ids


def write_output(rows: List[Dict[str, Any]], output_path: Path):
    """Write selected rows to a CSV with the specified columns."""
    columns = ["ArticleID", "StatementID", "Statement Text"]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row[col] for col in columns})


def main():
    parser = argparse.ArgumentParser(description="Sample ~1750 segments at the article level.")
    parser.add_argument(
        "--input",
        default="multi_coder_analysis/data/segmented_statements.csv",
        help="Path to the segmented statements CSV file (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        default="gold_standard_2.csv",
        help="Where to write the sampled CSV (default: %(default)s)",
    )
    parser.add_argument(
        "--n_segments",
        type=int,
        default=1750,
        help="Minimum number of segments to sample (default: %(default)s)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: system random)",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        type=int,
        help="Additional ArticleIDs to exclude (space-separated list)",
    )
    args = parser.parse_args()

    csv_path = Path(args.input)
    if not csv_path.is_file():
        print(f"Input CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    exclude_ids = set(DEFAULT_EXCLUDE_IDS)
    if args.exclude:
        exclude_ids.update(args.exclude)

    rng = random.Random(args.seed)

    segments_by_article = read_segments(csv_path, exclude_ids)
    if not segments_by_article:
        print("No segments available after applying exclusions.", file=sys.stderr)
        sys.exit(1)

    total_available = sum(len(v) for v in segments_by_article.values())
    if total_available < args.n_segments:
        print(
            f"Warning: only {total_available} segments available; less than requested {args.n_segments}",
            file=sys.stderr,
        )

    collected_rows, selected_article_ids = sample_articles(
        segments_by_article, args.n_segments, rng
    )

    output_path = Path(args.output)
    write_output(collected_rows, output_path)

    print(
        f"Wrote {len(collected_rows)} rows from {len(selected_article_ids)} articles to {output_path}",
        file=sys.stderr,
    )
    print(f"Excluded ArticleIDs: {sorted(exclude_ids)}", file=sys.stderr)


if __name__ == "__main__":
    main() 