import argparse
import re
from pathlib import Path
from typing import Optional, List

MARKER_RE = re.compile(r"^## File \d+:\s+(.+)$")
SEPARATOR_RE = re.compile(r"^-{2,}\s*$")


def restore_prompts(concat_file: Path, output_dir: Optional[Path] = None) -> List[Path]:
    """Recreate individual prompt files from a concatenated prompts text file.

    The concatenated file is expected to contain blocks in the format produced by
    multi_coder_analysis.concat_prompts.concatenate_prompts(), i.e.:

        ## File 3: hop_Q02.txt
        ------------------------------------------------------------
        <file contents>
        ...

    Parameters
    ----------
    concat_file : Path
        Path to the concatenated prompts text file.
    output_dir : Path | None, optional
        Directory where prompt files will be recreated.  Defaults to
        ``concat_file.parent / "restored_prompts"``.

    Returns
    -------
    list[Path]
        List of paths that were written.
    """
    concat_file = Path(concat_file)
    if not concat_file.exists():
        raise FileNotFoundError(concat_file)

    if output_dir is None:
        output_dir = concat_file.parent / "restored_prompts"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []

    current_path: Path | None = None
    buffer: list[str] = []

    def _flush() -> None:
        nonlocal buffer, current_path
        if current_path is None:
            return
        # Write buffered lines to disk
        current_path.parent.mkdir(parents=True, exist_ok=True)
        current_path.write_text("".join(buffer), encoding="utf-8")
        written.append(current_path)
        buffer = []
        current_path = None

    with concat_file.open("r", encoding="utf-8") as fh:
        # Skip the header lines until first marker
        for raw in fh:
            m = MARKER_RE.match(raw.rstrip())
            if m:
                # Found first marker line
                current_path = output_dir / m.group(1).strip()
                # Skip the dashed separator immediately following (if present)
                next_line = next(fh, "")
                if not SEPARATOR_RE.match(next_line):
                    # If it's not a separator, treat as content
                    buffer.append(next_line)
                break

        # Continue reading remainder of file
        for line in fh:
            marker_match = MARKER_RE.match(line.rstrip())
            if marker_match:
                # Start of a new file block
                _flush()
                current_path = output_dir / marker_match.group(1).strip()
                # Expect and skip separator line
                next_line = next(fh, "")
                if SEPARATOR_RE.match(next_line):
                    continue  # skip separator
                else:
                    buffer.append(next_line)
                    continue
            else:
                # Regular content line
                buffer.append(line)

    # Flush last file
    _flush()

    return written


from typing import List as _List, Optional as _Optional


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Restore prompt directory from a concatenated prompts file.")
    parser.add_argument("concat_file", help="Path to concatenated prompts file")
    parser.add_argument("--out", dest="output_dir", help="Output directory for restored prompts (default: <concat_dir>/restored_prompts)")

    args = parser.parse_args(argv)

    try:
        written = restore_prompts(Path(args.concat_file), Path(args.output_dir) if args.output_dir else None)
    except Exception as exc:
        parser.error(str(exc))

    print(f"Wrote {len(written)} prompt files to {(Path(args.output_dir) if args.output_dir else Path(args.concat_file).parent / 'restored_prompts').resolve()}")


if __name__ == "__main__":
    main() 