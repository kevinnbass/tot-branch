# Additional Bugs Found in Prompt Layout Experiment Code

## 1. **Missing `confidence_scores` Parameter in `run_tot_chain_batch`**
- **Location**: `multi_coder_analysis/run_multi_coder_tot.py`, line 1987
- **Issue**: When calling `run_tot_chain_batch`, the `confidence_scores` parameter is not passed, but it's used inside the function
- **Impact**: Batch processing might not handle confidence scoring correctly
- **Fix**: Add `confidence_scores` parameter to the function signature and pass it through

## 2. **Incorrect Function Signature for `_provider_factory`**
- **Location**: `multi_coder_analysis/run_multi_coder_tot.py`, line 808
- **Issue**: The `_provider_factory` function is defined with `ranked` and `max_candidates` parameters, but it should just return a provider instance
- **Impact**: This is likely a copy-paste error that will cause runtime errors
- **Fix**: Remove the incorrect parameters from `_provider_factory`

## 3. **Missing Import for `tqdm`**
- **Location**: `multi_coder_analysis/run_multi_coder_tot.py`
- **Issue**: The code uses `tqdm` but it's not imported
- **Impact**: Will cause `NameError` when progress bars are enabled
- **Fix**: Add `from tqdm import tqdm` to imports

## 4. **Potential Race Condition in Token Accumulator**
- **Location**: Throughout batch processing code
- **Issue**: `token_accumulator['segments_regex_ids']` is a set that's modified without proper locking in some places
- **Impact**: In concurrent execution, this could lead to lost updates
- **Fix**: Always use `token_lock` when modifying the set

## 5. **Missing Error Handling for Layout-Specific Logic**
- **Location**: `_assemble_prompt` and `_assemble_prompt_batch` functions
- **Issue**: If an unknown layout is passed, the code will silently use the standard layout without warning
- **Impact**: Users might think they're using a custom layout when they're not
- **Fix**: Add validation and warning for unknown layouts

## 6. **Inconsistent Parameter Passing in Layout Experiment**
- **Location**: `multi_coder_analysis/layout_experiment.py`
- **Issue**: The `confidence_scores` parameter is not passed to `run_coding_step_tot`
- **Impact**: Layout experiments won't test confidence scoring features
- **Fix**: Add confidence_scores to the experiment configuration

## 7. **Missing Global Variable Declaration**
- **Location**: `multi_coder_analysis/run_multi_coder_tot.py`, line 1763
- **Issue**: `_MISS_PATH` is assigned as a global but not declared with `global` keyword
- **Impact**: Might cause issues in some Python versions or with certain linters
- **Fix**: Add `global _MISS_PATH` before assignment

## 8. **Potential File Handle Leak**
- **Location**: Multiple places where files are opened for writing
- **Issue**: Some file operations don't use context managers
- **Impact**: File handles might not be properly closed on exceptions
- **Fix**: Always use `with` statements for file operations

## 9. **Missing Type Hints Causing Confusion**
- **Location**: Various function signatures
- **Issue**: Parameters like `batch_ctx` don't have type hints, making it unclear what type is expected
- **Impact**: Harder to maintain and debug
- **Fix**: Add proper type hints throughout

## 10. **Hardcoded Default Values**
- **Location**: Various places with model names and parameters
- **Issue**: Default model "models/gemini-2.5-flash-preview-04-17" is hardcoded in multiple places
- **Impact**: Difficult to update when models change
- **Fix**: Define constants at module level

## Quick Fixes Script

```python
#!/usr/bin/env python3
"""Quick fixes for additional bugs found."""

def fix_provider_factory():
    """Fix the _provider_factory function signature."""
    # In run_tot_chain_batch, around line 808
    # Change from:
    #   def _provider_factory(ranked: bool = False, max_candidates: int = 5):
    # To:
    #   def _provider_factory():

def fix_missing_imports():
    """Add missing imports."""
    # Add at the top of run_multi_coder_tot.py:
    # from tqdm import tqdm

def fix_confidence_scores_param():
    """Add confidence_scores to run_tot_chain_batch."""
    # Add to function signature:
    # confidence_scores: bool = False,
    
    # Pass to _call_llm_batch calls:
    # confidence_scores=confidence_scores,

def fix_global_declaration():
    """Fix missing global declaration."""
    # Before line 1763, add:
    # global _MISS_PATH

def add_layout_validation():
    """Add validation for unknown layouts."""
    # In _assemble_prompt and _assemble_prompt_batch:
    valid_layouts = ['standard', 'recency', 'sandwich', 'minimal_system', 'question_first']
    if layout not in valid_layouts:
        logging.warning(f"Unknown layout '{layout}', using 'standard' instead")
        layout = 'standard'
```

## Priority Fixes

### Critical (Causes Runtime Errors)
1. Missing `tqdm` import
2. Incorrect `_provider_factory` signature
3. Missing `confidence_scores` parameter

### Important (Causes Incorrect Behavior)
1. Race condition in token accumulator
2. Missing layout validation
3. File handle leaks

### Nice to Have (Code Quality)
1. Missing type hints
2. Hardcoded default values
3. Missing global declarations

## Testing Recommendations

1. **Unit Tests**: Test each layout with both single and batch processing
2. **Integration Tests**: Run full experiments with all layouts
3. **Concurrency Tests**: Test with high concurrency to catch race conditions
4. **Error Tests**: Test with invalid layouts and parameters
5. **Performance Tests**: Compare token usage across layouts 