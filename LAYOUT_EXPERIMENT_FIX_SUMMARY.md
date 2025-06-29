# Layout Experiment Fix Summary

## Overview
Fixed the built-in `--layout-experiment` flag in the multi_coder_analysis pipeline to avoid pickle errors and support all 13 implemented layouts.

## Problems Fixed

### 1. Pickle Error with ProcessPoolExecutor
**Issue**: The original implementation used `ProcessPoolExecutor` which tried to pickle objects containing thread locks, causing "cannot pickle '_thread.lock' object" errors.

**Fix**: Changed to `ThreadPoolExecutor` which avoids serialization issues since threads share memory.

### 2. Limited to 5 Layouts
**Issue**: Only tested 5 layouts (standard, recency, sandwich, minimal_system, question_first) instead of all 13 implemented layouts.

**Fix**: Added `ALL_LAYOUTS` list with all 13 layouts and made it the default. Added support for selecting specific layouts.

### 3. Wrong Output Directory
**Issue**: Output was created in `multi_coder_analysis/output/layout_experiments/` instead of `output/layout_experiments/`.

**Fix**: Changed the output path to use `Path("output") / "layout_experiments"`.

### 4. Missing Layout Selection Options
**Issue**: No way to specify which layouts to test.

**Fix**: Added multiple ways to select layouts:
- Command line: `--layouts standard hop_last`
- Environment variable: `TOT_LAYOUTS=all` or `TOT_LAYOUTS=standard,hop_last`
- Default: Tests all 13 layouts

## Files Modified

### 1. `multi_coder_analysis/layout_experiment.py`
- Changed from `ProcessPoolExecutor` to `ThreadPoolExecutor`
- Added `ALL_LAYOUTS` list with all 13 layouts
- Fixed output directory path
- Added layout selection logic (args, env var, default)
- Improved error handling and reporting
- Added progress indicators
- Enhanced comparison report with average F1 scores

### 2. `multi_coder_analysis/main.py`
- Added `--layouts` argument to specify which layouts to test

## Usage Examples

### Test specific layouts:
```bash
python -m multi_coder_analysis.main --use-tot --layout-experiment --layouts standard hop_last --gold-standard data.csv --input data.csv
```

### Test all layouts:
```bash
python -m multi_coder_analysis.main --use-tot --layout-experiment --gold-standard data.csv --input data.csv
```

### Using environment variable:
```bash
# PowerShell
$env:TOT_LAYOUTS="all"
python -m multi_coder_analysis.main --use-tot --layout-experiment --gold-standard data.csv --input data.csv

# Bash
TOT_LAYOUTS="standard,hop_last,evidence_based" python -m multi_coder_analysis.main --use-tot --layout-experiment --gold-standard data.csv --input data.csv
```

## All 13 Available Layouts

1. **standard** - Default layout with all context
2. **recency** - Recent information emphasized at the end
3. **sandwich** - Key info at beginning and end
4. **minimal_system** - Minimal system message
5. **question_first** - Question before context
6. **hop_last** - Current hop question at the end
7. **structured_json** - JSON-structured format
8. **segment_focus** - Focus on current segment
9. **instruction_first** - Instructions before content
10. **parallel_analysis** - Parallel analysis structure
11. **evidence_based** - Evidence-focused layout
12. **xml_structured** - XML-structured format
13. **primacy_recency** - Leverages both primacy and recency effects

## Output Structure

```
output/layout_experiments/[timestamp]/
├── experiment_config.json     # Experiment configuration
├── all_results.csv           # Raw results for all layouts
├── comparison_summary.csv    # Detailed metrics comparison
├── comparison_report.txt     # Human-readable report
├── summary.json             # JSON summary for programmatic access
├── standard/                # Results for standard layout
│   ├── model_labels_tot.csv
│   ├── comparison.csv
│   ├── metrics.json
│   └── traces_tot/
├── hop_last/               # Results for hop_last layout
│   └── ...
└── ...                     # Other layout directories
```

## Key Improvements

1. **Thread Safety**: Using ThreadPoolExecutor avoids serialization issues
2. **Flexibility**: Multiple ways to select layouts to test
3. **Comprehensive Testing**: Tests all 13 layouts by default
4. **Better Reporting**: Enhanced reports with average F1 scores and failed experiment tracking
5. **Progress Tracking**: Shows [x/y] progress during experiments
6. **Graceful Shutdown**: Handles Ctrl+C properly
7. **Error Recovery**: Continues with other layouts if one fails 