#!/usr/bin/env python3
"""
Consolidate individual trace files from traces_tot_mismatch directories
into a single JSONL file for easy analysis and copy/paste operations.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import argparse

def find_mismatch_directories(base_path="output"):
    """Find all traces_tot_mismatch directories in the output structure."""
    mismatch_dirs = []
    base = Path(base_path)
    
    for root, dirs, files in os.walk(base):
        if "traces_tot_mismatch" in dirs:
            mismatch_path = Path(root) / "traces_tot_mismatch"
            mismatch_dirs.append(mismatch_path)
    
    return mismatch_dirs

def consolidate_traces(output_file="consolidated_mismatch_traces.jsonl", base_path="output"):
    """Consolidate all mismatch trace files into a single JSONL file."""
    
    mismatch_dirs = find_mismatch_directories(base_path)
    
    if not mismatch_dirs:
        print("No traces_tot_mismatch directories found.")
        return
    
    print(f"Found {len(mismatch_dirs)} mismatch directories:")
    for dir_path in mismatch_dirs:
        print(f"  - {dir_path}")
    
    consolidated_entries = []
    total_files = 0
    
    for mismatch_dir in mismatch_dirs:
        if not mismatch_dir.exists():
            continue
            
        # Get the run timestamp from the path for context
        run_timestamp = None
        path_parts = str(mismatch_dir).split(os.sep)
        for part in path_parts:
            if part.startswith("202"):  # Matches YYYYMMDD_HHMMSS format
                run_timestamp = part
                break
        
        # Process each JSONL file in the directory
        for jsonl_file in mismatch_dir.glob("*.jsonl"):
            total_files += 1
            statement_id = jsonl_file.stem  # filename without extension
            
            print(f"Processing: {jsonl_file.name}")
            
            # Read the trace entries
            trace_entries = []
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            trace_entries.append(json.loads(line))
            except Exception as e:
                print(f"Error reading {jsonl_file}: {e}")
                continue
            
            # Create consolidated entry
            consolidated_entry = {
                "statement_id": statement_id,
                "run_timestamp": run_timestamp,
                "source_file": str(jsonl_file.relative_to(Path(base_path))),
                "trace_count": len(trace_entries),
                "full_trace": trace_entries
            }
            
            consolidated_entries.append(consolidated_entry)
    
    # Write consolidated file
    output_path = Path(output_file)
    print(f"\nWriting {len(consolidated_entries)} consolidated entries to: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in consolidated_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    # Print summary
    print(f"\n=== Consolidation Summary ===")
    print(f"Mismatch directories processed: {len(mismatch_dirs)}")
    print(f"Individual trace files processed: {total_files}")
    print(f"Consolidated entries created: {len(consolidated_entries)}")
    print(f"Output file: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")
    
    return output_path

def create_readable_summary(consolidated_file, summary_file=None):
    """Create a more readable summary version of the consolidated traces."""
    
    if summary_file is None:
        base_name = Path(consolidated_file).stem
        summary_file = f"{base_name}_summary.txt"
    
    consolidated_path = Path(consolidated_file)
    if not consolidated_path.exists():
        print(f"Consolidated file not found: {consolidated_path}")
        return
    
    with open(consolidated_path, 'r', encoding='utf-8') as f:
        entries = [json.loads(line) for line in f if line.strip()]
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=== CONSOLIDATED MISMATCH TRACES SUMMARY ===\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Entries: {len(entries)}\n\n")
        
        for i, entry in enumerate(entries, 1):
            f.write(f"--- ENTRY {i}: {entry['statement_id']} ---\n")
            f.write(f"Run: {entry['run_timestamp']}\n")
            f.write(f"Source: {entry['source_file']}\n")
            f.write(f"Trace Steps: {entry['trace_count']}\n")
            f.write("\nTRACE SUMMARY:\n")
            
            for step in entry['full_trace']:
                q_num = step.get('Q', '?')
                answer = step.get('answer', 'unknown')
                rationale = step.get('rationale', 'No rationale')[:100] + "..."
                f.write(f"  Q{q_num}: {answer} - {rationale}\n")
            
            f.write("\n" + "="*60 + "\n\n")
    
    print(f"Readable summary created: {summary_file}")
    return summary_file

def main():
    parser = argparse.ArgumentParser(description="Consolidate mismatch trace files")
    parser.add_argument("--output", "-o", default="consolidated_mismatch_traces.jsonl", 
                       help="Output file name for consolidated traces")
    parser.add_argument("--base-path", "-b", default="output",
                       help="Base path to search for mismatch directories")
    parser.add_argument("--summary", "-s", action="store_true",
                       help="Also create a readable summary file")
    
    args = parser.parse_args()
    
    # Consolidate traces
    output_file = consolidate_traces(args.output, args.base_path)
    
    # Create summary if requested
    if args.summary and output_file:
        create_readable_summary(output_file)

if __name__ == "__main__":
    main() 