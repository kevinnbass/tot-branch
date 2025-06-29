# Prompt Tracking Implementation

## Overview
This implementation ensures that only the prompts actually used during a pipeline run are copied to the output folder, rather than copying the entire prompts directory.

## Changes Made

### 1. Created Prompt Tracker Module (`multi_coder_analysis/utils/prompt_tracker.py`)
- Tracks which prompt files are loaded during execution
- Thread-safe implementation using locks
- Provides method to copy only used prompts to output directory
- Global tracker instance with reset capability

### 2. Modified Prompt Loader (`multi_coder_analysis/utils/prompt_loader.py`)
- Added tracking call when prompts are loaded via `load_prompt_and_meta()`
- Gracefully handles cases where tracker is not available

### 3. Updated ToT Module (`multi_coder_analysis/run_multi_coder_tot.py`)
- Modified `_load_global_header()` to track GLOBAL_HEADER.txt usage
- Modified `_load_global_footer()` to track GLOBAL_FOOTER.txt usage
- Updated `_assemble_prompt()` to track header/footer files loaded directly
- Updated `_assemble_prompt_batch()` to track header/footer files in batch mode

### 4. Modified Main Pipeline (`multi_coder_analysis/main.py`)
- Removed immediate copying of entire prompts directory
- Added code to copy only used prompts after pipeline completes
- Falls back to copying all prompts if tracker is unavailable
- Generates concatenated prompts file from only the used prompts

## How It Works

1. **During Execution**: When prompts are loaded (hop files, headers, footers), the prompt tracker records their paths
2. **After Pipeline Completes**: The tracker copies only the recorded prompt files to the output directory
3. **Concatenation**: A concatenated prompts file is generated containing only the prompts that were actually used

## Benefits

- **Reduced Output Size**: Only includes prompts that were actually used in the run
- **Better Auditability**: Clear record of which prompts influenced the results
- **Cleaner Output**: No unused prompt files cluttering the output directory

## Example

For a run using layout `minimal_system` that processes statements requiring hops 1-5:
- **Before**: All 12 hop files + variations + headers/footers copied (30+ files)
- **After**: Only hop_Q01.txt through hop_Q05.txt + GLOBAL_HEADER.txt + GLOBAL_FOOTER.txt (7 files)

## Testing

The implementation was tested with a test script that verified:
- Prompts are tracked when loaded
- Only used prompts are copied to output
- Unused prompts are not included
- Thread safety is maintained 