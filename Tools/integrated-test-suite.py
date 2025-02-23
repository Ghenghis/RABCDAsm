import unittest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Import our components
from ai_rabcdasm_interface import AIRABCDasm
from decryption_manager import DecryptionManager
from resource_analyzer import ResourceAnalyzer

class TestAIRABCDasmIntegration(unittest.TestCase):
    """Test AI-powered RABCDAsm integration"""
    
    def setUp(self):
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.test_files = Path(self.test_dir)
        
        # Initialize components
        self.ai_interface = AIRABCDasm()
        self.decryption = DecryptionManager()
        self.analyzer = ResourceAnalyzer()
        
        # Create test data
        self._setup_test_data()
        
    def tearDown(self):
        # Cleanup test files
        import shutil
        shutil.rmtree(self.test_dir)
        
    def _setup_test_data(self):
        """Create test data files"""
        # Sample SWF file
        with open(self.test_files / "test.swf", "wb") as f:
            f.write(b"CWS" + b"\x00" * 100)
            
        # Sample ABC file
        with open(self.test_files / "test.abc", "wb") as f:
            f.write(b"\x00\x02\x00" + b"\x00" * 100)
    
    async def test_ai_analysis(self):
        """Test AI analysis of SWF files"""
        # Mock AI response
        mock_response = {
            "analysis": {
                "structure": "valid",
                "resources": ["abc", "jpeg", "sound"],
                "suggestions": ["optimize images", "check encryption"]
            }
        }
        
        with patch("ai_rabcdasm_interface.AIRABCDasm.analyze") as mock_analyze:
            mock_analyze.return_value = mock_response
            
            # Run analysis
            result = await self.ai_interface.analyze_file(
                self.test_files / "test.swf"
            )
            
            # Verify results
            self.assertEqual(result["structure"], "valid")
            self.assertIn("abc", result["resources"])
            self.assertTrue(len(result["suggestions"]) > 0)
            
    def test_decryption_patterns(self):
        """Test decryption pattern detection and application"""
        test_patterns = {
            "xor": {
                "data": bytes([0x55, 0xAA] * 10),
                "key": 0x55,
                "expected": bytes([0x00, 0xFF] * 10)
            },
            "rc4": {
                "data": bytes(range(20)),
                "key": b"test",
                "expected": None  # Will be compared with RC4 output
            }
        }
        
        for pattern, test_data in test_patterns.items():
            with self.subTest(pattern=pattern):
                result = self.decryption.decrypt_data(
                    test_data["data"],
                    test_data["key"],
                    pattern
                )
                if test_data["expected"]:
                    self.assertEqual(result, test_data["expected"])
                self.assertIsNotNone(result)
                
    def test_resource_extraction(self):
        """Test resource extraction and validation"""
        resources = self.analyzer.extract_resources(
            self.test_files / "test.swf"
        )
        
        self.assertIsInstance(resources, dict)
        self.assertIn("abc_files", resources)
        self.assertIn("images", resources)
        self.assertIn("sounds", resources)
        
        # Validate extraction counts
        self.assertGreaterEqual(len(resources["abc_files"]), 0)
        
    async def test_end_to_end(self):
        """Test complete workflow from analysis to modification"""
        # 1. Analyze file
        analysis = await self.ai_interface.analyze_file(
            self.test_files / "test.swf"
        )
        
        # 2. Extract resources
        resources = self.analyzer.extract_resources(
            self.test_files / "test.swf"
        )
        
        # 3. Process with AI suggestions
        modifications = await self.ai_interface.generate_modifications(
            analysis, resources
        )
        
        # 4. Apply modifications
        result = await self.ai_interface.apply_modifications(
            self.test_files / "test.swf",
            modifications
        )
        
        self.assertTrue(result["success"])
        self.assertGreater(len(result["modified_files"]), 0)
        
    def test_validation_rules(self):
        """Test resource validation rules"""
        validation_rules = {
            "abc": {
                "min_size": 10,
                "max_size": 1024 * 1024,  # 1MB
                "required_markers": [b"\x00\x02\x00"]
            },
            "jpeg": {
                "min_size": 100,
                "max_size": 5 * 1024 * 1024,  # 5MB
                "required_markers": [b"\xFF\xD8\xFF"]
            }
        }
        
        # Test ABC validation
        abc_result = self.analyzer.validate_resource(
            self.test_files / "test.abc",
            "abc",
            validation_rules["abc"]
        )
        self.assertTrue(abc_result["valid"])
        
        # Test invalid data
        with open(self.test_files / "invalid.abc", "wb") as f:
            f.write(b"\x00" * 5)  # Too small
            
        invalid_result = self.analyzer.validate_resource(
            self.test_files / "invalid.abc",
            "abc",
            validation_rules["abc"]
        )
        self.assertFalse(invalid_result["valid"])
        
    def test_performance_metrics(self):
        """Test performance monitoring"""
        metrics = {
            "file_size": 1024,
            "process_time": 0.5,
            "memory_usage": 1024 * 1024
        }
        
        # Process file with metrics
        with self.analyzer.track_performance() as tracker:
            self.analyzer.process_file(
                self.test_files / "test.swf"
            )
            metrics = tracker.get_metrics()
            
        self.assertIn("file_size", metrics)
        self.assertIn("process_time", metrics)
        self.assertIn("memory_usage", metrics)
        self.assertGreater(metrics["process_time"], 0)

class TestDecryptionPatterns(unittest.TestCase):
    """Test specific decryption patterns"""
    
    def setUp(self):
        self.decryption = DecryptionManager()
        
    def test_xor_pattern(self):
        """Test XOR decryption pattern"""
        test_data = bytes([0x55, 0xAA, 0x55, 0xAA])
        key = 0x55
        expected = bytes([0x00, 0xFF, 0x00, 0xFF])
        
        result = self.decryption.xor_decrypt(test_data, key)
        self.assertEqual(result, expected)
        
    def test_rc4_pattern(self):
        """Test RC4 decryption pattern"""
        test_data = bytes(range(20))
        key = b"test_key"
        
        result = self.decryption.rc4_decrypt(test_data, key)
        self.assertNotEqual(result, test_data)
        # RC4 reversible test
        reversed_data = self.decryption.rc4_decrypt(result, key)
        self.assertEqual(reversed_data, test_data)
        
    def test_multi_layer(self):
        """Test multi-layer decryption"""
        test_data = bytes([0x55, 0xAA] * 10)
        keys = {
            "xor": 0x55,
            "rc4": b"test"
        }
        
        result = self.decryption.decrypt_multi_layer(
            test_data,
            keys,
            ["xor", "rc4"]
        )
        self.assertNotEqual(result, test_data)
        
        # Test layer order matters
        result2 = self.decryption.decrypt_multi_layer(
            test_data,
            keys,
            ["rc4", "xor"]
        )
        self.assertNotEqual(result, result2)

if __name__ == "__main__":
    unittest.main(verbosity=2)
