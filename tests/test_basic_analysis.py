"""
Test suite for basic AI code analysis features
"""

import unittest
from pathlib import Path
import os
import tempfile
import struct

from rabcdasm.ai_analyzer import AICodeAnalyzer

class TestBasicAnalysis(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.analyzer = AICodeAnalyzer()
        
        # Create a temporary test file
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.swf")
        self._create_test_swf()
            
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            
    def _create_test_swf(self):
        """Create a minimal valid SWF file for testing"""
        # Create minimal SWF file with valid header
        # Format: FWS + version + file size + minimal content
        minimal_content = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # 10 bytes of content
        
        # Calculate total file size
        header_size = 8  # FWS (3) + version (1) + size (4)
        total_size = header_size + len(minimal_content)
        
        content = bytearray()
        content.extend(b'FWS')  # Signature
        content.append(8)  # Version
        content.extend(struct.pack('<I', total_size))  # File size
        content.extend(minimal_content)
        
        with open(self.test_file, "wb") as f:
            f.write(content)
    
    def test_basic_pattern_detection(self):
        """Test basic code pattern detection"""
        patterns = self.analyzer.detect_patterns(self.test_file)
        self.assertIsNotNone(patterns)
        self.assertTrue(len(patterns) > 0)
        
        # Verify pattern structure
        for abc_file, abc_patterns in patterns.items():
            self.assertIsInstance(abc_patterns, list)
            if abc_patterns:
                pattern = abc_patterns[0]
                self.assertIsInstance(pattern, dict)
                self.assertIn('type', pattern)
                self.assertIn('location', pattern)
    
    def test_structure_analysis(self):
        """Test code structure analysis"""
        structure = self.analyzer.analyze_structure(self.test_file)
        self.assertIn('abc_blocks', structure)
        self.assertIn('resources', structure)
        
        # Verify structure components
        abc_blocks = structure['abc_blocks']
        self.assertIsInstance(abc_blocks, list)
        
        resources = structure['resources']
        self.assertIsInstance(resources, dict)
        self.assertIn('images', resources)
        self.assertIn('sounds', resources)
        
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            self.analyzer.detect_patterns("nonexistent.swf")
            
        # Test with invalid SWF file
        invalid_file = os.path.join(self.temp_dir, "invalid.swf")
        with open(invalid_file, "wb") as f:
            f.write(b'Invalid content')
            
        with self.assertRaises(ValueError):
            self.analyzer.analyze_structure(invalid_file)

if __name__ == '__main__':
    unittest.main()
