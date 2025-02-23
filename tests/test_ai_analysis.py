"""
Test suite for AI-powered code analysis features
"""

import unittest
from pathlib import Path
import os
import shutil
from typing import Dict, List

from rabcdasm.tools.ai_analyzer import AICodeAnalyzer
from rabcdasm.tools.rabcdasm_wrapper import RABCDAsmWrapper

class TestAIAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_dir = Path(__file__).parent / "test_files"
        cls.test_dir.mkdir(exist_ok=True)
        
        # Create test SWF file with known content
        cls.test_swf = cls.test_dir / "test.swf"
        cls.create_test_swf()
        
        # Initialize analyzer
        cls.analyzer = AICodeAnalyzer()
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)
            
    @classmethod
    def create_test_swf(cls):
        """Create a test SWF file with known content"""
        # TODO: Create actual test SWF file
        # For now, just create a dummy file
        cls.test_swf.write_bytes(b'FWS\x08\x00\x00\x00\x78\x00\x04\x00')
        
    def test_basic_pattern_detection(self):
        """Test basic code pattern detection"""
        patterns = self.analyzer.detect_patterns(self.test_swf)
        
        # Verify basic structure
        self.assertIsNotNone(patterns)
        self.assertIsInstance(patterns, dict)
        
        # Verify pattern categories
        self.assertIn('crypto', patterns)
        self.assertIn('network', patterns)
        self.assertIn('performance', patterns)
        
        # Verify pattern details
        for category, category_patterns in patterns.items():
            self.assertIsInstance(category_patterns, list)
            if category_patterns:
                pattern = category_patterns[0]
                self.assertIn('name', pattern)
                self.assertIn('confidence', pattern)
                self.assertIn('location', pattern)
                
    def test_structure_analysis(self):
        """Test code structure analysis"""
        structure = self.analyzer.analyze_structure(self.test_swf)
        
        # Verify basic structure components
        self.assertIn('abc_blocks', structure)
        self.assertIn('resources', structure)
        
        # Verify ABC blocks
        abc_blocks = structure['abc_blocks']
        self.assertIsInstance(abc_blocks, list)
        if abc_blocks:
            block = abc_blocks[0]
            self.assertIn('name', block)
            self.assertIn('size', block)
            self.assertIn('classes', block)
            
        # Verify resources
        resources = structure['resources']
        self.assertIn('images', resources)
        self.assertIn('sounds', resources)
        self.assertIn('other', resources)
        
    def test_dependency_analysis(self):
        """Test dependency analysis"""
        deps = self.analyzer.analyze_dependencies(self.test_swf)
        
        # Verify dependency structure
        self.assertIsInstance(deps, dict)
        self.assertIn('internal', deps)
        self.assertIn('external', deps)
        self.assertIn('missing', deps)
        
        # Verify dependency details
        for dep_type, dependencies in deps.items():
            self.assertIsInstance(dependencies, list)
            if dependencies:
                dep = dependencies[0]
                self.assertIn('name', dep)
                self.assertIn('type', dep)
                self.assertIn('used_by', dep)
                
    def test_security_analysis(self):
        """Test security analysis"""
        security = self.analyzer.analyze_security(self.test_swf)
        
        # Verify security analysis structure
        self.assertIsInstance(security, dict)
        self.assertIn('vulnerabilities', security)
        self.assertIn('risk_level', security)
        self.assertIn('recommendations', security)
        
        # Verify vulnerability details
        vulns = security['vulnerabilities']
        self.assertIsInstance(vulns, list)
        if vulns:
            vuln = vulns[0]
            self.assertIn('type', vuln)
            self.assertIn('severity', vuln)
            self.assertIn('location', vuln)
            self.assertIn('description', vuln)
            
    def test_performance_analysis(self):
        """Test performance analysis"""
        perf = self.analyzer.analyze_performance(self.test_swf)
        
        # Verify performance analysis structure
        self.assertIsInstance(perf, dict)
        self.assertIn('bottlenecks', perf)
        self.assertIn('metrics', perf)
        self.assertIn('recommendations', perf)
        
        # Verify bottleneck details
        bottlenecks = perf['bottlenecks']
        self.assertIsInstance(bottlenecks, list)
        if bottlenecks:
            bottleneck = bottlenecks[0]
            self.assertIn('type', bottleneck)
            self.assertIn('severity', bottleneck)
            self.assertIn('location', bottleneck)
            self.assertIn('impact', bottleneck)
            
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            self.analyzer.detect_patterns(self.test_dir / "nonexistent.swf")
            
        # Test with invalid SWF file
        invalid_swf = self.test_dir / "invalid.swf"
        invalid_swf.write_bytes(b'Invalid SWF content')
        with self.assertRaises(ValueError):
            self.analyzer.analyze_structure(invalid_swf)
            
if __name__ == '__main__':
    unittest.main()
