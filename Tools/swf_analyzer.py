import os
from pathlib import Path
import hashlib
from typing import Dict, List, Optional
from datetime import datetime
import json
from math import log2

class SWFAnalyzer:
    """Handles SWF file analysis and resource tracking"""
    
    def __init__(self, rabcdasm):
        self.rabcdasm = rabcdasm
        self.analysis_cache = {}
    
    def analyze_swf(self, swf_path: str) -> Dict:
        """
        Perform comprehensive analysis of a SWF file
        
        Args:
            swf_path: Path to the SWF file
            
        Returns:
            Dictionary containing analysis results
        """
        file_path = Path(swf_path)
        
        # Check if we have a recent cached analysis
        cache_key = f"{file_path}_{self._get_file_hash(swf_path)}"
        if cache_key in self.analysis_cache:
            cached = self.analysis_cache[cache_key]
            if (datetime.now() - cached['timestamp']).total_seconds() < 3600:
                return cached['results']
        
        # Perform fresh analysis
        results = {
            'file_info': self._analyze_file_info(file_path),
            'structure': self._analyze_structure(file_path),
            'resources': self._analyze_resources(file_path),
            'security': self._analyze_security(file_path),
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache results
        self.analysis_cache[cache_key] = {
            'results': results,
            'timestamp': datetime.now()
        }
        
        return results
    
    def _analyze_file_info(self, file_path: Path) -> Dict:
        """Analyze basic file information"""
        return {
            'name': file_path.name,
            'size': file_path.stat().st_size,
            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            'hash': self._get_file_hash(str(file_path))
        }
    
    def _analyze_structure(self, file_path: Path) -> Dict:
        """Analyze SWF file structure"""
        try:
            # Extract ABC files
            abc_files = self.rabcdasm.extract_abc(str(file_path))
            
            structure = {
                'abc_count': len(abc_files),
                'abc_files': [],
                'is_compressed': self._is_compressed(file_path)
            }
            
            # Analyze each ABC file
            for abc_file in abc_files:
                abc_info = self._analyze_abc_file(abc_file)
                structure['abc_files'].append(abc_info)
            
            return structure
            
        except Exception as e:
            return {
                'error': f"Structure analysis failed: {str(e)}",
                'abc_count': 0,
                'abc_files': []
            }
    
    def _analyze_abc_file(self, abc_path: str) -> Dict:
        """Analyze an ABC file"""
        try:
            # Disassemble ABC file
            asm_dir = self.rabcdasm.disassemble_abc(abc_path)
            
            # Analyze disassembled content
            return {
                'path': abc_path,
                'size': os.path.getsize(abc_path),
                'hash': self._get_file_hash(abc_path),
                'classes': self._count_classes(asm_dir),
                'methods': self._count_methods(asm_dir)
            }
            
        except Exception as e:
            return {
                'path': abc_path,
                'error': str(e)
            }
    
    def _analyze_resources(self, file_path: Path) -> List[Dict]:
        """Analyze embedded resources"""
        try:
            # Extract binary resources
            resources = self.rabcdasm.extract_binary_data(str(file_path))
            
            results = []
            for resource in resources:
                resource_info = {
                    'path': resource,
                    'type': self._detect_resource_type(resource),
                    'size': os.path.getsize(resource),
                    'hash': self._get_file_hash(resource)
                }
                results.append(resource_info)
            
            return results
            
        except Exception as e:
            return [{
                'error': f"Resource analysis failed: {str(e)}"
            }]
    
    def _analyze_security(self, file_path: Path) -> Dict:
        """Analyze security aspects"""
        return {
            'file_hash': self._get_file_hash(str(file_path)),
            'signature_status': self._check_signature(file_path),
            'encryption_detected': self._detect_encryption(file_path),
            'potentially_malicious': self._check_malicious_patterns(file_path)
        }
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _is_compressed(self, file_path: Path) -> bool:
        """Check if SWF file is compressed"""
        with open(file_path, 'rb') as f:
            signature = f.read(3)
            return signature in [b'CWS', b'ZWS']
    
    def _count_classes(self, asm_dir: str) -> int:
        """Count number of classes in disassembled code"""
        count = 0
        for root, _, files in os.walk(asm_dir):
            for file in files:
                if file.endswith('.class.asasm'):
                    count += 1
        return count
    
    def _count_methods(self, asm_dir: str) -> int:
        """Count number of methods in disassembled code"""
        count = 0
        for root, _, files in os.walk(asm_dir):
            for file in files:
                if file.endswith('.method.asasm'):
                    count += 1
        return count
    
    def _detect_resource_type(self, resource_path: str) -> str:
        """Detect resource type based on content"""
        with open(resource_path, 'rb') as f:
            header = f.read(8)
            
        # Check common file signatures
        signatures = {
            b'\xFF\xD8\xFF': 'JPEG',
            b'\x89PNG\r\n\x1A\n': 'PNG',
            b'GIF87a': 'GIF',
            b'GIF89a': 'GIF',
            b'ID3': 'MP3',
            b'OggS': 'OGG',
            b'RIFF': 'WAV'
        }
        
        for sig, type_name in signatures.items():
            if header.startswith(sig):
                return type_name
                
        return 'Unknown'
    
    def _check_signature(self, file_path: Path) -> str:
        """Check if SWF file is signed"""
        try:
            with open(file_path, 'rb') as f:
                # Skip signature and version
                f.seek(4)
                # Read file length
                length = int.from_bytes(f.read(4), 'little')
                # Check for signature block
                f.seek(length - 20)
                sig_block = f.read(20)
                return "Signed" if sig_block.startswith(b'SIGN') else "Unsigned"
        except:
            return "Error checking signature"
    
    def _detect_encryption(self, file_path: Path) -> bool:
        """Detect if file contains encrypted content"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                
            # Check for high entropy in content blocks
            block_size = 1024
            high_entropy_blocks = 0
            
            for i in range(0, len(content), block_size):
                block = content[i:i + block_size]
                if self._calculate_entropy(block) > 7.5:
                    high_entropy_blocks += 1
            
            return high_entropy_blocks > len(content) / block_size * 0.3
            
        except:
            return False
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0.0
            
        occurences = [data.count(x) for x in range(256)]
        entropy = 0
        for x in occurences:
            if x:
                p_x = float(x) / len(data)
                entropy -= p_x * (log2(p_x) if p_x > 0 else 0)
        return entropy
    
    def _check_malicious_patterns(self, file_path: Path) -> bool:
        """Check for potentially malicious patterns"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # List of suspicious patterns
            patterns = [
                b'eval(',
                b'Function(',
                b'setTimeout(',
                b'setInterval(',
                b'navigateToURL(',
                b'System.security',
                b'ExternalInterface'
            ]
            
            return any(pattern in content for pattern in patterns)
            
        except:
            return False
