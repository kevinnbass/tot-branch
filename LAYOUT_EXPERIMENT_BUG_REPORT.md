# Layout Experiment Bug Report

## Summary

After a comprehensive bug sweep of the layout experiment functionality, I found that the codebase is in good working order. The command you want to run should work correctly.

## Verification Results

### ✅ Prerequisites Check
- **Input file exists**: `multi_coder_analysis/data/gold_standard_preliminary.csv` (389KB, 2027 lines)
- **Gold standard file exists**: Same file used for comparison
- **Layout config exists**: `layout_experiment_config.yaml` with 1 enabled batch containing 6 layouts
- **All required modules exist**: main.py, layout_experiment.py, run_multi_coder_tot.py

### ✅ Configuration Validation
The layout experiment config file is properly structured with:
- Experiment metadata (name, description, base_config)
- 1 enabled batch (`phase1_batch1`) with 6 layouts:
  - minimal_segment_first
  - minimal_question_twice
  - minimal_json_segment
  - minimal_parallel_criteria
  - minimal_hop_sandwich
  - minimal_system (baseline)
- Execution settings (parallel_workers: 6)
- Analysis settings (primary_metrics, comparison_threshold)

### ✅ Code Analysis Results

1. **All layout implementations are present** in both `_assemble_prompt` and `_assemble_prompt_batch` functions
2. **VALID_LAYOUTS list is up to date** and includes all minimal system variations
3. **Parameter passing is correct** - the `confidence_scores` parameter is properly passed through all function calls
4. **Command-line arguments are properly defined** in main.py with layout experiment options

## Command Validation

The command you want to run is valid:
```bash
python -m multi_coder_analysis.main --use-tot --input multi_coder_analysis\data\gold_standard_preliminary.csv --gold-standard multi_coder_analysis\data\gold_standard_preliminary.csv --provider gemini --model "models/gemini-2.5-flash-preview-04-17" --concurrency 3 --batch-size 260 --regex-mode live --start 260 --end 519 --layout-experiment --layout-config layout_experiment_config.yaml --layout-workers 6
```

## Execution Flow

When you run this command, it will:

1. Parse arguments and detect `--layout-experiment` flag
2. Load the layout configuration from `layout_experiment_config.yaml`
3. Extract enabled layouts (6 minimal system variations)
4. Run experiments in parallel using 6 workers
5. Process rows 260-519 from the input file with batch size 260
6. For each layout:
   - Run the ToT pipeline with the specific layout
   - Calculate metrics against the gold standard
   - Save results in `output/layout_experiments/[timestamp]/[layout_name]/`
7. Generate a comparison report showing:
   - Accuracy for each layout
   - Per-frame precision/recall/F1 scores
   - Duration statistics
   - Best performing layout

## Expected Output Structure

```
output/layout_experiments/[timestamp]/
├── experiment_config.json
├── layout_config.yaml (copy)
├── all_results.csv
├── comparison_summary.csv
├── comparison_report.txt
├── minimal_segment_first/
│   ├── model_labels_tot.csv
│   ├── comparison.csv
│   ├── mismatches.csv (if any)
│   ├── consolidated_mismatch_traces.jsonl
│   └── traces_tot/
├── minimal_question_twice/
│   └── ... (same structure)
├── minimal_json_segment/
│   └── ... (same structure)
├── minimal_parallel_criteria/
│   └── ... (same structure)
├── minimal_hop_sandwich/
│   └── ... (same structure)
└── minimal_system/
    └── ... (same structure)
```

## Recommendations

1. **Monitor memory usage** - Running 6 parallel experiments with batch size 260 may consume significant memory
2. **Check API rate limits** - With concurrency=3 and 6 parallel experiments, you'll have up to 18 concurrent API calls
3. **Expect runtime** - Processing 260 rows × 6 layouts × 12 hops will take considerable time
4. **Review results** - The comparison report will show which layout performs best on your data

## No Critical Bugs Found

The layout experiment functionality is properly implemented and ready to use. The command should execute successfully.
