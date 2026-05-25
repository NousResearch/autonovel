"""
Test for empty except blocks fix - RED PHASE

Generic Formula: SECURE_EXCEPTION_HANDLING
Expression: λ(exception, fallback, message) → (log_warning(message), return fallback)
"""
import pytest
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import AFTER path is set
from draft_chapter import load_file
from reader_panel import get_novel_stats


class TestEmptyExceptFix:
    """Tests for proper exception handling WITH LOGGING (not silent failures)."""
    
    def test_load_file_should_log_on_file_not_found(self, caplog):
        """load_file should LOG a warning when file not found."""
        caplog.set_level(logging.WARNING)
        result = load_file("/tmp/definitely_nonexistent_file_12345.txt")
        assert len(caplog.records) > 0, "load_file should log warning on FileNotFoundError"
    
    def test_get_novel_title_should_log_on_corrupted_json(self, caplog, tmp_path):
        """get_novel_title should LOG warning when JSON is corrupted."""
        # Import HERE to ensure logger is fresh for this test
        import importlib
        import gen_revision
        importlib.reload(gen_revision)  # Force fresh import
        
        corrupted = tmp_path / "state.json"
        corrupted.write_text("{ invalid json that will fail to parse }")
        
        caplog.set_level(logging.WARNING)
        result = gen_revision.get_novel_title(state_path=corrupted)
        
        # Print all captured logs for debugging
        print(f"\n=== CAPTURED LOGS ===")
        for r in caplog.records:
            print(f"  {r.name}: {r.message}")
        print(f"=== TOTAL: {len(caplog.records)} records ===\n")
        
        assert len(caplog.records) > 0, f"get_novel_title should log JSON decode error"
    
    def test_get_novel_stats_should_log_on_corrupted_json(self, caplog, tmp_path):
        """get_novel_stats should LOG warning when JSON is corrupted."""
        caplog.set_level(logging.WARNING)
        corrupted = tmp_path / "state.json"  
        corrupted.write_text("{ this is definitely not valid JSON }")
        
        result = get_novel_stats(state_path=corrupted)
        assert len(caplog.records) > 0, "get_novel_stats should log on corrupted JSON"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
