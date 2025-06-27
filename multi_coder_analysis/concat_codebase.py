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
    "patches",
    # "prompts",  # User has prompts separately
}

# Core code extensions for ToT pipeline
ALWAYS_EXTS = {".py", ".yaml", ".yml", ".toml", ".txt"}

# Files to exclude - focus on non-essential files for ToT pipeline
EXCLUDE_FILES = {
    # Exclude the concatenation scripts themselves
    "multi_coder_analysis/concat_codebase.py",
    "multi_coder_analysis/concat_now.py", 
    "multi_coder_analysis/concat_prompts.py",
    
    # Exclude maintenance/helper scripts not part of pipeline execution
    "multi_coder_analysis/consolidate_mismatch_traces.py",
    "multi_coder_analysis/update_gold_standard.py",
    "multi_coder_analysis/fix_gold_standard.py",
    "multi_coder_analysis/fix_gold_standard_yaml.py",
    "multi_coder_analysis/fixes_config.yaml",
    
    # Exclude upgrade documentation
    "multi_coder_analysis/UPGRADE_v2.16.1_COMPREHENSIVE_PATCH_SUMMARY.md",
    "multi_coder_analysis/UPGRADE_v2.16.1_SUMMARY.md", 
    "multi_coder_analysis/UPGRADE_v2.16.2_FIXES_SUMMARY.md",
    "multi_coder_analysis/UPGRADE_v2.16.3_MINIMIZER_FIX_SUMMARY.md",
    "multi_coder_analysis/UPGRADE_v2.16_SUMMARY.md",
    
    # Exclude non-Gemini providers (pipeline uses Gemini only)
    "multi_coder_analysis/llm_providers/openrouter_provider.py",
    "multi_coder_analysis/providers/gemini.py",  # If this is a duplicate
    
    # Exclude legacy/unused files
    "multi_coder_analysis/hop_context.py",
    "multi_coder_analysis/regex_engine.py",  # Likely superseded
    "multi_coder_analysis/pricing.py",  # Not part of core execution
    "multi_coder_analysis/preprocess.py",  # Not used in this pipeline
    
    # Exclude permutation suite (not part of ToT pipeline)
    "multi_coder_analysis/permutation_suite.py",
}

# Pattern-based exclusions
EXCLUDE_PATTERNS = [
    lambda p: p.endswith(".patch"),
    lambda p: "/patches/" in p,
    lambda p: "/upgrade_" in p.lower(),
    lambda p: p.endswith("_summary.md"),
    lambda p: p.endswith("_summary.txt"),
    lambda p: "mismatch_traces" in p,  # Exclude analysis artifacts
    lambda p: "test_v2" in p and p.endswith(".csv"),  # Exclude test data files
]

def should_skip_dir(dir_path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in dir_path.parts)

def gather_files(
    repo_root: Path,
    include_tests: bool = False,
    include_docs: bool = False,
) -> List[Path]:
    """Collect files relevant to the ToT pipeline with Gemini provider and regex mode.
    
    Focuses on:
    • Entry point: main.py
    • Core ToT pipeline: run_multi_coder_tot.py
    • ToT implementation: core/pipeline/
    • Gemini provider: llm_providers/gemini_provider.py
    • Regex engine and rules: regex/
    • Models and configuration
    • Essential utilities
    """
    files: List[Path] = []

    # Essential ToT pipeline files (explicit inclusion)
    ESSENTIAL_FILES = [
        "multi_coder_analysis/main.py",  # Entry point
        "multi_coder_analysis/run_multi_coder_tot.py",  # Core ToT pipeline
        "multi_coder_analysis/__init__.py",
        
        # Gemini provider (required for --provider gemini)
        "multi_coder_analysis/llm_providers/gemini_provider.py",
        "multi_coder_analysis/llm_providers/base.py",  # Base provider needed
        "multi_coder_analysis/llm_providers/__init__.py",
        
        # Top-level config
        "config.yaml",
        "multi_coder_analysis/config.yaml",
    ]
    
    # Add essential files that exist
    for file_rel in ESSENTIAL_FILES:
        file_path = repo_root / file_rel
        if file_path.exists():
            files.append(file_path)

    # Core directories for ToT pipeline execution
    CORE_DIRS = [
        repo_root / "multi_coder_analysis" / "core",      # Core ToT logic
        repo_root / "multi_coder_analysis" / "models",    # Data models
        repo_root / "multi_coder_analysis" / "config",    # Configuration
        repo_root / "multi_coder_analysis" / "regex",     # Package regex rules
        repo_root / "multi_coder_analysis" / "runtime",   # Runtime components

        # Newly-added functional areas
        repo_root / "pipeline",          # Router + LeanHop builder
        repo_root / "regex",             # Top-level YAML rule sets
        repo_root / "prompts",           # LeanHop templates + headers/footers
    ]

    # Essential utilities only (not all utils)
    utils_dir = repo_root / "multi_coder_analysis" / "utils"
    if utils_dir.exists():
        # Only include specific utilities needed for pipeline
        for util_file in ["__init__.py", "archiver.py"]:
            util_path = utils_dir / util_file
            if util_path.exists():
                files.append(util_path)

    # Add core directories
    for core_dir in CORE_DIRS:
        if not core_dir.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(core_dir):
            current_dir = Path(dirpath)
            dirnames[:] = [d for d in dirnames if not should_skip_dir(current_dir / d)]
            for fname in filenames:
                fp = current_dir / fname
                try:
                    rel_posix = str(fp.relative_to(repo_root)).replace("\\", "/").lower()
                except ValueError:
                    continue
                if rel_posix in EXCLUDE_FILES:
                    continue
                if any(fn(rel_posix) for fn in EXCLUDE_PATTERNS):
                    continue
                if fp.suffix.lower() in ALWAYS_EXTS:
                    files.append(fp)

    # Include tests if requested
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
                        try:
                            rel_posix = str(fp.relative_to(repo_root)).replace("\\", "/").lower()
                        except ValueError:
                            continue
                        if rel_posix in EXCLUDE_FILES:
                            continue
                        if fp.suffix.lower() in ALWAYS_EXTS:
                            files.append(fp)

    # Include documentation if requested
    if include_docs:
        docs_dir = repo_root / "docs"
        if docs_dir.exists():
            for dirpath, dirnames, filenames in os.walk(docs_dir):
                current_dir = Path(dirpath)
                for fname in filenames:
                    fp = current_dir / fname
                    if fp.suffix.lower() in {".md"}:
                        files.append(fp)
        
        # Top-level README
        for readme in repo_root.glob("README*.md"):
            files.append(readme)

    # Remove duplicates and sort
    files = sorted(set(files), key=lambda p: str(p))
    return files

def concatenate_codebase(
    output_dir: Path = Path("concatenated_codebase"),
    include_tests: bool = False,
    include_docs: bool = False,
) -> Path:
    """Concatenate ToT pipeline codebase for debugging purposes."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"tot_pipeline_codebase_{timestamp}.txt"

    repo_root = Path(__file__).resolve().parent.parent

    files_to_concat = gather_files(repo_root, include_tests, include_docs)
    logging.info(f"Found {len(files_to_concat)} files for ToT pipeline:")
    for fp in files_to_concat:
        try:
            rel = fp.relative_to(repo_root)
            print(f"✔ {rel}")
        except ValueError:
            print(f"✔ {fp}")

    with open(output_path, "w", encoding="utf-8", errors="ignore") as outfile:
        outfile.write(f"# ToT Pipeline Codebase Snapshot — generated {datetime.now().isoformat(timespec='seconds')}\n")
        outfile.write("# Pipeline: python -m multi_coder_analysis.main --use-tot --provider gemini --regex-mode live\n")
        outfile.write("=" * 100 + "\n\n")
        
        for idx, file_path in enumerate(files_to_concat, 1):
            try:
                relative_path = file_path.relative_to(repo_root)
            except ValueError:
                relative_path = file_path
                
            outfile.write(f"## {idx:04d}. {relative_path}\n")
            outfile.write("-" * 100 + "\n")
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
                    # Clean problematic characters
                    cleaned = raw.replace("\x00", "")
                    outfile.write(cleaned)
            except Exception as e:
                outfile.write(f"[ERROR reading {relative_path}: {e}]\n")
            outfile.write("\n\n")
            
        outfile.write("=" * 100 + "\n")
        outfile.write(f"# End of ToT pipeline snapshot — {len(files_to_concat)} files\n")

    logging.info(f"ToT pipeline codebase concatenated to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(
        description="Concatenate ToT pipeline codebase into a single file for debugging.",
        epilog="Focuses on files needed for: python -m multi_coder_analysis.main --use-tot --provider gemini --regex-mode live"
    )
    parser.add_argument("--output-dir", type=Path, default=Path("concatenated_codebase"), 
                       help="Destination directory for the concatenated file.")
    parser.add_argument("--include-tests", action="store_true", 
                       help="Include test files in the snapshot.")
    parser.add_argument("--include-docs", action="store_true", 
                       help="Include documentation files in the snapshot.")
    parser.add_argument("--verbose", action="store_true", 
                       help="Enable verbose logging (DEBUG level).")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    path = concatenate_codebase(
        output_dir=args.output_dir,
        include_tests=args.include_tests,
        include_docs=args.include_docs,
    )
    print(f"✅ ToT Pipeline concatenation complete: {path}")

if __name__ == "__main__":
    main() 