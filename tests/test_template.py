"""Tests for the template module.

This module demonstrates the testing conventions for RABCDAsm,
including fixtures, parametrization, and proper test organization.
"""

import pytest
from pathlib import Path
from src.template import ABCAnalyzer, ProtectionError

# Test Data
TEST_DATA_DIR = Path(__file__).parent / "data"
VALID_SWF = TEST_DATA_DIR / "valid.swf"
INVALID_SWF = TEST_DATA_DIR / "invalid.swf"

@pytest.fixture
def analyzer(tmp_path):
    """Fixture providing a test SWF file and analyzer."""
    test_swf = tmp_path / "test.swf"
    test_swf.write_bytes(b'FWS' + b'\x00' * 5)  # Minimal valid SWF
    return ABCAnalyzer(test_swf)

@pytest.mark.parametrize("swf_header,expected", [
    (b'FWS\x00\x00\x00\x00\x00', True),
    (b'CWS\x00\x00\x00\x00\x00', True),
    (b'ZWS\x00\x00\x00\x00\x00', True),
    (b'XXX\x00\x00\x00\x00\x00', False),
])
def test_swf_validation(tmp_path, swf_header, expected):
    """Test SWF file validation with various headers."""
    test_swf = tmp_path / "test.swf"
    test_swf.write_bytes(swf_header)
    
    if expected:
        analyzer = ABCAnalyzer(test_swf)
        assert analyzer._is_valid_swf()
    else:
        with pytest.raises(ValueError):
            ABCAnalyzer(test_swf)

def test_analyzer_initialization(analyzer):
    """Test analyzer initialization."""
    assert analyzer.swf_path.exists()
    assert isinstance(analyzer._cache, dict)
    assert len(analyzer._cache) == 0

def test_protection_analysis(analyzer):
    """Test protection analysis functionality."""
    results = analyzer.analyze_protection()
    
    assert isinstance(results, dict)
    assert 'encryption_type' in results
    assert 'protection_level' in results
    assert isinstance(results['obfuscation'], list)
    assert isinstance(results['anti_debug'], list)

@pytest.mark.parametrize("deep_scan,timeout", [
    (True, None),
    (False, 30),
    (True, 60)
])
def test_analysis_parameters(analyzer, deep_scan, timeout):
    """Test analysis with different parameters."""
    results = analyzer.analyze_protection(
        deep_scan=deep_scan,
        timeout=timeout
    )
    assert results['protection_level'] >= 0

def test_invalid_file():
    """Test handling of invalid files."""
    with pytest.raises(FileNotFoundError):
        ABCAnalyzer("nonexistent.swf")

def test_analysis_error(analyzer, monkeypatch):
    """Test error handling during analysis."""
    def mock_analysis(*args, **kwargs):
        raise Exception("Analysis failed")
    
    monkeypatch.setattr(
        analyzer,
        '_is_valid_swf',
        mock_analysis
    )
    
    with pytest.raises(ProtectionError):
        analyzer.analyze_protection()
