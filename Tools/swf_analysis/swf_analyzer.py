import os
import sys
import zlib
import json
import struct
import binascii
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
import base64
from Crypto.Cipher import AES, Blowfish, DES3
from Crypto.Util.Padding import unpad
import re

@dataclass
class SWFTag:
    code: int
    length: int
    offset: int
    data: bytes

@dataclass
class DoABCTag:
    flags: int
    name: str
    data: bytes

@dataclass
class SymbolClass:
    id: int
    name: str

class EvonySWFAnalyzer:
    def __init__(self):
        """Initialize Evony SWF analyzer."""
        self.output_dir = os.path.join("evony_swf_analysis", 
                                     datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Known tag types
        self.tag_types = {
            0: "End",
            1: "ShowFrame",
            2: "DefineShape",
            4: "PlaceObject",
            5: "RemoveObject",
            6: "DefineBits",
            7: "DefineButton",
            8: "JPEGTables",
            9: "SetBackgroundColor",
            10: "DefineFont",
            11: "DefineText",
            12: "DoAction",
            13: "DefineFontInfo",
            14: "DefineSound",
            15: "StartSound",
            17: "DefineButtonSound",
            18: "SoundStreamHead",
            19: "SoundStreamBlock",
            20: "DefineBitsLossless",
            21: "DefineBitsJPEG2",
            22: "DefineShape2",
            24: "Protect",
            26: "PlaceObject2",
            28: "RemoveObject2",
            32: "DefineShape3",
            33: "DefineText2",
            34: "DefineButton2",
            35: "DefineBitsJPEG3",
            36: "DefineBitsLossless2",
            37: "DefineEditText",
            39: "DefineSprite",
            43: "FrameLabel",
            45: "SoundStreamHead2",
            46: "DefineMorphShape",
            48: "DefineFont2",
            56: "ExportAssets",
            57: "ImportAssets",
            58: "EnableDebugger",
            59: "DoInitAction",
            60: "DefineVideoStream",
            61: "VideoFrame",
            62: "DefineFontInfo2",
            64: "EnableDebugger2",
            65: "ScriptLimits",
            66: "SetTabIndex",
            69: "FileAttributes",
            70: "PlaceObject3",
            71: "ImportAssets2",
            73: "DefineFontAlignZones",
            74: "CSMTextSettings",
            75: "DefineFont3",
            76: "SymbolClass",
            77: "Metadata",
            78: "DefineScalingGrid",
            82: "DoABC",
            83: "DefineShape4",
            84: "DefineMorphShape2",
            86: "DefineSceneAndFrameLabelData",
            87: "DefineBinaryData",
            88: "DefineFontName",
            89: "StartSound2",
            90: "DefineBitsJPEG4",
            91: "DefineFont4"
        }
        
        # Known ABC namespaces
        self.interesting_namespaces = [
            "com.evony",
            "com.umge",
            "flash.crypto",
            "flash.utils",
            "mx.utils",
            "com.adobe"
        ]
        
        # Interesting strings
        self.interesting_strings = [
            "encrypt",
            "decrypt",
            "key",
            "iv",
            "salt",
            "hash",
            "md5",
            "sha1",
            "aes",
            "blowfish",
            "rc4",
            "base64",
            "command",
            "packet",
            "protocol",
            "server",
            "client",
            "resource",
            "config"
        ]
        
        # Tool paths
        self.as3_sorcerer_path = "tools/dev_tools/bin/as3sorcerer/as3sorcerer.jar"
        self.jpexs_path = "tools/dev_tools/bin/ffdec/ffdec.jar"
        self.swftools_path = "tools/dev_tools/bin/swftools"
        
        # Known encryption patterns
        self.encryption_patterns = {
            'aes': [
                rb'AES(?:\.|\[)["\'](?:encrypt|decrypt)["\']',
                rb'Rijndael',
                rb'CryptoJS\.AES'
            ],
            'blowfish': [
                rb'Blowfish(?:\.|\[)["\'](?:encrypt|decrypt)["\']',
                rb'bf_encrypt',
                rb'bf_decrypt'
            ],
            'des': [
                rb'DES(?:\.|\[)["\'](?:encrypt|decrypt)["\']',
                rb'TripleDES',
                rb'3DES'
            ],
            'rc4': [
                rb'RC4(?:\.|\[)["\'](?:encrypt|decrypt)["\']',
                rb'ArcFour',
                rb'rc4_encrypt'
            ]
        }
        
        # Key derivation patterns
        self.key_patterns = [
            rb'(?:var|let|const)\s+(?:key|KEY)\s*=\s*["\']([^"\']+)["\']',
            rb'generateKey\([^)]*\)',
            rb'deriveKey\([^)]*\)',
            rb'getKey\([^)]*\)',
            rb'initKey\([^)]*\)',
            rb'setupKey\([^)]*\)'
        ]
    
    def read_tag_header(self, data: bytes, offset: int) -> Tuple[int, int, int]:
        """Read SWF tag header."""
        tag_code_and_length = struct.unpack('<H', data[offset:offset+2])[0]
        tag_code = tag_code_and_length >> 6
        tag_length = tag_code_and_length & 0x3F
        header_size = 2
        
        if tag_length == 0x3F:
            tag_length = struct.unpack('<I', data[offset+2:offset+6])[0]
            header_size = 6
        
        return tag_code, tag_length, header_size
    
    def read_string(self, data: bytes, offset: int) -> Tuple[str, int]:
        """Read null-terminated string."""
        end = data.find(b'\x00', offset)
        if end == -1:
            return "", len(data)
        return data[offset:end].decode('utf-8', 'ignore'), end + 1
    
    def analyze_do_abc(self, tag_data: bytes) -> Optional[DoABCTag]:
        """Analyze DoABC tag content."""
        try:
            flags = struct.unpack('<I', tag_data[:4])[0]
            name, offset = self.read_string(tag_data, 4)
            abc_data = tag_data[offset:]
            
            return DoABCTag(flags, name, abc_data)
            
        except Exception as e:
            print(f"Error analyzing DoABC: {e}")
            return None
    
    def analyze_symbol_class(self, tag_data: bytes) -> List[SymbolClass]:
        """Analyze SymbolClass tag content."""
        try:
            symbols = []
            count = struct.unpack('<H', tag_data[:2])[0]
            offset = 2
            
            for _ in range(count):
                symbol_id = struct.unpack('<H', tag_data[offset:offset+2])[0]
                offset += 2
                name, new_offset = self.read_string(tag_data, offset)
                offset = new_offset
                symbols.append(SymbolClass(symbol_id, name))
            
            return symbols
            
        except Exception as e:
            print(f"Error analyzing SymbolClass: {e}")
            return []
    
    def analyze_binary_data(self, tag_data: bytes) -> Dict[str, Any]:
        """Analyze DefineBinaryData tag content."""
        try:
            tag_id = struct.unpack('<H', tag_data[:2])[0]
            reserved = struct.unpack('<I', tag_data[2:6])[0]
            data = tag_data[6:]
            
            # Try to detect data type
            data_type = "unknown"
            if data.startswith(b'CWS') or data.startswith(b'FWS'):
                data_type = "swf"
            elif data.startswith(b'\xFF\xD8\xFF'):
                data_type = "jpeg"
            elif data.startswith(b'\x89PNG'):
                data_type = "png"
            elif data.startswith(b'GIF8'):
                data_type = "gif"
            elif data.startswith(b'PK\x03\x04'):
                data_type = "zip"
            elif data.startswith(b'<?xml'):
                data_type = "xml"
            
            return {
                'id': tag_id,
                'reserved': reserved,
                'data_type': data_type,
                'data_length': len(data)
            }
            
        except Exception as e:
            print(f"Error analyzing BinaryData: {e}")
            return {}
    
    def find_interesting_strings(self, data: bytes) -> List[str]:
        """Find interesting strings in binary data."""
        found = []
        current_string = bytearray()
        
        for byte in data:
            if 32 <= byte <= 126:  # ASCII printable
                current_string.append(byte)
            else:
                if len(current_string) >= 4:
                    string = current_string.decode('ascii', 'ignore').lower()
                    if any(pattern in string for pattern in self.interesting_strings):
                        found.append(string)
                current_string = bytearray()
        
        # Check last string
        if len(current_string) >= 4:
            string = current_string.decode('ascii', 'ignore').lower()
            if any(pattern in string for pattern in self.interesting_strings):
                found.append(string)
        
        return list(set(found))  # Remove duplicates
    
    def decompile_as3_sorcerer(self, swf_path: str) -> None:
        """Decompile using AS3 Sorcerer 2020."""
        try:
            output_dir = os.path.join(self.output_dir, "as3sorcerer_out")
            os.makedirs(output_dir, exist_ok=True)
            
            subprocess.run([
                "java", "-jar", self.as3_sorcerer_path,
                "-source", swf_path,
                "-out", output_dir,
                "-advanced",  # Enable advanced deobfuscation
                "-pcode",    # Include bytecode analysis
                "-debug"     # Include debug information
            ])
            print("[+] Successfully decompiled using AS3 Sorcerer")
        except Exception as e:
            print(f"[-] Error decompiling with AS3 Sorcerer: {e}")

    def decompile_jpexs(self, swf_path: str) -> None:
        """Decompile using JPEXS Free Flash Decompiler."""
        try:
            subprocess.run([
                "java", "-jar", self.jpexs_path,
                "-export", "script",
                os.path.join(self.output_dir, "jpexs_out"),
                swf_path
            ])
            print("[+] Successfully decompiled using JPEXS")
        except Exception as e:
            print(f"[-] Error decompiling with JPEXS: {e}")

    def find_encryption_functions(self, code: str) -> List[Dict[str, Any]]:
        """Find potential encryption-related functions."""
        findings = []
        
        for enc_type, patterns in self.encryption_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, code.encode())
                for match in matches:
                    findings.append({
                        'type': enc_type,
                        'offset': match.start(),
                        'match': match.group().decode('utf-8', errors='ignore'),
                        'context': code[max(0, match.start()-50):match.end()+50]
                    })
        
        return findings

    def find_potential_keys(self, code: str) -> List[Dict[str, Any]]:
        """Find potential encryption keys and key derivation functions."""
        findings = []
        
        for pattern in self.key_patterns:
            matches = re.finditer(pattern, code.encode())
            for match in matches:
                findings.append({
                    'offset': match.start(),
                    'match': match.group().decode('utf-8', errors='ignore'),
                    'context': code[max(0, match.start()-50):match.end()+50]
                })
        
        return findings

    def analyze_swf(self, swf_path: str) -> None:
        """Main analysis function."""
        print(f"[*] Analyzing {swf_path}")
        
        # Step 1: Decompile using multiple tools
        print("\n[*] Decompiling SWF file...")
        self.decompile_as3_sorcerer(swf_path)  # Use AS3 Sorcerer first
        self.decompile_jpexs(swf_path)         # Also use JPEXS for comparison
        
        # Step 2: Extract ABC bytecode
        print("\n[*] Extracting ABC bytecode...")
        subprocess.run([
            os.path.join(self.swftools_path, "swfextract"),
            "-a",
            swf_path,
            "-o", 
            os.path.join(self.output_dir, "extracted.abc")
        ])
        
        # Step 3: Search for encryption functions and keys
        print("\n[*] Searching for encryption functions and keys...")
        for decompiler in ["as3sorcerer_out", "jpexs_out"]:
            decompiler_dir = os.path.join(self.output_dir, decompiler)
            if os.path.exists(decompiler_dir):
                for root, _, files in os.walk(decompiler_dir):
                    for file in files:
                        if file.endswith('.as'):
                            with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                                code = f.read()
                                
                            enc_funcs = self.find_encryption_functions(code)
                            if enc_funcs:
                                print(f"\n[+] Found encryption functions in {decompiler}/{file}:")
                                for func in enc_funcs:
                                    print(f"    Type: {func['type']}")
                                    print(f"    Match: {func['match']}")
                                    print(f"    Context: {func['context']}\n")
                            
                            pot_keys = self.find_potential_keys(code)
                            if pot_keys:
                                print(f"\n[+] Found potential keys in {decompiler}/{file}:")
                                for key in pot_keys:
                                    print(f"    Match: {key['match']}")
                                    print(f"    Context: {key['context']}\n")
        
        print("\n[*] Analysis complete. Results saved in:", self.output_dir)

    def process_swf(self, file_path: str) -> bool:
        """Process a SWF file for analysis."""
        try:
            print(f"\nProcessing: {file_path}")
            
            # Read file
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Check compression
            signature = data[:3].decode('ascii')
            version = data[3]
            file_length = struct.unpack('<I', data[4:8])[0]
            
            if signature == 'CWS':
                # Decompress
                body = zlib.decompress(data[8:])
                data = data[:8] + body
            elif signature != 'FWS':
                print("Not a valid SWF file")
                return False
            
            # Process tags
            offset = 8  # Skip signature and length
            
            # Skip header (rectangle, frame rate, frame count)
            rect_bits = data[offset] >> 3
            rect_bytes = ((rect_bits * 4) + 7) // 8 + 1
            offset += rect_bytes + 4
            
            # Initialize analysis data
            analysis = {
                'file_info': {
                    'signature': signature,
                    'version': version,
                    'length': file_length,
                    'compressed': signature == 'CWS'
                },
                'tags': [],
                'abc_tags': [],
                'symbols': [],
                'binary_data': [],
                'interesting_strings': []
            }
            
            # Process each tag
            while offset < len(data):
                tag_code, tag_length, header_size = self.read_tag_header(data, offset)
                tag_data = data[offset+header_size:offset+header_size+tag_length]
                
                tag_info = {
                    'code': tag_code,
                    'name': self.tag_types.get(tag_code, f"Unknown_{tag_code}"),
                    'length': tag_length,
                    'offset': offset
                }
                
                # Special handling for certain tags
                if tag_code == 82:  # DoABC
                    abc_tag = self.analyze_do_abc(tag_data)
                    if abc_tag:
                        analysis['abc_tags'].append({
                            'name': abc_tag.name,
                            'flags': abc_tag.flags,
                            'data_length': len(abc_tag.data)
                        })
                
                elif tag_code == 76:  # SymbolClass
                    symbols = self.analyze_symbol_class(tag_data)
                    analysis['symbols'].extend([
                        {'id': s.id, 'name': s.name}
                        for s in symbols
                    ])
                
                elif tag_code == 87:  # DefineBinaryData
                    binary_info = self.analyze_binary_data(tag_data)
                    if binary_info:
                        analysis['binary_data'].append(binary_info)
                
                # Look for interesting strings
                strings = self.find_interesting_strings(tag_data)
                if strings:
                    tag_info['interesting_strings'] = strings
                    analysis['interesting_strings'].extend(strings)
                
                analysis['tags'].append(tag_info)
                
                offset += header_size + tag_length
                
                if tag_code == 0:  # End tag
                    break
            
            # Remove duplicates from interesting strings
            analysis['interesting_strings'] = list(set(analysis['interesting_strings']))
            
            # Generate report
            report_path = os.path.join(
                self.output_dir,
                f"analysis_{os.path.basename(file_path)}.json"
            )
            
            with open(report_path, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            # Generate summary
            summary_path = os.path.join(
                self.output_dir,
                f"summary_{os.path.basename(file_path)}.txt"
            )
            
            with open(summary_path, 'w') as f:
                f.write("Evony SWF Analysis Summary\n")
                f.write("=========================\n\n")
                
                f.write("1. File Information:\n")
                f.write("-----------------\n")
                f.write(f"Signature: {analysis['file_info']['signature']}\n")
                f.write(f"Version: {analysis['file_info']['version']}\n")
                f.write(f"Length: {analysis['file_info']['length']:,} bytes\n")
                f.write(f"Compressed: {analysis['file_info']['compressed']}\n\n")
                
                f.write("2. Tag Statistics:\n")
                f.write("---------------\n")
                tag_counts = {}
                for tag in analysis['tags']:
                    name = tag['name']
                    if name not in tag_counts:
                        tag_counts[name] = 0
                    tag_counts[name] += 1
                
                for name, count in sorted(tag_counts.items()):
                    f.write(f"{name}: {count}\n")
                f.write("\n")
                
                f.write("3. ABC Tags:\n")
                f.write("---------\n")
                for abc in analysis['abc_tags']:
                    f.write(f"Name: {abc['name']}\n")
                    f.write(f"Flags: 0x{abc['flags']:08x}\n")
                    f.write(f"Data Length: {abc['data_length']:,} bytes\n\n")
                
                f.write("4. Symbol Classes:\n")
                f.write("---------------\n")
                for symbol in analysis['symbols']:
                    f.write(f"ID {symbol['id']}: {symbol['name']}\n")
                f.write("\n")
                
                f.write("5. Binary Data:\n")
                f.write("------------\n")
                for binary in analysis['binary_data']:
                    f.write(f"ID {binary['id']}:\n")
                    f.write(f"  Type: {binary['data_type']}\n")
                    f.write(f"  Length: {binary['data_length']:,} bytes\n\n")
                
                f.write("6. Interesting Strings:\n")
                f.write("-------------------\n")
                for string in sorted(analysis['interesting_strings']):
                    f.write(f"{string}\n")
            
            print(f"\nAnalysis complete!")
            print(f"Full analysis: {report_path}")
            print(f"Summary: {summary_path}")
            return True
            
        except Exception as e:
            print(f"Error processing file: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python evony_swf_analyzer.py <swf_file>")
        sys.exit(1)
    
    analyzer = EvonySWFAnalyzer()
    analyzer.analyze_swf(sys.argv[1])
