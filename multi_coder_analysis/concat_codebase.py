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
    "docs",
    "concatenated_prompts",
    "concatenated_codebase",
}

# Always include these extensions for code/config
ALWAYS_EXTS = {".py", ".yaml", ".yml"}

# Explicit individual files (relative to repo root) to skip
EXCLUDE_FILES = {
    "readme.md",  # root-level README
    "multi_coder_analysis/llm_providers/openrouter_provider.py",
    "multi_coder_analysis/update_gold_standard.py",
}

# Conditional inclusion for specific text files
def _should_include_special(file_path: Path, repo_root: Path) -> bool:
    # --- Prompt templates (.txt) ---
    if file_path.suffix.lower() == ".txt":
        try:
            rel = file_path.relative_to(repo_root)
        except ValueError:
            return False
        return rel.parts[0] == "multi_coder_analysis" and "prompts" in rel.parts

    # --- Markdown: only top-level README(s) ---
    if file_path.suffix.lower() == ".md":
        # Only include top-level README*.md files (drop upgrade summaries / large changelogs)
        try:
            rel = file_path.relative_to(repo_root)
        except ValueError:
            return False
        return len(rel.parts) == 1 and rel.name.lower().startswith("readme")

    return False


def should_skip_dir(dir_path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in dir_path.parts)


def gather_files(repo_root: Path) -> List[Path]:
    """Collect files relevant to the pipeline.

    Rules:
    • All .py/.yaml/.yml in multi_coder_analysis (excluding EXCLUDE_DIRS).
    • .txt prompt templates inside multi_coder_analysis/prompts.
    • Top-level README*.md, config.yaml, requirements.txt.
    """
    files: List[Path] = []

    # 1. Walk multi_coder_analysis
    mca_root = repo_root / "multi_coder_analysis"
    for dirpath, dirnames, filenames in os.walk(mca_root):
        current_dir = Path(dirpath)
        dirnames[:] = [d for d in dirnames if not should_skip_dir(current_dir / d)]
        for fname in filenames:
            fp = current_dir / fname
            rel_posix = str(fp.relative_to(repo_root)).replace("\\", "/").lower()
            if rel_posix in EXCLUDE_FILES:
                continue
            if fp.suffix.lower() in ALWAYS_EXTS or _should_include_special(fp, repo_root):
                files.append(fp)

    # 2. Top-level important files
    for top_name in ("config.yaml", "requirements.txt"):
        tp = repo_root / top_name
        if tp.exists():
            files.append(tp)

    # README markdown(s)
    for md in repo_root.glob("README*.md"):
        rel_md = str(md.relative_to(repo_root)).replace("\\", "/").lower()
        if rel_md not in EXCLUDE_FILES:
            files.append(md)

    # Stable ordering
    files = sorted(set(files), key=lambda p: str(p))
    return files


def concatenate_codebase(output_dir: Path = Path("concatenated_codebase")) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"codebase_concat_{timestamp}.txt"

    repo_root = Path(__file__).resolve().parent.parent

    files_to_concat = gather_files(repo_root)
    logging.info(f"Found {len(files_to_concat)} files to concatenate:")
    for fp in files_to_concat:
        rel = fp.relative_to(repo_root)
        print(f"✔ {rel}")

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