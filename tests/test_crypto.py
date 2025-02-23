"""
Test suite for cryptographic operations
Based on tools from RoboTool/tools_backup
"""

import os
import pytest
from pathlib import Path
from tools.lib.swf_analyzer import SWFAnalyzer
from tools.lib.rabcdasm_wrapper import RABCDAsmWrapper

class TestCryptoAnalysis:
    @pytest.fixture
    def analyzer(self):
        rabcdasm = RABCDAsmWrapper(os.path.join('tools', 'rabcdasm'))
        return SWFAnalyzer(rabcdasm)
        
    @pytest.fixture
    def sample_swf(self):
        return os.path.join(os.path.dirname(__file__), 'sample_data', 'test.swf')
        
    def test_detect_encryption(self, analyzer, sample_swf):
        """Test encryption detection"""
        results = analyzer.analyze_swf(sample_swf)
        assert 'security' in results
        security = results['security']
        assert 'encryption_detected' in security
        
    def test_identify_crypto_patterns(self, analyzer, sample_swf):
        """Test cryptographic pattern identification"""
        results = analyzer.analyze_swf(sample_swf)
        security = results['security']
        
        # Check for common patterns
        patterns = security.get('crypto_patterns', [])
        known_patterns = [
            'RC4',
            'AES',
            'XOR',
            'Base64',
            'Custom'
        ]
        
        for pattern in patterns:
            assert pattern in known_patterns
            
    def test_extract_keys(self, analyzer, sample_swf):
        """Test cryptographic key extraction"""
        results = analyzer.analyze_swf(sample_swf)
        security = results['security']
        
        # Check extracted keys
        keys = security.get('extracted_keys', [])
        for key in keys:
            assert isinstance(key, dict)
            assert 'type' in key
            assert 'value' in key
            assert 'location' in key
            
    def test_analyze_string_patterns(self, analyzer, sample_swf):
        """Test string pattern analysis for encrypted content"""
        results = analyzer.analyze_swf(sample_swf)
        security = results['security']
        
        # Check string patterns
        patterns = security.get('string_patterns', [])
        for pattern in patterns:
            assert isinstance(pattern, dict)
            assert 'type' in pattern
            assert 'count' in pattern
            assert 'entropy' in pattern
