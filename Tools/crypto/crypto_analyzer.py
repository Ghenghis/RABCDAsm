import os
import sys
import zlib
import json
import struct
import binascii
import math
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

class EvonyCryptoAnalyzer:
    def __init__(self):
        """Initialize Evony crypto analyzer."""
        self.output_dir = os.path.join("evony_crypto_analysis", 
                                     datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Known encryption patterns
        self.encryption_patterns = {
            b'\x00\x01\x02\x03': 'AES-CBC',
            b'\x41\x45\x53': 'AES-Custom',
            b'\x42\x46\x53': 'Blowfish',
            b'\x52\x43\x34': 'RC4',
            b'\x58\x4F\x52': 'XOR'
        }
        
        # Interesting byte sequences
        self.interesting_sequences = [
            # AES S-box patterns
            bytes.fromhex('637c777bf26b6fc53001672bfed7ab76'),
            # Blowfish P-array pattern
            bytes.fromhex('243f6a8885a308d313198a2e03707344'),
            # Common encryption markers
            b'Salted__',
            b'BEGIN',
            b'END',
            # Base64 padding
            b'==',
            b'='
        ]
        
        # Common key lengths
        self.key_lengths = [16, 24, 32]  # AES-128, AES-192, AES-256
        
    def analyze_binary_data(self, data: bytes) -> Dict[str, Any]:
        """Analyze binary data for encryption artifacts."""
        results = {
            'potential_encryption': [],
            'key_candidates': [],
            'iv_candidates': [],
            'entropy': self.calculate_entropy(data),
            'patterns': []
        }
        
        # Look for encryption patterns
        for pattern, enc_type in self.encryption_patterns.items():
            if pattern in data:
                results['potential_encryption'].append({
                    'type': enc_type,
                    'offset': data.index(pattern),
                    'context': data[max(0, data.index(pattern)-16):
                                  min(len(data), data.index(pattern)+48)].hex()
                })
        
        # Look for interesting sequences
        for seq in self.interesting_sequences:
            if seq in data:
                results['patterns'].append({
                    'sequence': seq.hex(),
                    'offset': data.index(seq),
                    'count': data.count(seq)
                })
        
        # Look for potential keys (high entropy sequences)
        for length in self.key_lengths:
            for i in range(len(data) - length):
                chunk = data[i:i+length]
                entropy = self.calculate_entropy(chunk)
                if entropy > 7.5:  # High entropy threshold
                    results['key_candidates'].append({
                        'offset': i,
                        'length': length,
                        'entropy': entropy,
                        'data': chunk.hex()
                    })
        
        # Look for potential IVs (16 bytes, moderate entropy)
        for i in range(len(data) - 16):
            chunk = data[i:i+16]
            entropy = self.calculate_entropy(chunk)
            if 6.5 < entropy < 7.5:  # Moderate entropy threshold
                results['iv_candidates'].append({
                    'offset': i,
                    'entropy': entropy,
                    'data': chunk.hex()
                })
        
        return results
    
    def calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of byte sequence."""
        if not data:
            return 0.0
        
        counts = defaultdict(int)
        for byte in data:
            counts[byte] += 1
        
        entropy = 0
        for count in counts.values():
            probability = count / len(data)
            entropy -= probability * (math.log2(probability) if probability > 0 else 0)
        
        return entropy
    
    def analyze_abc_tag(self, data: bytes) -> Dict[str, Any]:
        """Analyze ABC tag for encryption-related code."""
        results = {
            'crypto_strings': [],
            'potential_functions': [],
            'interesting_constants': []
        }
        
        # Look for crypto-related strings
        crypto_keywords = [
            b'encrypt', b'decrypt', b'cipher', b'key', b'iv', 
            b'salt', b'hash', b'md5', b'sha1', b'aes', b'des', 
            b'blowfish', b'rc4', b'base64'
        ]
        
        for keyword in crypto_keywords:
            pos = 0
            while True:
                pos = data.find(keyword, pos)
                if pos == -1:
                    break
                    
                # Get surrounding context
                start = max(0, pos - 32)
                end = min(len(data), pos + len(keyword) + 32)
                context = data[start:end]
                
                results['crypto_strings'].append({
                    'keyword': keyword.decode('ascii'),
                    'offset': pos,
                    'context': context.hex()
                })
                pos += 1
        
        # Look for function signatures
        function_patterns = [
            b'function encrypt', b'function decrypt',
            b'function hash', b'function generate'
        ]
        
        for pattern in function_patterns:
            pos = 0
            while True:
                pos = data.find(pattern, pos)
                if pos == -1:
                    break
                    
                # Get function context
                start = max(0, pos - 64)
                end = min(len(data), pos + 256)
                context = data[start:end]
                
                results['potential_functions'].append({
                    'signature': pattern.decode('ascii'),
                    'offset': pos,
                    'context': context.hex()
                })
                pos += 1
        
        # Look for interesting constants
        constant_patterns = [
            # AES S-box first row
            bytes.fromhex('637c777bf26b6fc5'),
            # Common encryption constants
            bytes.fromhex('0123456789abcdef'),
            # Common key schedule constants
            bytes.fromhex('01020408102040801b366cd8ab4d9a2f')
        ]
        
        for pattern in constant_patterns:
            if pattern in data:
                results['interesting_constants'].append({
                    'pattern': pattern.hex(),
                    'offset': data.index(pattern),
                    'context': data[max(0, data.index(pattern)-16):
                                  min(len(data), data.index(pattern)+48)].hex()
                })
        
        return results
    
    def process_swf(self, file_path: str) -> bool:
        """Process a SWF file for crypto analysis."""
        try:
            print(f"\nProcessing: {file_path}")
            
            # Read file
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Check compression
            signature = data[:3].decode('ascii')
            if signature == 'CWS':
                # Decompress
                body = zlib.decompress(data[8:])
                data = data[:8] + body
            elif signature != 'FWS':
                print("Not a valid SWF file")
                return False
            
            # Initialize analysis
            analysis = {
                'file_info': {
                    'path': file_path,
                    'size': len(data),
                    'compressed': signature == 'CWS'
                },
                'encryption_analysis': [],
                'abc_analysis': [],
                'summary': {
                    'potential_encryption_methods': set(),
                    'key_candidates': 0,
                    'crypto_functions': 0,
                    'interesting_constants': 0
                }
            }
            
            # Process ABC tags
            offset = 8
            while offset < len(data):
                # Read tag header
                tag_code_and_length = struct.unpack('<H', data[offset:offset+2])[0]
                tag_code = tag_code_and_length >> 6
                tag_length = tag_code_and_length & 0x3F
                header_size = 2
                
                if tag_length == 0x3F:
                    tag_length = struct.unpack('<I', data[offset+2:offset+6])[0]
                    header_size = 6
                
                # Process DoABC tags
                if tag_code == 82:  # DoABC
                    tag_data = data[offset+header_size:offset+header_size+tag_length]
                    flags = struct.unpack('<I', tag_data[:4])[0]
                    name_end = tag_data.find(b'\x00', 4)
                    name = tag_data[4:name_end].decode('utf-8', 'ignore')
                    abc_data = tag_data[name_end+1:]
                    
                    # Analyze ABC data
                    abc_analysis = self.analyze_abc_tag(abc_data)
                    analysis['abc_analysis'].append({
                        'name': name,
                        'flags': flags,
                        'analysis': abc_analysis
                    })
                    
                    # Update summary
                    analysis['summary']['crypto_functions'] += len(abc_analysis['potential_functions'])
                    analysis['summary']['interesting_constants'] += len(abc_analysis['interesting_constants'])
                
                # Analyze binary data in chunks
                chunk_size = 4096
                for i in range(0, tag_length, chunk_size):
                    chunk = data[offset+header_size+i:
                               min(offset+header_size+i+chunk_size, 
                                   offset+header_size+tag_length)]
                    
                    chunk_analysis = self.analyze_binary_data(chunk)
                    if (chunk_analysis['potential_encryption'] or 
                        chunk_analysis['key_candidates'] or 
                        chunk_analysis['patterns']):
                        
                        analysis['encryption_analysis'].append({
                            'offset': offset + header_size + i,
                            'analysis': chunk_analysis
                        })
                        
                        # Update summary
                        analysis['summary']['potential_encryption_methods'].update(
                            enc['type'] for enc in chunk_analysis['potential_encryption']
                        )
                        analysis['summary']['key_candidates'] += len(chunk_analysis['key_candidates'])
                
                offset += header_size + tag_length
            
            # Convert summary set to list for JSON serialization
            analysis['summary']['potential_encryption_methods'] = list(
                analysis['summary']['potential_encryption_methods']
            )
            
            # Generate report
            report_path = os.path.join(
                self.output_dir,
                f"crypto_analysis_{os.path.basename(file_path)}.json"
            )
            
            with open(report_path, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            # Generate summary
            summary_path = os.path.join(
                self.output_dir,
                f"crypto_summary_{os.path.basename(file_path)}.txt"
            )
            
            with open(summary_path, 'w') as f:
                f.write("Evony Crypto Analysis Summary\n")
                f.write("===========================\n\n")
                
                f.write("1. File Information:\n")
                f.write("-----------------\n")
                f.write(f"Path: {analysis['file_info']['path']}\n")
                f.write(f"Size: {analysis['file_info']['size']:,} bytes\n")
                f.write(f"Compressed: {analysis['file_info']['compressed']}\n\n")
                
                f.write("2. Encryption Methods:\n")
                f.write("-------------------\n")
                for method in analysis['summary']['potential_encryption_methods']:
                    f.write(f"- {method}\n")
                f.write("\n")
                
                f.write("3. Crypto Statistics:\n")
                f.write("-----------------\n")
                f.write(f"Potential Key Candidates: {analysis['summary']['key_candidates']}\n")
                f.write(f"Crypto Functions Found: {analysis['summary']['crypto_functions']}\n")
                f.write(f"Interesting Constants: {analysis['summary']['interesting_constants']}\n\n")
                
                f.write("4. ABC Tag Analysis:\n")
                f.write("-----------------\n")
                for abc in analysis['abc_analysis']:
                    f.write(f"\nABC Tag: {abc['name']}\n")
                    f.write(f"Flags: 0x{abc['flags']:08x}\n")
                    f.write(f"Crypto Strings: {len(abc['analysis']['crypto_strings'])}\n")
                    f.write(f"Potential Functions: {len(abc['analysis']['potential_functions'])}\n")
                    f.write(f"Interesting Constants: {len(abc['analysis']['interesting_constants'])}\n")
                    
                    if abc['analysis']['crypto_strings']:
                        f.write("\nInteresting Crypto Strings:\n")
                        for cs in abc['analysis']['crypto_strings'][:5]:  # Show top 5
                            f.write(f"- {cs['keyword']} at offset 0x{cs['offset']:x}\n")
            
            print(f"\nAnalysis complete!")
            print(f"Full analysis: {report_path}")
            print(f"Summary: {summary_path}")
            return True
            
        except Exception as e:
            print(f"Error processing file: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python evony_crypto_analyzer.py <swf_file>")
        sys.exit(1)
    
    analyzer = EvonyCryptoAnalyzer()
    analyzer.process_swf(sys.argv[1])
