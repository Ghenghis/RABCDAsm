"""
Test suite for AI-powered debugging features
"""

import unittest
from pathlib import Path
import os
import tempfile
import struct

from rabcdasm.ai_debugger import AIDebugger

class TestDebugFeatures(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.debugger = AIDebugger()
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.abc")
        self._create_test_abc()
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            
    def _create_test_abc(self):
        """Create test ABC file with known issues"""
        # Create ABC file with intentional errors
        content = (
            # Invalid method body
            b'\x00\x10\x00\x00'  # Invalid header
            b'\x00\x00\x00\x01'  # One method
            b'\xFF\xFF\xFF\xFF'  # Invalid method index
        )
        with open(self.test_file, "wb") as f:
            f.write(content)
            
    def test_error_pattern_detection(self):
        """Test detection of error patterns in ABC code"""
        errors = self.debugger.detect_errors(self.test_file)
        
        # Verify error list structure
        self.assertIsInstance(errors, list)
        self.assertTrue(len(errors) > 0)
        
        # Verify error details
        error = errors[0]
        self.assertIn('type', error)
        self.assertIn('severity', error)
        self.assertIn('location', error)
        self.assertIn('description', error)
        
        # Verify error types
        error_types = {e['type'] for e in errors}
        self.assertTrue(error_types.intersection({
            'invalid_method',
            'invalid_header',
            'corrupted_data'
        }))
        
    def test_fix_suggestion(self):
        """Test generation of fix suggestions"""
        error = {
            'type': 'invalid_method',
            'severity': 'high',
            'location': {'offset': 8},
            'description': 'Invalid method index in ABC file'
        }
        
        fixes = self.debugger.suggest_fixes(error)
        
        # Verify fix list structure
        self.assertIsInstance(fixes, list)
        self.assertTrue(len(fixes) > 0)
        
        # Verify fix details
        fix = fixes[0]
        self.assertIn('description', fix)
        self.assertIn('action', fix)
        self.assertIn('confidence', fix)
        
    def test_error_analysis(self):
        """Test detailed error analysis"""
        analysis = self.debugger.analyze_errors(self.test_file)
        
        # Verify analysis structure
        self.assertIn('error_count', analysis)
        self.assertIn('severity_summary', analysis)
        self.assertIn('fix_suggestions', analysis)
        
        # Verify severity summary
        severity = analysis['severity_summary']
        self.assertIn('high', severity)
        self.assertIn('medium', severity)
        self.assertIn('low', severity)
        
    def test_error_categorization(self):
        """Test error categorization by type"""
        categories = self.debugger.categorize_errors(self.test_file)
        
        # Verify category structure
        self.assertIn('syntax', categories)
        self.assertIn('semantic', categories)
        self.assertIn('runtime', categories)
        
        # Verify category details
        for category, errors in categories.items():
            self.assertIsInstance(errors, list)
            if errors:
                error = errors[0]
                self.assertIn('type', error)
                self.assertIn('count', error)
                
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            self.debugger.detect_errors("nonexistent.abc")
            
        # Test with invalid ABC file
        invalid_file = os.path.join(self.temp_dir, "invalid.abc")
        with open(invalid_file, "wb") as f:
            f.write(b'Invalid content')
            
        with self.assertRaises(ValueError):
            self.debugger.analyze_errors(invalid_file)

if __name__ == '__main__':
    unittest.main()
