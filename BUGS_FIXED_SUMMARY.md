# Bug Fixes Summary for Enhanced Cue Detection JSON A/B Test

## Date: 2024-12-29

### Bugs Fixed:

1. **✅ Missing JSON layouts in ALL_LAYOUTS**
   - **Issue**: The `cue_detection_enhanced_json` and `cue_detection_enhanced_json_batch` layouts were defined in `run_multi_coder_tot.py` but missing from `ALL_LAYOUTS` in `layout_experiment.py`
   - **Fix**: Added both layouts to the `ALL_LAYOUTS` list
   - **Impact**: These layouts can now be used in layout experiments

2. **✅ Hardcoded `include_examples=True`**
   - **Issue**: 8 instances where `include_examples=True` was hardcoded instead of respecting `_EXAMPLES_POLICY`
   - **Fix**: Replaced all instances with `include_examples=(_EXAMPLES_POLICY != "none")`
   - **Impact**: The `--examples` flag now works correctly for JSON layouts

3. **✅ Duplicate global variable declarations**
   - **Issue**: `_EXAMPLES_POLICY` and `_REPLY_SCHEMA` were declared multiple times (5 times for `_EXAMPLES_POLICY`)
   - **Fix**: Removed duplicate declarations, keeping only one at the module level
   - **Impact**: Cleaner code, prevents potential confusion

4. **✅ Duplicate module content**
   - **Issue**: The entire module appeared to be duplicated multiple times in the file
   - **Fix**: Removed duplicate content, keeping only one complete module
   - **Impact**: Significantly reduced file size and eliminated redundancy

### Bugs NOT Fixed (Not actual bugs):

1. **Unused `include_all_rules` parameter** - This is intentional, parameter exists for future use
2. **Missing `hop_idx` in single-segment JSON layouts** - Already correctly uses `ctx.q_idx`

### CRITICAL BUG NOT FIXED:

1. **⚠️ Race condition with global variables** 
   - **Issue**: Layout experiments run concurrently using `ThreadPoolExecutor`. When multiple experiments run with different `--examples` settings, they all modify the same global `_EXAMPLES_POLICY` variable, causing interference.
   - **Impact**: This is a **REAL BUG** that can cause incorrect behavior. For example:
     - Experiment A starts with `--examples full`
     - Experiment B starts with `--examples none` and overwrites the global
     - Experiment A continues but now incorrectly uses no examples
   - **Fix needed**: Pass the examples policy through the call chain instead of using globals, or ensure experiments with different settings don't run concurrently.

## Testing Recommendations:

1. Run a layout experiment with the JSON layouts to ensure they work:
   ```bash
   python scripts/layout_experiment.py --layouts cue_detection_enhanced_json,cue_detection_enhanced_json_batch
   ```

2. Test the `--examples` flag with JSON layouts:
   ```bash
   python multi_coder_analysis/main.py --use-tot --examples none --layout cue_detection_enhanced_json
   ```

3. Verify no regression in existing layouts

## ⚠️ WARNING:
Do not run layout experiments with different `--examples` settings concurrently until the race condition is fixed. All experiments in a single run should use the same examples policy. 