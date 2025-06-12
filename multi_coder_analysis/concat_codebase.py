import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List

EXCLUDE_DIRS = {
    "__pycache__",
    ".git",
    "env",
    "venv",
    "node_modules",
    "output",
    "data",
}

INCLUDE_EXTS = {".py", ".txt", ".md", ".yaml", ".yml"}


def should_skip_dir(dir_path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in dir_path.parts)


def gather_files(root: Path) -> List[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)
        # Modify dirnames in-place to skip excluded dirs
        dirnames[:] = [d for d in dirnames if not should_skip_dir(current_dir / d)]
        for fname in filenames:
            fp = current_dir / fname
            if fp.suffix.lower() in INCLUDE_EXTS:
                files.append(fp)
    # Sort for stable order
    files.sort(key=lambda p: str(p))
    return files


def concatenate_codebase(output_dir: Path = Path("concatenated_codebase")) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"codebase_concat_{timestamp}.txt"

    repo_root = Path(__file__).resolve().parent.parent

    files_to_concat = gather_files(repo_root)
    logging.info(f"Found {len(files_to_concat)} files to concatenate.")

    with open(output_path, "w", encoding="utf-8", errors="ignore") as outfile:
        outfile.write(f"# Full Codebase Snapshot — generated {datetime.now().isoformat(timespec='seconds')}\n")
        outfile.write("=" * 100 + "\n\n")
        for idx, file_path in enumerate(files_to_concat, 1):
            relative_path = file_path.relative_to(repo_root)
            outfile.write(f"## {idx:04d}. {relative_path}\n")
            outfile.write("-" * 100 + "\n")
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    outfile.write(f.read())
            except Exception as e:
                outfile.write(f"[ERROR reading {relative_path}: {e}]\n")
            outfile.write("\n\n")
        outfile.write("=" * 100 + "\n")
        outfile.write(f"# End of snapshot — {len(files_to_concat)} files\n")

    logging.info(f"Codebase concatenated to: {output_path}")
    return output_path


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    path = concatenate_codebase()
    print(f"✅ Concatenation complete: {path}")


if __name__ == "__main__":
    main() 