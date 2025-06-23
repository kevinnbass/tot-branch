import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List
import argparse

EXCLUDE_DIRS = {
    "__pycache__",
    ".git",
    "env",
    "venv",
    "node_modules",
    "output",
    "data",
    "concatenated_prompts",
    "concatenated_codebase",
    "patches",  # historical diff artefacts – not needed for context
    # Tests are explicitly included below.
}

# Always include these extensions (core code & infra) – markdown excluded by default
ALWAYS_EXTS = {".py", ".yaml", ".yml", ".toml"}

# Explicit individual files (relative to repo root) to skip
EXCLUDE_FILES = {
    # Keep minimal exclusions (generated snapshots, compiled artifacts)
    "multi_coder_analysis/update_gold_standard.py",
    # Exclude helper/maintenance scripts and config overrides
    "multi_coder_analysis/concat_codebase.py",
    "multi_coder_analysis/concat_now.py",
    "multi_coder_analysis/concat_prompts.py",
    "multi_coder_analysis/consolidate_mismatch_traces.py",
    "multi_coder_analysis/fix_gold_standard.py",
    "multi_coder_analysis/fix_gold_standard_yaml.py",
    "multi_coder_analysis/fixes_config.yaml",
    "requirements.txt",
    # Large historical upgrade notes (markdown)
    "multi_coder_analysis/UPGRADE_v2.16.1_COMPREHENSIVE_PATCH_SUMMARY.md",
    "multi_coder_analysis/UPGRADE_v2.16.1_SUMMARY.md",
    "multi_coder_analysis/UPGRADE_v2.16.2_FIXES_SUMMARY.md",
    "multi_coder_analysis/UPGRADE_v2.16.3_MINIMIZER_FIX_SUMMARY.md",
    "multi_coder_analysis/UPGRADE_v2.16_SUMMARY.md",
    # Legacy shim modules no longer needed for code understanding
    "multi_coder_analysis/hop_context.py",
    "multi_coder_analysis/regex_engine.py",
    "multi_coder_analysis/utils/prompt_loader.py",
    "multi_coder_analysis/utils/tracing.py",
    "multi_coder_analysis/llm_providers/base.py",
    "multi_coder_analysis/llm_providers/gemini_provider.py",
    "multi_coder_analysis/llm_providers/openrouter_provider.py",
}

# Pattern-based exclusions for additional size trimming (evaluated on POSIX path)
EXCLUDE_PATTERNS = [
    lambda p: p.endswith(".patch"),  # any patch files missed by dir exclude
    lambda p: "/patches/" in p,      # embedded patches directory
    lambda p: "/upgrade_" in p.lower(),  # any other upgrade markdowns
    lambda p: p.endswith("_summary.md"),  # misc summary notes
]

# Helper for conditional inclusion (defined inside gather_files to capture flags)

def should_skip_dir(dir_path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in dir_path.parts)


def gather_files(
    repo_root: Path,
    include_tests: bool = False,
    include_docs: bool = False,
    include_scripts: bool = False,
    include_prompts: bool = False,
    include_legacy: bool = False,
) -> List[Path]:
    """Collect files relevant to the pipeline.

    Rules:
    • All .py/.yaml/.yml in multi_coder_analysis (excluding EXCLUDE_DIRS).
    • Test files from tests/ and unit_tests/ directories.
    • .txt prompt templates inside multi_coder_analysis/prompts.
    • Top-level README*.md, config.yaml, requirements.txt.
    """
    files: List[Path] = []

    # Closure so that include_docs flag is visible inside helper
    def _should_include_special(file_path: Path, repo_root: Path) -> bool:  # type: ignore
        """Return True if file should be included based on extension & location."""

        # --- Prompt templates (.txt) ---
        if file_path.suffix.lower() == ".txt":
            try:
                rel = file_path.relative_to(repo_root)
            except ValueError:
                return False
            # Include any prompt templates located under /prompts directories
            return "prompts" in rel.parts

        # --- Markdown documentation (.md) ---
        if file_path.suffix.lower() == ".md":
            try:
                rel = file_path.relative_to(repo_root)
            except ValueError:
                return False

            # Architecture / design docs
            if rel.parts[0] in {"docs", "multi_coder_analysis"}:
                return include_docs  # only include when docs flag enabled

            # Top-level README*.md (root) and README in subpackages
            if rel.name.lower().startswith("readme"):
                return include_docs  # gated by docs flag as well

        return False

    # Directories to scan exhaustively for essential code only
    PRIMARY_DIRS = [
        repo_root / "multi_coder_analysis" / "models",
        repo_root / "multi_coder_analysis" / "core",
        repo_root / "multi_coder_analysis" / "runtime",
        repo_root / "multi_coder_analysis" / "config",
        repo_root / "multi_coder_analysis" / "providers",
        repo_root / "multi_coder_analysis" / "regex",
        repo_root / "multi_coder_analysis" / "utils",
    ]

    if include_docs:
        PRIMARY_DIRS.append(repo_root / "docs")

    if include_prompts:
        PRIMARY_DIRS.append(repo_root / "multi_coder_analysis" / "prompts")

    if include_legacy:
        PRIMARY_DIRS.append(repo_root / "multi_coder_analysis" / "llm_providers")

    if include_scripts:
        PRIMARY_DIRS.append(repo_root / "scripts")

    for root_dir in PRIMARY_DIRS:
        if not root_dir.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root_dir):
            current_dir = Path(dirpath)
            dirnames[:] = [d for d in dirnames if not should_skip_dir(current_dir / d)]
            for fname in filenames:
                fp = current_dir / fname
                rel_posix = str(fp.relative_to(repo_root)).replace("\\", "/").lower()
                if rel_posix in EXCLUDE_FILES:
                    continue
                if fp.suffix.lower() in ALWAYS_EXTS or _should_include_special(fp, repo_root):
                    files.append(fp)

    if include_tests:
        test_dirs = ["tests", "unit_tests"]
        for test_dir_name in test_dirs:
            test_dir = repo_root / test_dir_name
            if test_dir.exists() and test_dir.is_dir():
                for dirpath, dirnames, filenames in os.walk(test_dir):
                    current_dir = Path(dirpath)
                    dirnames[:] = [d for d in dirnames if not should_skip_dir(current_dir / d)]
                    for fname in filenames:
                        fp = current_dir / fname
                        rel_posix = str(fp.relative_to(repo_root)).replace("\\", "/").lower()
                        if rel_posix in EXCLUDE_FILES:
                            continue
                        if fp.suffix.lower() in ALWAYS_EXTS:
                            files.append(fp)

    # 3. Top-level important files
    for top_name in ("config.yaml", "pyproject.toml", "requirements.txt"):
        tp = repo_root / top_name
        if tp.exists():
            rel_t = str(tp.relative_to(repo_root)).replace("\\", "/").lower()
            if rel_t in EXCLUDE_FILES:
                continue
            files.append(tp)

    # README files (include only when docs are requested)
    if include_docs:
        for md in repo_root.glob("README*.md"):
            rel_md = str(md.relative_to(repo_root)).replace("\\", "/").lower()
            if rel_md not in EXCLUDE_FILES and not any(fn(rel_md) for fn in EXCLUDE_PATTERNS):
                files.append(md)

    # 4. Include any .patch files for context
    for patch_file in repo_root.glob("**/*.patch"):
        if should_skip_dir(patch_file.parent):
            continue
        files.append(patch_file)

    # Stable ordering
    files = sorted(set(files), key=lambda p: str(p))
    return files


def concatenate_codebase(
    output_dir: Path = Path("concatenated_codebase"),
    include_tests: bool = False,
    include_docs: bool = False,
    include_scripts: bool = False,
    include_prompts: bool = False,
    include_legacy: bool = False,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"codebase_concat_{timestamp}.txt"

    repo_root = Path(__file__).resolve().parent.parent

    files_to_concat = gather_files(repo_root, include_tests, include_docs, include_scripts, include_prompts, include_legacy)
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
                    raw = f.read()
                    # Strip NUL and other non-printable control characters that confuse editors/LLMs
                    cleaned = raw.replace("\x00", "")
                    outfile.write(cleaned)
            except Exception as e:
                outfile.write(f"[ERROR reading {relative_path}: {e}]\n")
            outfile.write("\n\n")
        outfile.write("=" * 100 + "\n")
        outfile.write(f"# End of snapshot — {len(files_to_concat)} files\n")

    logging.info(f"Codebase concatenated to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Concatenate project codebase into a single file.")
    parser.add_argument("--output-dir", type=Path, default=Path("concatenated_codebase"), help="Destination directory for the concatenated file.")
    parser.add_argument("--include-tests", action="store_true", help="Include tests/ and unit_tests/ directories in the snapshot.")
    parser.add_argument("--include-docs", action="store_true", help="Include docs/ directory (Markdown documentation) in the snapshot.")
    parser.add_argument("--include-scripts", action="store_true", help="Include scripts/ directory in the snapshot.")
    parser.add_argument("--include-prompts", action="store_true", help="Include prompts/ directory in the snapshot.")
    parser.add_argument("--include-legacy", action="store_true", help="Include legacy provider shims in the snapshot.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging (DEBUG level).")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    path = concatenate_codebase(
        output_dir=args.output_dir,
        include_tests=args.include_tests,
        include_docs=args.include_docs,
        include_scripts=args.include_scripts,
        include_prompts=args.include_prompts,
        include_legacy=args.include_legacy,
    )
    print(f"✅ Concatenation complete: {path}")


if __name__ == "__main__":
    main() 