"""Integration tests for refactored architecture (Phase 10)."""

import pytest
import warnings
from pathlib import Path
from unittest.mock import Mock, patch

from multi_coder_analysis.models import HopContext
from multi_coder_analysis.core.regex import Engine
from multi_coder_analysis.providers import get_provider
from multi_coder_analysis.config import load_settings
from multi_coder_analysis.runtime.tracing import TraceWriter, get_logger


class TestArchitecturalIntegration:
    """Test that all layers work together correctly."""
    
    def test_models_layer_pure(self):
        """Test that models layer has no I/O dependencies."""
        ctx = HopContext(
            statement_id="test_001",
            segment_text="This is alarming news about climate change.",
            article_id="art_123"
        )
        
        # Should be pure data - no side effects
        assert ctx.statement_id == "test_001"
        assert ctx.final_frame is None
        assert not ctx.is_concluded
        
        # Should be serializable
        import json
        from dataclasses import asdict
        data = asdict(ctx)
        json.dumps(data)  # Should not raise
    
    def test_core_layer_pure_functions(self):
        """Test that core layer has no I/O side effects."""
        engine = Engine.default()
        
        # Should be deterministic
        result1 = engine.match("alarming climate change", hop=1)
        result2 = engine.match("alarming climate change", hop=1)
        assert result1 == result2
        
        # Should not perform I/O (test by mocking filesystem)
        with patch('pathlib.Path.read_text') as mock_read:
            # Engine should use cached rules, not read files
            engine.match("test text", hop=1)
            # Allow one call for initial loading if not cached
            assert mock_read.call_count <= 1
    
    def test_providers_layer_protocol_compliance(self):
        """Test that providers implement the protocol correctly."""
        # Mock provider for testing
        mock_provider = Mock()
        mock_provider.generate.return_value = "Test response"
        mock_provider.get_last_thoughts.return_value = "Test thoughts"
        mock_provider.get_last_usage.return_value = {"tokens": 100}
        
        # Should satisfy protocol requirements
        from multi_coder_analysis.providers.base import ProviderProtocol
        assert isinstance(mock_provider, ProviderProtocol)
        
        # Should work with factory
        with patch('multi_coder_analysis.providers.get_provider', return_value=mock_provider):
            provider = get_provider("mock")
            response = provider.generate("test prompt", "test-model")
            assert response == "Test response"
    
    def test_configuration_layer_validation(self):
        """Test that configuration validation works correctly."""
        from multi_coder_analysis.config.settings import Settings
        
        # Valid config should work
        settings = Settings(
            provider="gemini",
            batch_size=4,
            regex_mode="live"
        )
        assert settings.provider == "gemini"
        assert settings.batch_size == 4
        
        # Invalid config should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            Settings(batch_size=-1)  # Negative batch size should fail
    
    def test_tracing_layer_structured_output(self):
        """Test that tracing produces structured output."""
        import tempfile
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = TraceWriter(Path(tmpdir))
            
            # Write a trace
            writer.write_trace("test_001", {"hop": 1, "result": "alarming"})
            
            # Verify NDJSON format
            trace_file = Path(tmpdir) / "test_001.ndjson"
            assert trace_file.exists()
            
            content = trace_file.read_text()
            trace_entry = json.loads(content.strip())
            
            assert "run_id" in trace_entry
            assert trace_entry["statement_id"] == "test_001"
            assert trace_entry["trace_data"]["hop"] == 1
    
    def test_deprecation_warnings_emitted(self):
        """Test that deprecated imports emit warnings."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # This should emit a deprecation warning
            import llm_providers  # noqa
            
            # Verify warning was emitted
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
            assert any("deprecated" in str(warning.message).lower() for warning in w)
    
    def test_backward_compatibility_maintained(self):
        """Test that old import paths still work."""
        # Legacy imports should still work (with warnings)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            
            # These should not raise ImportError
            from hop_context import HopContext as LegacyHopContext  # noqa
            from regex_engine import match as legacy_match  # noqa
            
            # Should be functionally equivalent
            ctx1 = HopContext(statement_id="test", segment_text="test", article_id="test")
            ctx2 = LegacyHopContext(statement_id="test", segment_text="test", article_id="test")
            
            assert type(ctx1) == type(ctx2)
    
    def test_pipeline_integration(self):
        """Test that the new pipeline architecture works end-to-end."""
        from multi_coder_analysis.core.pipeline.tot import build_tot_pipeline
        
        # Mock provider
        mock_provider = Mock()
        mock_provider.generate.return_value = "Alarmist framing detected"
        mock_provider.get_last_thoughts.return_value = "Analysis thoughts"
        mock_provider.get_last_usage.return_value = {"tokens": 50}
        
        # Build pipeline
        pipeline = build_tot_pipeline(mock_provider, "test-model")
        
        # Create test context
        ctx = HopContext(
            statement_id="test_pipeline",
            segment_text="This alarming climate report shows devastating impacts.",
            article_id="test_article"
        )
        
        # Run pipeline
        result = pipeline.run(ctx)
        
        # Verify result
        assert result.statement_id == "test_pipeline"
        # Pipeline should have processed the context
        assert result is not None
    
    def test_logging_integration(self):
        """Test that structured logging works correctly."""
        logger = get_logger(__name__)
        
        # Should be a structlog logger
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'bind')
        
        # Should include run_id
        bound_logger = logger.bind(test_key="test_value")
        assert bound_logger is not None
    
    def test_settings_environment_override(self):
        """Test that environment variables override settings."""
        import os
        from multi_coder_analysis.config.settings import Settings
        
        # Set environment variable
        original_value = os.environ.get("MCA_PROVIDER")
        try:
            os.environ["MCA_PROVIDER"] = "test_provider"
            
            settings = Settings()
            assert settings.provider == "test_provider"
            
        finally:
            # Cleanup
            if original_value is not None:
                os.environ["MCA_PROVIDER"] = original_value
            else:
                os.environ.pop("MCA_PROVIDER", None)


class TestPerformanceRegression:
    """Test that refactoring doesn't degrade performance."""
    
    def test_regex_engine_performance(self):
        """Test that regex engine meets performance requirements."""
        import time
        
        engine = Engine.default()
        test_text = "This is an alarming report about climate change impacts."
        
        # Warm up
        for _ in range(10):
            engine.match(test_text, hop=1)
        
        # Measure performance
        start_time = time.perf_counter()
        for _ in range(1000):
            engine.match(test_text, hop=1)
        end_time = time.perf_counter()
        
        avg_time_ms = (end_time - start_time) * 1000 / 1000
        
        # Should be under 3ms per call on average
        assert avg_time_ms < 3.0, f"Regex engine too slow: {avg_time_ms:.2f}ms per call"
    
    def test_memory_usage_stable(self):
        """Test that repeated operations don't leak memory."""
        import gc
        
        engine = Engine.default()
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform many operations
        for i in range(1000):
            ctx = HopContext(
                statement_id=f"test_{i}",
                segment_text=f"Test text {i}",
                article_id=f"article_{i}"
            )
            engine.match(ctx.segment_text, hop=1)
        
        # Force garbage collection again
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Object count shouldn't grow significantly
        growth = final_objects - initial_objects
        assert growth < 100, f"Memory leak detected: {growth} objects created"


if __name__ == "__main__":
    pytest.main([__file__]) 