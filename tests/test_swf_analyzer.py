"""
Test suite for SWF analysis functionality
Based on tools from J:\evony_1921\useful_Scripts and RoboTool
"""

import os
import pytest
from pathlib import Path
from tools.lib.swf_analyzer import SWFAnalyzer
from tools.lib.rabcdasm_wrapper import RABCDAsmWrapper

class TestSWFAnalyzer:
    @pytest.fixture
    def analyzer(self):
        rabcdasm = RABCDAsmWrapper(os.path.join('tools', 'rabcdasm'))
        return SWFAnalyzer(rabcdasm)
        
    @pytest.fixture
    def sample_swf(self):
        return os.path.join(os.path.dirname(__file__), 'sample_data', 'autoevony.swf')
        
    def test_analyze_file_info(self, analyzer, sample_swf):
        """Test basic file information analysis"""
        results = analyzer.analyze_swf(sample_swf)
        assert 'file_info' in results
        info = results['file_info']
        assert info['name'] == 'autoevony.swf'
        assert info['size'] > 0
        assert 'hash' in info
        
    def test_analyze_structure(self, analyzer, sample_swf):
        """Test SWF structure analysis"""
        results = analyzer.analyze_swf(sample_swf)
        assert 'structure' in results
        structure = results['structure']
        assert 'abc_count' in structure
        assert 'is_compressed' in structure
        
    def test_analyze_resources(self, analyzer, sample_swf):
        """Test resource extraction and analysis"""
        results = analyzer.analyze_swf(sample_swf)
        assert 'resources' in results
        resources = results['resources']
        assert isinstance(resources, list)
        
    def test_analyze_security(self, analyzer, sample_swf):
        """Test security analysis features"""
        results = analyzer.analyze_swf(sample_swf)
        assert 'security' in results
        security = results['security']
        assert 'file_hash' in security
        assert 'encryption_detected' in security
        
    def test_detect_resource_type(self, analyzer):
        """Test resource type detection"""
        # Create test files with known signatures
        test_files = {
            'jpeg': b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00',
            'png': b'\x89PNG\r\n\x1A\n\x00\x00\x00\x0D',
            'gif': b'GIF89a\x01\x00\x01\x00\x80\x00\x00'
        }
        
        for type_name, content in test_files.items():
            test_path = os.path.join(os.path.dirname(__file__), f'test_output/test.{type_name}')
            os.makedirs(os.path.dirname(test_path), exist_ok=True)
            with open(test_path, 'wb') as f:
                f.write(content)
            detected = analyzer._detect_resource_type(test_path)
            assert detected.upper() == type_name.upper()
            
    def test_cache_behavior(self, analyzer, sample_swf):
        """Test analysis caching"""
        # First analysis
        results1 = analyzer.analyze_swf(sample_swf)
        
        # Should use cache
        results2 = analyzer.analyze_swf(sample_swf)
        
        assert results1 == results2
        
        # Modify file timestamp
        os.utime(sample_swf, None)
        
        # Should perform fresh analysis
        results3 = analyzer.analyze_swf(sample_swf)
        assert results3['timestamp'] != results1['timestamp']
