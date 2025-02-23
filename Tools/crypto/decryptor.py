import os
import json
import zlib
import hashlib
import math
import re
from typing import Dict, List, Any, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
from Crypto.Cipher import AES, Blowfish, DES, DES3, ARC4, CAST
from Crypto.Hash import MD5, SHA1, SHA256
from Crypto.Util.Padding import unpad
from Crypto.Protocol.KDF import PBKDF2
import hmac
import subprocess
from decrypt_tracker import DecryptionTracker, DecryptionResult
from swf_handler import SWFHandler, SWFResource, SWFClass
from network_analyzer import NetworkAnalyzer, NetworkCommand
from crypto_patterns import CryptoPatternMatcher

@dataclass
class EvonyPattern:
    name: str
    signature: bytes
    description: str
    example_data: bytes = None
    frequency: int = 0
    success_rate: float = 0.0

class EvonyDecryptor:
    def __init__(self):
        self.tracker = DecryptionTracker()
        self.swf_handler = SWFHandler()
        self.network_analyzer = NetworkAnalyzer()
        self.pattern_matcher = CryptoPatternMatcher()
        self.base_dir = "evony_analysis"
        
        # Create directories
        self.dirs = {
            'swf': os.path.join(self.base_dir, 'swf'),
            'resources': os.path.join(self.base_dir, 'resources'),
            'network': os.path.join(self.base_dir, 'network'),
            'reports': os.path.join(self.base_dir, 'reports'),
            'decompiled': os.path.join(self.base_dir, 'decompiled'),
            'extracted': os.path.join(self.base_dir, 'extracted')
        }
        
        for dir_path in self.dirs.values():
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
        # Initialize Evony-specific patterns
        self.evony_patterns = {
            # Network Protocols (from NETWORK_SYSTEMS.md)
            'login': EvonyPattern(
                "Login Protocol",
                b'LOGIN_',
                "Login and authentication protocol using AES-CBC",
            ),
            'resource': EvonyPattern(
                "Resource Protocol",
                b'RESOURCE_',
                "Resource loading using custom encryption",
            ),
            'combat': EvonyPattern(
                "Combat Protocol",
                b'COMBAT_',
                "Combat system using Blowfish encryption",
            ),
            'market': EvonyPattern(
                "Market Protocol",
                b'MARKET_',
                "Trading system using AES-CBC",
            ),
            
            # Resource Types (from SETUP_DEPLOYMENT.md)
            'ui_resource': EvonyPattern(
                "UI Resource",
                b'ui/fla/',
                "User interface resources in SWF format",
            ),
            'map_resource': EvonyPattern(
                "Map Resource",
                b'map/tiles/',
                "Map and terrain data with custom compression",
            ),
            'item_resource': EvonyPattern(
                "Item Resource",
                b'items/data/',
                "Item and inventory data using Blowfish",
            ),
            
            # Encryption Methods (from SECURITY_SYSTEM.md)
            'evony_aes': EvonyPattern(
                "Evony AES",
                b'EVON',
                "AES-CBC with HMAC-SHA256 key derivation",
            ),
            'evony_bf': EvonyPattern(
                "Evony Blowfish",
                b'EVBF',
                "Blowfish-CBC for configuration data",
            ),
            'evony_xor': EvonyPattern(
                "Evony XOR",
                b'EVXR',
                "Multi-byte XOR for basic obfuscation",
            ),
            
            # SWF Patterns (from SETUP_DEPLOYMENT.md)
            'swf_embed': EvonyPattern(
                "SWF Embed",
                b'[Embed(',
                "Embedded SWF resource",
            ),
            'swf_import': EvonyPattern(
                "SWF Import",
                b'importClass',
                "Imported ActionScript class",
            ),
            'swf_resource': EvonyPattern(
                "SWF Resource",
                b'Class_',
                "Compiled ActionScript resource",
            )
        }
        
        # Known Evony keys (from SECURITY_SYSTEM.md)
        self.evony_keys = {
            'client': b'EvonyAge2012',  # Main client key
            'resource': b'ResourceData', # Resource decryption
            'network': b'NetworkComm',   # Network protocol
            'combat': b'CombatSystem',   # Combat system
            'market': b'MarketTrade',    # Market system
            'ui': b'UserInterface'       # UI resources
        }
        
        # Initialize statistics
        self.stats = {
            'patterns_found': {},
            'decryption_success': {},
            'resource_types': {},
            'network_commands': set()
        }
    
    def analyze_pattern(self, data: bytes) -> List[EvonyPattern]:
        """Analyze data for encryption patterns."""
        patterns = []
        
        # Use pattern matcher
        analysis = self.pattern_matcher.analyze_encryption(data)
        
        # Convert matched patterns to EvonyPattern format
        for pattern in analysis['patterns_found']:
            patterns.append(EvonyPattern(
                name=pattern['name'],
                signature=bytes.fromhex(pattern['offset'].to_bytes(4, 'big').hex()),
                key_length=pattern['key_length'],
                iv_length=pattern['iv_length'] if 'iv_length' in pattern else None,
                description=pattern['description']
            ))
        
        # Track statistics
        for pattern in patterns:
            if pattern.name not in self.stats['patterns_found']:
                self.stats['patterns_found'][pattern.name] = 0
            self.stats['patterns_found'][pattern.name] += 1
        
        return patterns
    
    def decrypt_evony_data(self, data: bytes, patterns: List[EvonyPattern]) -> Tuple[bytes, str]:
        """Decrypt Evony data using detected patterns."""
        try:
            # Get key recommendations
            analysis = self.pattern_matcher.analyze_encryption(data)
            recommended_keys = {
                rec['pattern']: bytes.fromhex(rec['key'])
                for rec in analysis['key_recommendations']
            }
            
            for pattern in patterns:
                try:
                    # Check if we have a recommended key
                    if pattern.name in recommended_keys:
                        key = recommended_keys[pattern.name]
                    else:
                        # Try to derive key
                        salt = None
                        if pattern.name.startswith('aes_') or pattern.name == 'evony_aes':
                            # Look for salt marker
                            salt_marker = b'\x53\x61\x6C\x74' if 'aes_' in pattern.name else b'\x45\x56\x53\x4C'
                            salt_pos = data.find(salt_marker)
                            if salt_pos >= 0:
                                salt = data[salt_pos+4:salt_pos+12]
                        
                        key, iv = self._derive_key_iv(salt, pattern)
                    
                    # Decrypt based on pattern
                    if pattern.name.startswith('aes_') or pattern.name == 'evony_aes':
                        from Crypto.Cipher import AES
                        from Crypto.Util.Padding import unpad
                        
                        cipher = AES.new(key, AES.MODE_CBC, iv)
                        decrypted = unpad(cipher.decrypt(data), AES.block_size)
                        return decrypted, pattern.name
                        
                    elif pattern.name.startswith('bf_') or pattern.name == 'evony_bf':
                        from Crypto.Cipher import Blowfish
                        from Crypto.Util.Padding import unpad
                        
                        cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
                        decrypted = unpad(cipher.decrypt(data), Blowfish.block_size)
                        return decrypted, pattern.name
                        
                    elif pattern.name == 'rc4_raw':
                        from Crypto.Cipher import ARC4
                        
                        cipher = ARC4.new(key)
                        decrypted = cipher.decrypt(data)
                        return decrypted, pattern.name
                        
                    elif pattern.name.startswith('xor_') or pattern.name == 'evony_xor':
                        # Simple XOR with key
                        key_bytes = key[:4]  # Use first 4 bytes
                        decrypted = bytes(b ^ key_bytes[i % 4] for i, b in enumerate(data))
                        return decrypted, pattern.name
                
                except Exception as e:
                    print(f"Failed to decrypt with {pattern.name}: {e}")
                    continue
            
            return data, "unknown"
            
        except Exception as e:
            print(f"Error decrypting data: {e}")
            return data, "error"
    
    def analyze_network_command(self, data: bytes) -> Dict[str, Any]:
        """Analyze network command structure."""
        try:
            # Use network analyzer
            command = self.network_analyzer.analyze_packet(data)
            if not command:
                return {'type': 'unknown', 'error': 'Failed to parse command'}
            
            # Track command
            self.stats['network_commands'].add(command.name)
            
            # Try to decrypt if encrypted
            if command.encrypted:
                patterns = self.analyze_pattern(command.raw_data)
                if patterns:
                    decrypted, method = self.decrypt_evony_data(command.raw_data, patterns)
                    if method != "unknown":
                        # Update command with decrypted data
                        try:
                            # Try to parse as JSON
                            json_start = decrypted.find(b'{')
                            if json_start >= 0:
                                json_data = decrypted[json_start:].decode('utf-8')
                                command.parameters = json.loads(json_data)
                        except:
                            pass
            
            return {
                'type': command.name,
                'command_id': command.command_id,
                'parameters': command.parameters,
                'encrypted': command.encrypted
            }
            
        except Exception as e:
            print(f"Error analyzing network command: {e}")
            return {'type': 'error', 'error': str(e)}
    
    def process_swf(self, swf_path: str) -> bool:
        """Process a SWF file for decryption and analysis."""
        try:
            print(f"\nProcessing SWF: {swf_path}")
            
            # Create backup
            backup_path = self.tracker.create_backup(swf_path)
            if not backup_path:
                return False
            
            # Create output directories
            decompiled_dir = os.path.join(self.dirs['decompiled'], 
                                        os.path.basename(swf_path))
            extracted_dir = os.path.join(self.dirs['extracted'], 
                                       os.path.basename(swf_path))
            
            for dir_path in [decompiled_dir, extracted_dir]:
                os.makedirs(dir_path, exist_ok=True)
            
            # Step 1: Analyze SWF structure
            print("Analyzing SWF structure...")
            analysis = self.swf_handler.analyze_swf(swf_path, decompiled_dir)
            if not analysis:
                print("Failed to analyze SWF!")
                return False
            
            # Step 2: Extract resources
            print("Extracting resources...")
            resources = self.swf_handler.extract_resources(swf_path, extracted_dir)
            
            # Track resource statistics
            resource_stats = {
                'total': len(resources),
                'encrypted': 0,
                'decrypted': 0,
                'by_type': {},
                'patterns': {}
            }
            
            # Step 3: Process each resource
            for resource in resources:
                print(f"Processing resource: {resource.name}")
                
                # Track resource type
                if resource.type not in resource_stats['by_type']:
                    resource_stats['by_type'][resource.type] = {
                        'total': 0,
                        'encrypted': 0,
                        'decrypted': 0
                    }
                resource_stats['by_type'][resource.type]['total'] += 1
                
                # Analyze patterns
                patterns = self.analyze_pattern(resource.data)
                
                if patterns:
                    resource_stats['encrypted'] += 1
                    resource_stats['by_type'][resource.type]['encrypted'] += 1
                    
                    # Track pattern types
                    for pattern in patterns:
                        if pattern.name not in resource_stats['patterns']:
                            resource_stats['patterns'][pattern.name] = {
                                'count': 0,
                                'successful_decryptions': 0
                            }
                        resource_stats['patterns'][pattern.name]['count'] += 1
                    
                    # Try Evony-specific decryption
                    decrypted, method = self.decrypt_evony_data(resource.data, patterns)
                    
                    if method != "unknown":
                        resource_stats['decrypted'] += 1
                        resource_stats['by_type'][resource.type]['decrypted'] += 1
                        resource_stats['patterns'][method]['successful_decryptions'] += 1
                        
                        # Save decrypted resource
                        output_path = os.path.join(extracted_dir, 
                                                 f"decrypted_{resource.name}")
                        with open(output_path, 'wb') as f:
                            f.write(decrypted)
                        
                        # Track success
                        result = DecryptionResult(
                            file_path=output_path,
                            encryption_type=method,
                            success=True,
                            size_before=len(resource.data),
                            size_after=len(decrypted),
                            timestamp=datetime.now().isoformat(),
                            hash_before=hashlib.sha256(resource.data).hexdigest(),
                            hash_after=hashlib.sha256(decrypted).hexdigest(),
                            additional_info={
                                'resource_type': resource.type,
                                'patterns_found': [p.name for p in patterns]
                            }
                        )
                        self.tracker.track_decryption(result)
            
            # Step 4: Process ActionScript classes
            print("Processing ActionScript classes...")
            classes = self.swf_handler.extract_classes(decompiled_dir)
            
            class_stats = {
                'total': len(classes),
                'with_encryption': 0,
                'encryption_methods': set()
            }
            
            for cls in classes:
                # Look for encryption-related code
                if cls.source:
                    with open(cls.source, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Look for encryption patterns in source
                        encryption_found = False
                        for pattern in self.evony_patterns.values():
                            if pattern.signature.decode() in content:
                                encryption_found = True
                                class_stats['encryption_methods'].add(pattern.name)
                        
                        if encryption_found:
                            class_stats['with_encryption'] += 1
                            print(f"Found encryption code in: {cls.name}")
                            
                            # Save for analysis
                            analysis_path = os.path.join(
                                self.dirs['reports'],
                                f"encryption_class_{cls.name}.txt"
                            )
                            with open(analysis_path, 'w') as f:
                                f.write(f"Class: {cls.name}\n")
                                f.write(f"Superclass: {cls.super_class}\n")
                                f.write("\nMethods:\n")
                                for method in cls.methods:
                                    f.write(f"- {method}\n")
                                f.write("\nProperties:\n")
                                for prop in cls.properties:
                                    f.write(f"- {prop}\n")
                                f.write("\nSource:\n")
                                f.write(content)
            
            # Step 5: Generate detailed report
            print("Generating report...")
            report_path = os.path.join(
                self.dirs['reports'],
                f"swf_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            with open(report_path, 'w') as f:
                f.write("Evony SWF Analysis Report\n")
                f.write("=======================\n\n")
                
                f.write("1. File Information:\n")
                f.write("-----------------\n")
                f.write(f"Path: {swf_path}\n")
                f.write(f"Size: {analysis['file_info']['size']:,} bytes\n\n")
                
                f.write("2. Resource Analysis:\n")
                f.write("------------------\n")
                f.write(f"Total Resources: {resource_stats['total']}\n")
                f.write(f"Encrypted Resources: {resource_stats['encrypted']}\n")
                f.write(f"Successfully Decrypted: {resource_stats['decrypted']}\n\n")
                
                f.write("By Resource Type:\n")
                for res_type, stats in resource_stats['by_type'].items():
                    f.write(f"\n{res_type}:\n")
                    f.write(f"  Total: {stats['total']}\n")
                    f.write(f"  Encrypted: {stats['encrypted']}\n")
                    f.write(f"  Decrypted: {stats['decrypted']}\n")
                
                f.write("\n3. Encryption Patterns:\n")
                f.write("--------------------\n")
                for pattern, stats in resource_stats['patterns'].items():
                    f.write(f"\n{pattern}:\n")
                    f.write(f"  Found: {stats['count']} times\n")
                    f.write(f"  Successful Decryptions: {stats['successful_decryptions']}\n")
                    if stats['count'] > 0:
                        success_rate = (stats['successful_decryptions'] / stats['count']) * 100
                        f.write(f"  Success Rate: {success_rate:.1f}%\n")
                
                f.write("\n4. ActionScript Analysis:\n")
                f.write("----------------------\n")
                f.write(f"Total Classes: {class_stats['total']}\n")
                f.write(f"Classes with Encryption: {class_stats['with_encryption']}\n")
                f.write("\nEncryption Methods Found:\n")
                for method in sorted(class_stats['encryption_methods']):
                    f.write(f"- {method}\n")
                
                f.write("\n5. Dependencies and Imports:\n")
                f.write("-------------------------\n")
                f.write("\nDependencies:\n")
                for dep in analysis['dependencies']:
                    f.write(f"- {dep}\n")
                
                f.write("\nImports:\n")
                for imp in analysis['imports']:
                    f.write(f"- {imp}\n")
            
            # Commit batch
            self.tracker.commit_batch()
            
            print(f"\nAnalysis complete! Check {report_path} for details")
            return True
            
        except Exception as e:
            print(f"Error processing SWF: {e}")
            return False
    
    def process_file(self, file_path: str):
        """Process a file for decryption and analysis."""
        try:
            # Determine file type
            if file_path.endswith('.swf'):
                return self.process_swf(file_path)
            elif file_path.endswith('.pcap') or file_path.endswith('.cap'):
                return self.process_network_data(file_path)
            
            # Create backup
            backup_path = self.tracker.create_backup(file_path)
            if not backup_path:
                return False
            
            # Read file
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Calculate hash before
            hash_before = hashlib.sha256(data).hexdigest()
            size_before = len(data)
            
            # Analyze patterns
            patterns = self.analyze_pattern(data)
            
            # Try Evony-specific decryption first
            decrypted, method = self.decrypt_evony_data(data, patterns)
            
            if method == "unknown":
                # Try generic decryption methods
                decrypted, method = self.decrypt_data(data)
            
            # Calculate hash after
            hash_after = hashlib.sha256(decrypted).hexdigest()
            size_after = len(decrypted)
            
            # Analyze result
            success = hash_after != hash_before and self._is_valid_data(decrypted)
            
            # Track result
            result = DecryptionResult(
                file_path=file_path,
                encryption_type=method,
                success=success,
                size_before=size_before,
                size_after=size_after,
                timestamp=datetime.now().isoformat(),
                hash_before=hash_before,
                hash_after=hash_after,
                additional_info={
                    'patterns_found': [p.name for p in patterns],
                    'valid_data': self._is_valid_data(decrypted)
                }
            )
            
            self.tracker.track_decryption(result)
            
            # Save decrypted data if successful
            if success:
                output_path = os.path.join(self.dirs['resources'], 
                                         f"decrypted_{os.path.basename(file_path)}")
                with open(output_path, 'wb') as f:
                    f.write(decrypted)
                
                # Update statistics
                if method not in self.stats['decryption_success']:
                    self.stats['decryption_success'][method] = 0
                self.stats['decryption_success'][method] += 1
            
            return success
            
        except Exception as e:
            print(f"Error processing file: {e}")
            return False
    
    def process_network_data(self, data_path: str) -> bool:
        """Process network capture data."""
        try:
            print(f"\nProcessing network data: {data_path}")
            
            # Create output directory
            network_dir = os.path.join(self.dirs['network'], 
                                     os.path.basename(data_path))
            os.makedirs(network_dir, exist_ok=True)
            
            # Read and parse commands
            commands = []
            with open(data_path, 'rb') as f:
                data = f.read()
                
                # Look for command boundaries
                offset = 0
                while offset < len(data):
                    # Look for command header
                    header_match = re.search(
                        self.network_analyzer.command_patterns['header'],
                        data[offset:]
                    )
                    if not header_match:
                        break
                    
                    # Get command length
                    length_match = re.search(
                        self.network_analyzer.command_patterns['length'],
                        data[offset:]
                    )
                    if not length_match:
                        offset += 1
                        continue
                    
                    length = struct.unpack('>I', length_match.group(1))[0]
                    command_data = data[offset:offset + length]
                    
                    # Analyze command
                    command = self.network_analyzer.analyze_packet(command_data)
                    if command:
                        commands.append(command)
                    
                    offset += length
            
            if not commands:
                print("No valid commands found!")
                return False
            
            # Analyze protocol patterns
            analysis = self.network_analyzer.analyze_protocol(commands)
            if not analysis:
                print("Failed to analyze protocol!")
                return False
            
            # Generate report
            report_path = os.path.join(
                network_dir,
                f"network_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            self.network_analyzer.generate_report(analysis, report_path)
            
            # Save decrypted commands
            decrypted_dir = os.path.join(network_dir, 'decrypted_commands')
            os.makedirs(decrypted_dir, exist_ok=True)
            
            for i, command in enumerate(commands):
                if command.encrypted:
                    patterns = self.analyze_pattern(command.raw_data)
                    if patterns:
                        decrypted, method = self.decrypt_evony_data(
                            command.raw_data, patterns)
                        
                        if method != "unknown":
                            # Save decrypted command
                            output_path = os.path.join(
                                decrypted_dir,
                                f"command_{i}_{command.name}.bin"
                            )
                            with open(output_path, 'wb') as f:
                                f.write(decrypted)
                            
                            # Track success
                            result = DecryptionResult(
                                file_path=output_path,
                                encryption_type=method,
                                success=True,
                                size_before=len(command.raw_data),
                                size_after=len(decrypted),
                                timestamp=command.timestamp,
                                hash_before=hashlib.sha256(command.raw_data).hexdigest(),
                                hash_after=hashlib.sha256(decrypted).hexdigest(),
                                additional_info={
                                    'command_name': command.name,
                                    'command_id': command.command_id,
                                    'patterns_found': [p.name for p in patterns]
                                }
                            )
                            self.tracker.track_decryption(result)
            
            # Commit batch
            self.tracker.commit_batch()
            
            print(f"\nNetwork analysis complete! Check {report_path} for details")
            return True
            
        except Exception as e:
            print(f"Error processing network data: {e}")
            return False
    
    def generate_detailed_report(self) -> str:
        """Generate detailed analysis report."""
        try:
            report_path = os.path.join(self.dirs['reports'], 
                                     f"detailed_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            
            with open(report_path, 'w') as f:
                f.write("Evony Client Analysis Report\n")
                f.write("===========================\n\n")
                
                # Pattern Analysis
                f.write("Pattern Analysis:\n")
                f.write("-----------------\n")
                for pattern_name, count in self.stats['patterns_found'].items():
                    pattern = self.evony_patterns.get(pattern_name)
                    if pattern:
                        f.write(f"\n{pattern.name}:\n")
                        f.write(f"  Description: {pattern.description}\n")
                        f.write(f"  Frequency: {pattern.frequency}\n")
                        f.write(f"  Success Rate: {pattern.success_rate:.2%}\n")
                        if pattern.example_data:
                            f.write(f"  Example: {pattern.example_data.hex()[:32]}...\n")
                
                # Decryption Success
                f.write("\nDecryption Success Rates:\n")
                f.write("------------------------\n")
                total_decryptions = sum(self.stats['decryption_success'].values())
                for method, count in self.stats['decryption_success'].items():
                    f.write(f"{method}: {count} ({count/total_decryptions:.2%})\n")
                
                # Network Commands
                f.write("\nNetwork Commands Found:\n")
                f.write("---------------------\n")
                for command in sorted(self.stats['network_commands']):
                    f.write(f"- {command}\n")
                
                # Include tracker report
                f.write("\nOverall Progress:\n")
                f.write("----------------\n")
                tracker_report = self.tracker.generate_report()
                if os.path.exists(tracker_report):
                    with open(tracker_report, 'r') as tr:
                        f.write(tr.read())
            
            return report_path
            
        except Exception as e:
            print(f"Error generating detailed report: {e}")
            return ""
    
    def process_directory(self, dir_path: str):
        """Process all files in a directory."""
        try:
            for root, _, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    print(f"\nProcessing: {file}")
                    
                    if file.endswith('.swf'):
                        self.process_swf(file_path)
                    elif file.endswith('.pcap') or file.endswith('.cap'):
                        self.process_network_data(file_path)
                    else:
                        self.process_file(file_path)
            
            # Commit batch and generate report
            self.tracker.commit_batch()
            report_path = self.generate_detailed_report()
            
            print(f"\nAnalysis complete! Check {report_path} for detailed results")
            
        except Exception as e:
            print(f"Error processing directory: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python evony_decryptor.py <path_to_file_or_directory>")
        sys.exit(1)
    
    decryptor = EvonyDecryptor()
    path = sys.argv[1]
    
    if os.path.isfile(path):
        if path.endswith('.swf'):
            decryptor.process_swf(path)
        elif path.endswith('.pcap') or path.endswith('.cap'):
            decryptor.process_network_data(path)
        else:
            decryptor.process_file(path)
    else:
        decryptor.process_directory(path)
    
    # Generate final report
    report_path = decryptor.generate_detailed_report()
    print(f"\nDetailed report available at: {report_path}")
