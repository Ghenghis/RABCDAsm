"""
Test suite for ABC file manipulation
Based on tools from RoboTool and J:\evony_1921
"""

import os
import pytest
from pathlib import Path
from tools.lib.rabcdasm_wrapper import RABCDAsmWrapper

class TestABCManipulation:
    @pytest.fixture
    def rabcdasm(self):
        return RABCDAsmWrapper(os.path.join('tools', 'rabcdasm'))
        
    @pytest.fixture
    def sample_swf(self):
        return os.path.join(os.path.dirname(__file__), 'sample_data', 'autoevony.swf')
        
    def test_extract_abc(self, rabcdasm, sample_swf):
        """Test ABC extraction from SWF"""
        abc_files = rabcdasm.extract_abc(sample_swf)
        assert len(abc_files) > 0
        for abc_file in abc_files:
            assert os.path.exists(abc_file)
            assert abc_file.endswith('.abc')
            
    def test_disassemble_abc(self, rabcdasm, sample_swf):
        """Test ABC disassembly"""
        abc_files = rabcdasm.extract_abc(sample_swf)
        for abc_file in abc_files:
            asm_dir = rabcdasm.disassemble_abc(abc_file)
            assert os.path.isdir(asm_dir)
            
            # Check for main assembly file
            main_asm = os.path.join(asm_dir, Path(abc_file).stem + '.main.asasm')
            assert os.path.exists(main_asm)
            
    def test_assemble_abc(self, rabcdasm, sample_swf):
        """Test ABC assembly"""
        abc_files = rabcdasm.extract_abc(sample_swf)
        for abc_file in abc_files:
            # Disassemble
            asm_dir = rabcdasm.disassemble_abc(abc_file)
            main_asm = os.path.join(asm_dir, Path(abc_file).stem + '.main.asasm')
            
            # Assemble back
            new_abc = rabcdasm.assemble_abc(main_asm)
            assert os.path.exists(new_abc)
            assert new_abc.endswith('.abc')
            
    def test_replace_abc(self, rabcdasm, sample_swf):
        """Test ABC replacement in SWF"""
        # Make a copy of test file
        test_swf = os.path.join(os.path.dirname(__file__), 'test_output', 'replace_test.swf')
        os.makedirs(os.path.dirname(test_swf), exist_ok=True)
        with open(sample_swf, 'rb') as src, open(test_swf, 'wb') as dst:
            dst.write(src.read())
            
        # Extract and modify ABC
        abc_files = rabcdasm.extract_abc(test_swf)
        for i, abc_file in enumerate(abc_files):
            # Disassemble
            asm_dir = rabcdasm.disassemble_abc(abc_file)
            main_asm = os.path.join(asm_dir, Path(abc_file).stem + '.main.asasm')
            
            # Modify assembly (add a comment)
            with open(main_asm, 'r') as f:
                content = f.read()
            with open(main_asm, 'w') as f:
                f.write('; Modified for testing\n' + content)
                
            # Reassemble and replace
            new_abc = rabcdasm.assemble_abc(main_asm)
            rabcdasm.replace_abc(test_swf, i, new_abc)
            
        assert os.path.exists(test_swf)
        assert os.path.getsize(test_swf) > 0
        
    def test_decompress_swf(self, rabcdasm, sample_swf):
        """Test SWF decompression"""
        # Make a copy of test file
        test_swf = os.path.join(os.path.dirname(__file__), 'test_output', 'decompress_test.swf')
        os.makedirs(os.path.dirname(test_swf), exist_ok=True)
        with open(sample_swf, 'rb') as src, open(test_swf, 'wb') as dst:
            dst.write(src.read())
            
        decompressed = rabcdasm.decompress_swf(test_swf)
        assert os.path.exists(decompressed)
        assert os.path.getsize(decompressed) > 0
        
    def test_extract_binary_data(self, rabcdasm, sample_swf):
        """Test binary data extraction"""
        bin_files = rabcdasm.extract_binary_data(sample_swf)
        for bin_file in bin_files:
            assert os.path.exists(bin_file)
            assert os.path.getsize(bin_file) > 0
