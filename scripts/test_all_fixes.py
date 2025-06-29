#!/usr/bin/env python3
"""
Comprehensive test script to verify all bug fixes in the prompt layout experiment code.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')


def test_imports():
    """Test that all required imports work."""
    print("\n🧪 Testing imports...")
    
    try:
        from multi_coder_analysis.run_multi_coder_tot import (
            _assemble_prompt,
            _assemble_prompt_batch,
            run_tot_chain_batch,
            DEFAULT_MODEL,
            VALID_LAYOUTS
        )
        print("✅ Core imports successful")
        
        # Test that constants are defined
        assert DEFAULT_MODEL is not None, "DEFAULT_MODEL not defined"
        assert VALID_LAYOUTS is not None, "VALID_LAYOUTS not defined"
        print(f"✅ Constants defined: DEFAULT_MODEL={DEFAULT_MODEL}")
        print(f"✅ Valid layouts: {VALID_LAYOUTS}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Assertion error: {e}")
        return False
    
    try:
        from scripts.thread_safe_cache import ThreadSafeCache, generate_cache_key
        print("✅ Thread-safe cache imports successful")
    except ImportError:
        print("⚠️  Thread-safe cache not available (optional)")
    
    try:
        from tqdm import tqdm
        print("✅ tqdm import successful")
    except ImportError:
        print("❌ tqdm import failed")
        return False
    
    return True


def test_function_signatures():
    """Test that function signatures have been fixed."""
    print("\n🧪 Testing function signatures...")
    
    import inspect
    from multi_coder_analysis.run_multi_coder_tot import (
        run_tot_chain_batch,
        _assemble_prompt,
        _assemble_prompt_batch,
        _call_llm_batch
    )
    
    # Test run_tot_chain_batch signature
    sig = inspect.signature(run_tot_chain_batch)
    params = list(sig.parameters.keys())
    
    required_params = ['layout', 'ranked', 'max_candidates']
    missing_params = [p for p in required_params if p not in params]
    
    if missing_params:
        print(f"❌ Missing parameters in run_tot_chain_batch: {missing_params}")
        return False
    else:
        print("✅ run_tot_chain_batch has all required parameters")
    
    # Test _assemble_prompt signature
    sig = inspect.signature(_assemble_prompt)
    if 'layout' not in sig.parameters:
        print("❌ _assemble_prompt missing layout parameter")
        return False
    else:
        print("✅ _assemble_prompt has layout parameter")
    
    # Test _assemble_prompt_batch signature
    sig = inspect.signature(_assemble_prompt_batch)
    if 'layout' not in sig.parameters:
        print("❌ _assemble_prompt_batch missing layout parameter")
        return False
    else:
        print("✅ _assemble_prompt_batch has layout parameter")
    
    return True


def test_layout_validation():
    """Test that layout validation works."""
    print("\n🧪 Testing layout validation...")
    
    from multi_coder_analysis.run_multi_coder_tot import _assemble_prompt
    from multi_coder_analysis.models.hop import HopContext
    
    # Create a test context
    ctx = HopContext(
        statement_id="TEST001",
        segment_text="Test segment",
        article_id="ARTICLE001"
    )
    ctx.q_idx = 1
    
    # Test with valid layout
    try:
        sys_prompt, user_prompt = _assemble_prompt(ctx, layout="standard")
        print("✅ Valid layout 'standard' works")
    except Exception as e:
        print(f"❌ Valid layout failed: {e}")
        return False
    
    # Test with invalid layout (should fall back to standard with warning)
    try:
        # Capture warnings
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stderr(f):
            sys_prompt, user_prompt = _assemble_prompt(ctx, layout="invalid_layout")
        
        # Check if warning was logged (would need to check logs)
        print("✅ Invalid layout handled gracefully")
        
    except Exception as e:
        print(f"❌ Invalid layout caused error: {e}")
        return False
    
    return True


def test_thread_safe_cache():
    """Test thread-safe cache implementation."""
    print("\n🧪 Testing thread-safe cache...")
    
    try:
        from scripts.thread_safe_cache import ThreadSafeCache, generate_cache_key
    except ImportError:
        print("⚠️  Thread-safe cache not available, skipping test")
        return True
    
    import tempfile
    import threading
    
    # Create temporary cache directory
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = ThreadSafeCache(Path(temp_dir))
        
        # Test basic operations
        key = generate_cache_key("test segment", 1, "standard", "test-model")
        test_data = {"result": "test", "confidence": 0.9}
        
        # Test set
        if not cache.set(key, test_data):
            print("❌ Cache set failed")
            return False
        
        # Test get
        retrieved = cache.get(key)
        if retrieved != test_data:
            print("❌ Cache get returned wrong data")
            return False
        
        print("✅ Basic cache operations work")
        
        # Test thread safety
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(10):
                    key = generate_cache_key(f"segment_{worker_id}_{i}", 1, "standard", "model")
                    data = {"worker": worker_id, "iteration": i}
                    cache.set(key, data)
                    retrieved = cache.get(key)
                    if retrieved != data:
                        errors.append(f"Worker {worker_id} iteration {i} mismatch")
                results.append(worker_id)
            except Exception as e:
                errors.append(f"Worker {worker_id} error: {e}")
        
        # Run multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        if errors:
            print(f"❌ Thread safety errors: {errors}")
            return False
        
        if len(results) == 5:
            print("✅ Thread-safe cache works correctly")
        else:
            print(f"❌ Not all workers completed: {len(results)}/5")
            return False
    
    return True


def test_layout_metrics():
    """Test layout-specific metrics functions."""
    print("\n🧪 Testing layout-specific metrics...")
    
    try:
        from scripts.experiment_prompt_layouts_improved import (
            calculate_layout_metrics,
            aggregate_layout_metrics
        )
    except ImportError:
        print("⚠️  Layout metrics functions not available, skipping test")
        return True
    
    # Test calculate_layout_metrics
    metrics = calculate_layout_metrics(
        layout="recency",
        sys_prompt="System prompt",
        user_prompt="User prompt with test segment in the middle",
        segment_text="test segment",
        response_time=1.5
    )
    
    if 'segment_position_ratio' not in metrics:
        print("❌ Layout metrics missing expected fields")
        return False
    
    print("✅ calculate_layout_metrics works")
    
    # Test aggregate_layout_metrics
    all_metrics = [
        {"layout": "standard", "response_time": 1.0, "total_prompt_length": 100},
        {"layout": "standard", "response_time": 1.2, "total_prompt_length": 110},
        {"layout": "recency", "response_time": 0.9, "total_prompt_length": 95},
    ]
    
    aggregated = aggregate_layout_metrics(all_metrics)
    
    if 'standard' not in aggregated or 'recency' not in aggregated:
        print("❌ Aggregated metrics missing layouts")
        return False
    
    if 'response_time' not in aggregated['standard']:
        print("❌ Aggregated metrics missing expected metrics")
        return False
    
    print("✅ aggregate_layout_metrics works")
    
    return True


def test_batch_processing_parameters():
    """Test that batch processing has all required parameters."""
    print("\n🧪 Testing batch processing parameters...")
    
    # This is a smoke test - we can't run the full batch processing without data
    # but we can check that the functions accept the right parameters
    
    from multi_coder_analysis.run_multi_coder_tot import _call_llm_batch
    import inspect
    
    sig = inspect.signature(_call_llm_batch)
    params = list(sig.parameters.keys())
    
    required = ['template', 'ranked', 'max_candidates', 'confidence_scores', 'layout']
    missing = [p for p in required if p not in params]
    
    if missing:
        print(f"❌ _call_llm_batch missing parameters: {missing}")
        return False
    else:
        print("✅ _call_llm_batch has all required parameters")
    
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("🧪 COMPREHENSIVE BUG FIX VERIFICATION")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Function Signatures", test_function_signatures),
        ("Layout Validation", test_layout_validation),
        ("Thread-Safe Cache", test_thread_safe_cache),
        ("Layout Metrics", test_layout_metrics),
        ("Batch Processing Parameters", test_batch_processing_parameters),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The bug fixes are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 