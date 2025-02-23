import os
import sys
import zlib
import json
import struct
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import subprocess
import re
import base64

class EvonyABCAnalyzer:
    def __init__(self):
        """Initialize Evony ABC analyzer."""
        self.output_dir = os.path.join("evony_abc_analysis", 
                                     datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Interesting patterns
        self.crypto_keywords = [
            b'encrypt', b'decrypt', b'cipher', b'key', b'iv', 
            b'salt', b'hash', b'md5', b'sha1', b'aes', b'des', 
            b'blowfish', b'rc4', b'base64'
        ]
        
        self.function_patterns = [
            b'function encrypt', b'function decrypt',
            b'function hash', b'function generate'
        ]
        
        self.constant_patterns = [
            # AES S-box first row
            bytes.fromhex('637c777bf26b6fc5'),
            # Common encryption constants
            bytes.fromhex('0123456789abcdef'),
            # Common key schedule constants
            bytes.fromhex('01020408102040801b366cd8ab4d9a2f')
        ]
        
        self.deobfuscation_patterns = {
            'string_encryption': [
                r'eval\s*\(',
                r'String\.fromCharCode',
                r'unescape\s*\('
            ],
            'control_flow': [
                r'try\s*{\s*}\s*catch',
                r'while\s*\(\s*true\s*\)',
                r'switch\s*\(\s*[0-9]+\s*\)'
            ],
            'dynamic_loading': [
                r'loadBytes',
                r'loadSWF',
                r'URLRequest'
            ]
        }
        self.setup_rabcdasm()
        
    def setup_rabcdasm(self):
        """Setup RABCDAsm for bytecode manipulation"""
        self.rabcdasm_path = os.path.join(os.path.dirname(__file__), 'bin', 'rabcdasm')
        if not os.path.exists(self.rabcdasm_path):
            os.makedirs(self.rabcdasm_path)
            
    def analyze_doabc2(self, file_path):
        """Analyze DoABC2 tags in SWF file"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Look for DoABC2 tag (tag type = 82)
            tag_type = 82
            pos = 0
            abc_tags = []
            
            while pos < len(content):
                if content[pos] == tag_type:
                    length = int.from_bytes(content[pos+1:pos+3], byteorder='little')
                    abc_tags.append(content[pos+3:pos+3+length])
                    pos += 3 + length
                else:
                    pos += 1
                    
            return abc_tags
        except Exception as e:
            logging.error(f"Error analyzing DoABC2 tags: {str(e)}")
            return []
            
    def decompile_abc(self, abc_data):
        """Decompile ABC bytecode using RABCDAsm"""
        try:
            temp_file = os.path.join(self.rabcdasm_path, 'temp.abc')
            with open(temp_file, 'wb') as f:
                f.write(abc_data)
                
            # Run RABCDAsm
            subprocess.run(['rabcdasm', temp_file], cwd=self.rabcdasm_path)
            
            # Read decompiled output
            asasm_file = temp_file + '.asasm'
            with open(asasm_file, 'r') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error decompiling ABC: {str(e)}")
            return None
    
    def analyze_abc_tag(self, data: bytes) -> Dict[str, Any]:
        """Analyze ABC tag content."""
        results = {
            'crypto_strings': [],
            'potential_functions': [],
            'interesting_constants': [],
            'deobfuscation': []
        }
        
        # Look for crypto-related strings
        for keyword in self.crypto_keywords:
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
        for pattern in self.function_patterns:
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
        for pattern in self.constant_patterns:
            if pattern in data:
                results['interesting_constants'].append({
                    'pattern': pattern.hex(),
                    'offset': data.index(pattern),
                    'context': data[max(0, data.index(pattern)-16):
                                  min(len(data), data.index(pattern)+48)].hex()
                })
        
        # Look for deobfuscation patterns
        for pattern_type, patterns in self.deobfuscation_patterns.items():
            for pattern in patterns:
                if pattern.encode('ascii') in data:
                    results['deobfuscation'].append({
                        'pattern': pattern,
                        'offset': data.index(pattern.encode('ascii')),
                        'context': data[max(0, data.index(pattern.encode('ascii'))-16):
                                      min(len(data), data.index(pattern.encode('ascii'))+48)].hex()
                    })
        
        return results
    
    def process_swf(self, file_path: str) -> bool:
        """Process a SWF file for ABC analysis."""
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
                'abc_analysis': []
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
                    print(f"Found ABC tag at offset {offset}, length {tag_length}")
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
                        'offset': offset,
                        'length': tag_length,
                        'analysis': abc_analysis
                    })
                    
                    # Decompile ABC data
                    decompiled_abc = self.decompile_abc(abc_data)
                    if decompiled_abc:
                        print(f"Decompiled ABC data for {name}:")
                        print(decompiled_abc)
                
                offset += header_size + tag_length
                
                if tag_code == 0:  # End tag
                    break
            
            # Generate summary
            summary_path = os.path.join(
                self.output_dir,
                f"abc_summary_{os.path.basename(file_path)}.txt"
            )
            
            with open(summary_path, 'w') as f:
                f.write("Evony ABC Analysis Summary\n")
                f.write("=========================\n\n")
                
                f.write("1. File Information:\n")
                f.write("-----------------\n")
                f.write(f"Path: {analysis['file_info']['path']}\n")
                f.write(f"Size: {analysis['file_info']['size']:,} bytes\n")
                f.write(f"Compressed: {analysis['file_info']['compressed']}\n\n")
                
                f.write("2. ABC Tags:\n")
                f.write("-----------\n")
                for abc in analysis['abc_analysis']:
                    f.write(f"\nABC Tag: {abc['name']}\n")
                    f.write(f"Offset: 0x{abc['offset']:x}\n")
                    f.write(f"Length: {abc['length']:,} bytes\n")
                    f.write(f"Flags: 0x{abc['flags']:08x}\n")
                    
                    analysis = abc['analysis']
                    f.write(f"Crypto Strings: {len(analysis['crypto_strings'])}\n")
                    f.write(f"Potential Functions: {len(analysis['potential_functions'])}\n")
                    f.write(f"Interesting Constants: {len(analysis['interesting_constants'])}\n")
                    f.write(f"Deobfuscation Patterns: {len(analysis['deobfuscation'])}\n")
                    
                    if analysis['crypto_strings']:
                        f.write("\nInteresting Crypto Strings:\n")
                        for cs in analysis['crypto_strings'][:5]:  # Show top 5
                            f.write(f"- {cs['keyword']} at offset 0x{cs['offset']:x}\n")
                            
                    if analysis['potential_functions']:
                        f.write("\nPotential Crypto Functions:\n")
                        for fn in analysis['potential_functions'][:5]:  # Show top 5
                            f.write(f"- {fn['signature']} at offset 0x{fn['offset']:x}\n")
                            
                    if analysis['interesting_constants']:
                        f.write("\nInteresting Constants:\n")
                        for const in analysis['interesting_constants'][:5]:  # Show top 5
                            f.write(f"- Pattern: {const['pattern']} at offset 0x{const['offset']:x}\n")
                            
                    if analysis['deobfuscation']:
                        f.write("\nDeobfuscation Patterns:\n")
                        for pattern in analysis['deobfuscation'][:5]:  # Show top 5
                            f.write(f"- Pattern: {pattern['pattern']} at offset 0x{pattern['offset']:x}\n")
            
            print(f"\nAnalysis complete!")
            print(f"Summary: {summary_path}")
            return True
            
        except Exception as e:
            print(f"Error processing file: {e}")
            return False

    def analyze_file(self, file_path: str) -> Optional[bytes]:
        """Analyze a file and return decrypted data if successful"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Extract ABC tags
            abc_data = self.extract_abc_tags(data)
            if abc_data:
                # Save extracted ABC
                output_dir = os.path.dirname(file_path)
                abc_path = os.path.join(output_dir, 'extracted_abc.bin')
                with open(abc_path, 'wb') as f:
                    f.write(abc_data)
                
                # Analyze ABC content
                self.analyze_abc_content(abc_data, abc_path + '.analysis')
                return abc_data
            
            return None
        
        except Exception as e:
            logging.error(f"Error analyzing file {file_path}: {str(e)}")
            return None

    def analyze_decrypted_files(self, decrypted_dir, output_dir):
        """Analyze decrypted files and extract ABC content"""
        for filename in os.listdir(decrypted_dir):
            if filename.endswith('.bin'):
                file_path = os.path.join(decrypted_dir, filename)
                
                # Read binary content
                with open(file_path, 'rb') as f:
                    content = f.read()
                    
                # Extract metadata from filename
                parts = filename.replace('.bin', '').split('_')
                if len(parts) >= 4:
                    encryption = parts[1]
                    component = parts[2]
                    operation = parts[3]
                    
                    # Create output path
                    output_path = os.path.join(output_dir, f"{component}_{operation}_abc.bin")
                    
                    try:
                        # Detect ABC tags
                        abc_data = self.extract_abc_tags(content)
                        if abc_data:
                            with open(output_path, 'wb') as f:
                                f.write(abc_data)
                            
                            # Analyze extracted ABC
                            self.analyze_abc_content(abc_data, output_path + '.analysis')
                    except Exception as e:
                        logging.error(f"Error processing {filename}: {str(e)}")

    def extract_abc_tags(self, data):
        """Extract ABC tags from binary data"""
        abc_data = bytearray()
        
        # Look for DoABC tag header
        pos = 0
        while pos < len(data):
            if pos + 2 > len(data):
                break
                
            tag_type = data[pos] & 0x3F
            tag_length = ((data[pos] & 0xC0) << 2) | data[pos + 1]
            
            if tag_type in (72, 82):  # DoABC or DoABC2
                if pos + tag_length <= len(data):
                    abc_data.extend(data[pos:pos + tag_length])
                    
            pos += tag_length + 2
            
        return bytes(abc_data) if abc_data else None

    def analyze_abc_content(self, abc_data, output_path):
        """Analyze ABC content for patterns and deobfuscation"""
        analysis = {
            'metadata': {},
            'strings': [],
            'methods': [],
            'classes': [],
            'namespaces': []
        }
        
        # Parse ABC structure
        try:
            # Extract constant pool
            pos = 4  # Skip version
            
            # Parse integer pool
            int_count = self.read_u30(abc_data, pos)
            pos += self.get_u30_size(int_count)
            pos += int_count * 4
            
            # Parse uint pool
            uint_count = self.read_u30(abc_data, pos)
            pos += self.get_u30_size(uint_count)
            pos += uint_count * 4
            
            # Parse double pool
            double_count = self.read_u30(abc_data, pos)
            pos += self.get_u30_size(double_count)
            pos += double_count * 8
            
            # Parse string pool
            string_count = self.read_u30(abc_data, pos)
            pos += self.get_u30_size(string_count)
            
            strings = []
            for i in range(string_count):
                str_len = self.read_u30(abc_data, pos)
                pos += self.get_u30_size(str_len)
                if str_len > 0:
                    string = abc_data[pos:pos + str_len].decode('utf-8', errors='ignore')
                    strings.append(string)
                    pos += str_len
            
            analysis['strings'] = strings
            
            # Look for obfuscation patterns
            for string in strings:
                if self.is_obfuscated(string):
                    deobfuscated = self.attempt_deobfuscation(string)
                    if deobfuscated:
                        analysis['deobfuscated_strings'].append({
                            'original': string,
                            'deobfuscated': deobfuscated
                        })
        
        except Exception as e:
            logging.error(f"Error analyzing ABC content: {str(e)}")
        
        # Write analysis results
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)

    def is_obfuscated(self, string):
        """Check if a string appears to be obfuscated"""
        # Check for common obfuscation patterns
        patterns = [
            r'^[a-zA-Z0-9]{20,}$',  # Long random strings
            r'^[_$][0-9]+$',        # Numeric variables
            r'eval\(|Function\(',    # Dynamic code execution
            r'String\.fromCharCode'  # Character code conversion
        ]
        
        return any(re.match(pattern, string) for pattern in patterns)

    def attempt_deobfuscation(self, string):
        """Attempt to deobfuscate a string"""
        try:
            # Handle string.fromCharCode sequences
            if 'String.fromCharCode' in string:
                chars = re.findall(r'fromCharCode\((.*?)\)', string)
                if chars:
                    return ''.join(chr(int(c)) for c in chars[0].split(','))
                    
            # Handle hex-encoded strings
            if re.match(r'^[0-9A-Fa-f]+$', string) and len(string) % 2 == 0:
                try:
                    return bytes.fromhex(string).decode('utf-8')
                except:
                    pass
                    
            # Handle base64
            if re.match(r'^[A-Za-z0-9+/=]+$', string):
                try:
                    return base64.b64decode(string).decode('utf-8')
                except:
                    pass
                    
        except Exception:
            pass
            
        return None

    def read_u30(self, data, pos):
        """Read a u30 value from the data"""
        value = 0
        shift = 0
        while True:
            byte = data[pos]
            value |= (byte & 0x7F) << shift
            pos += 1
            if not (byte & 0x80):
                break
            shift += 7
        return value

    def get_u30_size(self, value):
        """Get the size of a u30 value"""
        if value < 0x80:
            return 1
        elif value < 0x4000:
            return 2
        elif value < 0x200000:
            return 3
        else:
            return 4

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python evony_abc_analyzer.py <swf_file>")
        sys.exit(1)
    
    analyzer = EvonyABCAnalyzer()
    analyzer.process_swf(sys.argv[1])
