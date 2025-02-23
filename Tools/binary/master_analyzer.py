import os
import re
import base64
import zlib
import logging
import subprocess
import binascii
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib
from datetime import datetime
from Crypto.Cipher import AES, Blowfish, DES3
from Crypto.Util.Padding import unpad
import traceback

@dataclass
class AnalysisResult:
    success: bool
    encryption_detected: bool
    obfuscation_detected: bool
    patterns_found: List[str]
    decrypted_files: List[str]
    error: Optional[str] = None

class EvonyMasterAnalyzer:
    def __init__(self, swf_path: str):
        """Initialize Evony SWF Master Analyzer."""
        self.swf_path = swf_path
        self.output_dir = os.path.join("evony_analysis", 
                                     datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.makedirs(self.output_dir, exist_ok=True)
        self.setup_logging()
        
        # Tool paths
        self.as3_sorcerer_path = "C:/Program Files (x86)/AS3 Sorcerer/as3sorcerer.jar"
        self.tools_path = os.path.join(os.path.dirname(swf_path), "tools")
        
        # Encryption patterns
        self.encryption_patterns = {
            'aes': [
                rb'AES(?:\.|\[)["\'](?:encrypt|decrypt)["\']',
                rb'Rijndael',
                rb'CryptoJS\.AES',
                rb'\x00\x01\x02\x03\x04\x05\x06\x07',
                rb'(?:\x10{16}|\x20{16})',
                rb'SecurityManager\.encrypt',
                rb'EncryptionManager',
                rb'CryptoHelper'
            ],
            'rc4': [
                rb'RC4(?:\.|\[)["\'](?:encrypt|decrypt)["\']',
                rb'ArcFour',
                rb'rc4_encrypt',
                rb'[\x00-\xFF]{256}',
                rb'StreamCipher',
                rb'ByteStreamEncryption'
            ],
            'des': [
                rb'DES(?:\.|\[)["\'](?:encrypt|decrypt)["\']',
                rb'TripleDES',
                rb'3DES',
                rb'BlockCipher'
            ],
            'xor': [
                rb'(?:[\x00-\xFF])\1{2,}',
                rb'XOR',
                rb'\^=',
                rb'ByteXOR'
            ],
            'base64': [
                rb'[A-Za-z0-9+/]{4}*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?',
                rb'btoa\(',
                rb'atob\(',
                rb'Base64\.encode',
                rb'Base64\.decode'
            ]
        }
        
        # Obfuscation patterns
        self.obfuscation_patterns = {
            'junk_code': [
                rb'if\s*\(\s*false\s*\)',
                rb'while\s*\(\s*false\s*\)',
                rb'function\s*\w+\s*\(\)\s*{\s*return\s*\w+\s*;\s*}',
                rb'void\s+0;',
                rb'undefined;'
            ],
            'control_flow': [
                rb'switch\s*\(\s*\w+\s*\)\s*{\s*case\s+0x[0-9a-f]+:',
                rb'if\s*\(\s*\w+\s*===\s*0x[0-9a-f]+\s*\)',
                rb'goto\s+case\s+\d+',
                rb'default:\s*\{\s*\w+\s*=\s*\d+;\s*\}'
            ],
            'string_encryption': [
                rb'String\.fromCharCode\([^)]+\)',
                rb'\[[^\]]+\]\.join\([\'"][\'"]?\)',
                rb'\\u[0-9a-fA-F]{4}',
                rb'charCodeAt\(\d+\)\s*\^\s*\d+',
                rb'split\([\'"][\'"]?\)\.reverse\(\)'
            ],
            'dynamic_eval': [
                rb'eval\s*\(',
                rb'Function\s*\([^)]*\)',
                rb'setTimeout\s*\(\s*[\'"][^\'"]+[\'"]\s*,',
                rb'new\s+Function\s*\('
            ],
            'property_obfuscation': [
                rb'\[\s*[\'"](?:\\x[0-9a-fA-F]{2})+[\'"]\s*\]',
                rb'\w+\[\s*[\'"][\w$]+[\'"]\s*\]\s*=',
                rb'Object\.defineProperty\s*\(',
                rb'__defineGetter__'
            ]
        }

        # Evony-specific patterns
        self.evony_patterns = {
            'network': [
                rb'Socket(?:Connection|Manager|Event)',
                rb'NetManager',
                rb'HttpRequest',
                rb'AMFService'
            ],
            'game_logic': [
                rb'GameManager',
                rb'BattleManager',
                rb'ResourceManager',
                rb'PlayerManager'
            ],
            'ui': [
                rb'UIComponent',
                rb'PopUpManager',
                rb'MainView',
                rb'Dialog'
            ]
        }

    def setup_logging(self):
        """Configure detailed logging"""
        log_file = os.path.join(self.output_dir, 'analysis.log')
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def verify_swf(self) -> Tuple[bool, str]:
        """Verify SWF file integrity and type"""
        try:
            with open(self.swf_path, 'rb') as f:
                header = f.read(3)
                if header not in [b'CWS', b'FWS', b'ZWS']:
                    return False, "Invalid SWF signature"
                    
                f.seek(0)
                data = f.read()
                
                # For compressed SWF (CWS), decompress the data
                if header == b'CWS':
                    try:
                        decompressed = zlib.decompress(data[8:])
                        full_data = data[:8] + decompressed
                        # Save decompressed version for analysis
                        decompressed_path = os.path.join(self.output_dir, "decompressed.swf")
                        with open(decompressed_path, 'wb') as df:
                            df.write(b'FWS' + full_data[3:])
                        self.swf_path = decompressed_path
                        data = full_data
                    except zlib.error as e:
                        return False, f"Error decompressing SWF: {str(e)}"
                
                # Check file size consistency with some tolerance for compression
                reported_size = int.from_bytes(data[4:8], byteorder='little')
                actual_size = len(data)
                if not (0.5 <= actual_size / reported_size <= 2.0):
                    return False, f"File size mismatch: reported={reported_size}, actual={actual_size}"
                    
                return True, header.decode()
        except Exception as e:
            return False, f"Error verifying SWF: {str(e)}"

    def detect_patterns(self, content: bytes, pattern_dict: Dict[str, List[bytes]]) -> Dict[str, float]:
        """Detect patterns in content and return confidence scores"""
        results = {}
        for category, patterns in pattern_dict.items():
            total_matches = 0
            pattern_matches = 0
            for pattern in patterns:
                try:
                    matches = len(re.findall(pattern, content, re.IGNORECASE | re.MULTILINE))
                    if matches > 0:
                        pattern_matches += 1
                    total_matches += matches
                except Exception as e:
                    self.logger.error(f"Error matching pattern {pattern}: {e}")
            
            # Calculate confidence based on both pattern variety and frequency
            if pattern_matches > 0:
                variety_score = pattern_matches / len(patterns)
                frequency_score = min(1.0, total_matches / 10)  # Cap at 10 matches
                confidence = (variety_score + frequency_score) / 2
                if confidence > 0.1:  # Only report if confidence is significant
                    results[category] = confidence
        
        return results

    def decompile_with_as3sorcerer(self) -> bool:
        """Decompile using AS3 Sorcerer with advanced options"""
        try:
            output_dir = os.path.join(self.output_dir, "as3sorcerer_out")
            os.makedirs(output_dir, exist_ok=True)
            
            subprocess.run([
                "java", "-jar", self.as3_sorcerer_path,
                "-source", self.swf_path,
                "-out", output_dir,
                "-advanced",  # Enable advanced deobfuscation
                "-pcode",    # Include bytecode analysis
                "-debug"     # Include debug information
            ], check=True)
            
            self.logger.info("Successfully decompiled with AS3 Sorcerer")
            return True
        except Exception as e:
            self.logger.error(f"Error decompiling with AS3 Sorcerer: {e}")
            return False

    def parse_decompiled_code(self, content: bytes) -> List[Dict]:
        """Parse decompiled ActionScript code into individual files"""
        files = []
        current_file = None
        current_content = []
        
        # Split content into lines for processing
        lines = content.split(b'\n')
        for line in lines:
            try:
                line = line.strip()
                if not line:
                    continue
                
                # Check for file header
                if line.startswith(b'//------------------------------------------------------------'):
                    # Save previous file if exists
                    if current_file and current_content:
                        files.append({
                            'name': current_file,
                            'content': b'\n'.join(current_content)
                        })
                    current_content = []
                    current_file = None
                elif line.startswith(b'//') and not current_file:
                    # Try to extract file name
                    try:
                        file_name = line[2:].strip().decode('utf-8')
                        if file_name and not file_name.startswith('www.') and not file_name.startswith('Decompiled'):
                            current_file = file_name
                    except:
                        pass
                else:
                    current_content.append(line)
            except Exception as e:
                self.logger.error(f"Error parsing line: {e}")
                
        # Add last file
        if current_file and current_content:
            files.append({
                'name': current_file,
                'content': b'\n'.join(current_content)
            })
            
        return files

    def analyze_decompiled_code(self) -> Dict:
        """Analyze decompiled ActionScript code"""
        results = {
            'encryption': {},
            'obfuscation': {},
            'evony_specific': {},
            'suspicious_functions': [],
            'crypto_implementation': None  # New field for crypto analysis
        }
        
        as3_dir = os.path.join(self.output_dir, "as3sorcerer_out")
        if not os.path.exists(as3_dir):
            return results
            
        # Additional ActionScript-specific patterns
        actionscript_patterns = {
            'network': [
                rb'URLLoader',
                rb'URLRequest',
                rb'Socket\.',
                rb'XMLSocket',
                rb'NetConnection',
                rb'SharedObject'
            ],
            'binary': [
                rb'ByteArray',
                rb'readBytes',
                rb'writeBytes',
                rb'readObject',
                rb'writeObject'
            ],
            'security': [
                rb'Security\.',
                rb'allowDomain',
                rb'loadPolicyFile',
                rb'LocalConnection'
            ]
        }
            
        for root, _, files in os.walk(as3_dir):
            for file in files:
                if file.endswith('.as'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()
                            
                        # Detect encryption methods
                        enc_results = self.detect_patterns(content, self.encryption_patterns)
                        for method, confidence in enc_results.items():
                            if method not in results['encryption']:
                                results['encryption'][method] = confidence
                            else:
                                results['encryption'][method] = max(results['encryption'][method], confidence)
                        
                        # Detect obfuscation techniques
                        obf_results = self.detect_patterns(content, self.obfuscation_patterns)
                        for technique, confidence in obf_results.items():
                            if technique not in results['obfuscation']:
                                results['obfuscation'][technique] = confidence
                            else:
                                results['obfuscation'][technique] = max(results['obfuscation'][technique], confidence)
                        
                        # Detect Evony-specific patterns
                        evony_results = self.detect_patterns(content, self.evony_patterns)
                        for category, confidence in evony_results.items():
                            if category not in results['evony_specific']:
                                results['evony_specific'][category] = confidence
                            else:
                                results['evony_specific'][category] = max(results['evony_specific'][category], confidence)
                        
                        # Detect ActionScript-specific patterns
                        as3_results = self.detect_patterns(content, actionscript_patterns)
                        for category, confidence in as3_results.items():
                            key = f'as3_{category}'
                            if key not in results['evony_specific']:
                                results['evony_specific'][key] = confidence
                            else:
                                results['evony_specific'][key] = max(results['evony_specific'][key], confidence)
                        
                        # Record suspicious functions if any patterns were found
                        if any(enc_results.values()) or any(obf_results.values()) or \
                           any(evony_results.values()) or any(as3_results.values()):
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    code_content = f.read()
                                
                                # Extract function context
                                suspicious_lines = []
                                lines = code_content.split('\n')
                                for i, line in enumerate(lines):
                                    if any(pattern.encode() in line.encode() for patterns in 
                                          [self.encryption_patterns.values(), 
                                           self.obfuscation_patterns.values(), 
                                           self.evony_patterns.values(),
                                           actionscript_patterns.values()] 
                                          for pattern in patterns):
                                        context_start = max(0, i - 5)
                                        context_end = min(len(lines), i + 6)
                                        suspicious_lines.extend(lines[context_start:context_end])
                                
                                results['suspicious_functions'].append({
                                    'file': os.path.relpath(file_path, as3_dir),
                                    'encryption': enc_results,
                                    'obfuscation': obf_results,
                                    'evony_specific': evony_results,
                                    'as3_specific': as3_results,
                                    'context': '\n'.join(suspicious_lines)
                                })
                            except Exception as e:
                                self.logger.error(f"Error extracting context from {file_path}: {e}")
                    
                    except Exception as e:
                        self.logger.error(f"Error analyzing file {file_path}: {e}")
        
        # Add crypto implementation analysis
        crypto_results = self.analyze_crypto_implementation(content)
        if any(crypto_results.values()):
            results['crypto_implementation'] = crypto_results
        
        return results

    def analyze_crypto_implementation(self, content: bytes) -> Dict:
        """Analyze cryptographic implementation details"""
        results = {
            'password_hashing': [],
            'token_generation': [],
            'action_verification': [],
            'api_signing': [],
            'vulnerabilities': []
        }
        
        try:
            # Password hashing patterns
            password_patterns = [
                rb'SHA1\.hash\([^)]+\)\s*\+\s*[\'"]=[\'"].*?MD5\.hash',  # Combined SHA1+MD5
                rb'MD5\.hash\((\w+)\.password\)',  # Direct password hashing
            ]
            
            # Token generation patterns
            token_patterns = [
                rb'MD5\.hash\(MD5\.hash\([^)]+\)\s*\+\s*[\'"]IUGI_md5_key_',  # Double MD5 with static salt
                rb'MD5\.hash\([^)]+\)\s*\+\s*[\'"][^\'"]+_key_',  # MD5 with static salt
            ]
            
            # Action verification patterns
            action_patterns = [
                rb'MD5\.hash\([\'"](?:PlayEvony|Celebrate|EarnPrestige)[\'"].*?TAO_',  # Game action verification
                rb'MD5\.hash\(.*?Context\.getInstance\(\)\.(?:userName|getPlayerBean)',  # Context-based verification
            ]
            
            # API signing patterns
            api_patterns = [
                rb'MD5\.hash\([^)]+9f758e2deccbe6244f734371b9642eda',  # Hardcoded API key
                rb'[\'"][a-f0-9]{32}[\'"]',  # Potential hardcoded MD5 hashes
            ]
            
            # Check password hashing
            for pattern in password_patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
                if matches:
                    for match in matches:
                        context_start = max(0, content.rfind(b'\n', 0, match.start()) + 1)
                        context_end = content.find(b'\n', match.end())
                        if context_end == -1:
                            context_end = len(content)
                        
                        # Get broader context
                        broader_start = content.rfind(b'function', 0, context_start)
                        if broader_start != -1:
                            context_start = broader_start
                        
                        context = content[context_start:context_end].strip()
                        results['password_hashing'].append({
                            'pattern': pattern,
                            'context': context.decode('utf-8', errors='ignore'),
                            'line': content.count(b'\n', 0, match.start()) + 1,
                            'vulnerability': 'HIGH - Weak password hashing using MD5/SHA1 concatenation'
                        })
                        results['vulnerabilities'].append({
                            'type': 'weak_password_hashing',
                            'severity': 'HIGH',
                            'description': 'Password hashing uses weak algorithms (MD5/SHA1) and unsafe concatenation',
                            'context': context.decode('utf-8', errors='ignore'),
                            'line': content.count(b'\n', 0, match.start()) + 1
                        })
            
            # Check token generation
            for pattern in token_patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
                if matches:
                    for match in matches:
                        context_start = max(0, content.rfind(b'\n', 0, match.start()) + 1)
                        context_end = content.find(b'\n', match.end())
                        if context_end == -1:
                            context_end = len(content)
                        context = content[context_start:context_end].strip()
                        results['token_generation'].append({
                            'pattern': pattern,
                            'context': context.decode('utf-8', errors='ignore'),
                            'line': content.count(b'\n', 0, match.start()) + 1,
                            'vulnerability': 'HIGH - Token generation uses static salt and weak hashing'
                        })
                        results['vulnerabilities'].append({
                            'type': 'static_salt',
                            'severity': 'HIGH',
                            'description': 'Token generation uses hardcoded salt values',
                            'context': context.decode('utf-8', errors='ignore'),
                            'line': content.count(b'\n', 0, match.start()) + 1
                        })
            
            # Check action verification
            for pattern in action_patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
                if matches:
                    for match in matches:
                        context_start = max(0, content.rfind(b'\n', 0, match.start()) + 1)
                        context_end = content.find(b'\n', match.end())
                        if context_end == -1:
                            context_end = len(content)
                        context = content[context_start:context_end].strip()
                        results['action_verification'].append({
                            'pattern': pattern,
                            'context': context.decode('utf-8', errors='ignore'),
                            'line': content.count(b'\n', 0, match.start()) + 1,
                            'vulnerability': 'MEDIUM - Action verification uses predictable values'
                        })
                        results['vulnerabilities'].append({
                            'type': 'predictable_verification',
                            'severity': 'MEDIUM',
                            'description': 'Action verification uses predictable concatenation of values',
                            'context': context.decode('utf-8', errors='ignore'),
                            'line': content.count(b'\n', 0, match.start()) + 1
                        })
            
            # Check API signing
            for pattern in api_patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
                if matches:
                    for match in matches:
                        context_start = max(0, content.rfind(b'\n', 0, match.start()) + 1)
                        context_end = content.find(b'\n', match.end())
                        if context_end == -1:
                            context_end = len(content)
                        context = content[context_start:context_end].strip()
                        results['api_signing'].append({
                            'pattern': pattern,
                            'context': context.decode('utf-8', errors='ignore'),
                            'line': content.count(b'\n', 0, match.start()) + 1,
                            'vulnerability': 'CRITICAL - Hardcoded API key in client code'
                        })
                        results['vulnerabilities'].append({
                            'type': 'hardcoded_api_key',
                            'severity': 'CRITICAL',
                            'description': 'API key is hardcoded in client code',
                            'context': context.decode('utf-8', errors='ignore'),
                            'line': content.count(b'\n', 0, match.start()) + 1
                        })
        
        except Exception as e:
            self.logger.error(f"Error analyzing crypto implementation: {str(e)}")
            traceback.print_exc()
        
        return results

    def analyze_encryption_implementation(self, content: bytes, file_path: str) -> Dict:
        """Analyze encryption implementation for potential vulnerabilities"""
        vulnerabilities = []
        implementation_details = {}
        
        # Known vulnerable patterns
        vulnerability_patterns = {
            'hardcoded_keys': [
                rb'(?:key|iv|salt)\s*=\s*["\'][0-9a-fA-F]{16,}["\']',
                rb'0x[0-9a-fA-F]{16,}',
                rb'["\'][A-Za-z0-9+/]{22,}["\']'  # Base64 encoded keys
            ],
            'weak_key_generation': [
                rb'Math\.random\(',
                rb'new\s+Date\(\)',
                rb'getTime\(\)',
                rb'toString\(\).substring'
            ],
            'static_iv': [
                rb'(?:iv|salt)\s*=\s*new\s+ByteArray',
                rb'writeBytes\([^,]+,\s*0,\s*16\)'
            ],
            'ecb_mode': [
                rb'ECB',
                rb'Cipher\.getInstance\([^)]*ECB[^)]*\)',
                rb'(?:encrypt|decrypt)(?:Block|Blocks)'
            ],
            'padding_oracle': [
                rb'catch\s*\([^)]+\)\s*{\s*return\s*(?:false|null)',
                rb'catch\s*\([^)]+\)\s*{\s*throw',
                rb'PKCS5Padding|PKCS7Padding'
            ]
        }
        
        # Implementation patterns
        implementation_patterns = {
            'key_derivation': [
                rb'(?:derive|generate)Key',
                rb'PBKDF2',
                rb'hash(?:Password|Key)',
                rb'MD5|SHA(?:-?\d+)?'
            ],
            'encryption_mode': [
                rb'CBC|CFB|OFB|CTR|GCM',
                rb'Cipher\.getInstance',
                rb'CryptoStream'
            ],
            'initialization': [
                rb'initWith(?:Key|IV)',
                rb'createEncryptor',
                rb'cipher\.init'
            ]
        }
        
        # Check for vulnerabilities
        for vuln_type, patterns in vulnerability_patterns.items():
            matches = []
            for pattern in patterns:
                try:
                    found = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in found:
                        context_start = max(0, content.rfind(b'\n', 0, match.start()) + 1)
                        context_end = content.find(b'\n', match.end())
                        if context_end == -1:
                            context_end = len(content)
                        context = content[context_start:context_end].strip()
                        matches.append({
                            'pattern': pattern,
                            'context': context.decode('utf-8', errors='ignore'),
                            'line': content.count(b'\n', 0, match.start()) + 1
                        })
                except Exception as e:
                    self.logger.error(f"Error matching vulnerability pattern {pattern}: {e}")
            
            if matches:
                vulnerabilities.append({
                    'type': vuln_type,
                    'matches': matches,
                    'severity': 'HIGH' if vuln_type in ['hardcoded_keys', 'ecb_mode'] else 'MEDIUM'
                })
        
        # Analyze implementation details
        for impl_type, patterns in implementation_patterns.items():
            matches = []
            for pattern in patterns:
                try:
                    found = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in found:
                        context_start = max(0, content.rfind(b'\n', 0, match.start()) + 1)
                        context_end = content.find(b'\n', match.end())
                        if context_end == -1:
                            context_end = len(content)
                        context = content[context_start:context_end].strip()
                        matches.append({
                            'pattern': pattern,
                            'context': context.decode('utf-8', errors='ignore'),
                            'line': content.count(b'\n', 0, match.start()) + 1
                        })
                except Exception as e:
                    self.logger.error(f"Error matching implementation pattern {pattern}: {e}")
            
            if matches:
                implementation_details[impl_type] = matches
        
        return {
            'file': file_path,
            'vulnerabilities': vulnerabilities,
            'implementation': implementation_details
        }

    def analyze_encryption_component(self, content: bytes, file_path: str) -> Dict:
        """Deep analysis of encryption component implementation"""
        results = {
            'key_handling': [],
            'crypto_operations': [],
            'data_flow': [],
            'critical_vulnerabilities': []
        }
        
        try:
            # Normalize line endings and decode content
            content = content.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
            
            # Critical vulnerability patterns
            critical_patterns = {
                'key_exposure': [
                    rb'SharedObject\.getLocal\([^)]+\).*?\.data\[[\'"](key|iv|salt)[\'"]',
                    rb'trace\([^)]*(?:key|iv|salt)[^)]*\)',
                    rb'\.text\s*=\s*[^;]*(?:key|iv|salt)',
                    rb'URLVariables.*?key=',
                    rb'ExternalInterface\.call.*?key'
                ],
                'predictable_values': [
                    rb'(?:key|iv|salt)\s*=\s*(?:Math\.random|new Date|getTime)\(',
                    rb'\.getUTCMilliseconds\(\)',
                    rb'\.toString\(\)\.substr',
                    rb'Math\.floor\(Math\.random\(\)\s*\*'
                ],
                'unsafe_transmission': [
                    rb'send\([^)]*(?:key|iv|salt)[^)]*\)',
                    rb'URLRequest\([^)]*key[^)]*\)',
                    rb'Socket\.write.*?key',
                    rb'navigateToURL.*?key='
                ],
                'weak_encryption': [
                    rb'XORCipher',
                    rb'(?:key|data)\s*\^=',
                    rb'simple(?:Encrypt|Decrypt)',
                    rb'\.reverse\(\)'
                ]
            }
            
            # Crypto operation patterns
            crypto_patterns = {
                'key_generation': [
                    rb'function\s+(?:create|generate|derive)Key',
                    rb'ByteArray\.(?:readBytes|writeBytes)\([^,]+,\s*0,\s*(?:16|24|32)\)',
                    rb'MD5\.hash',
                    rb'SHA\d*\.hash'
                ],
                'encryption_flow': [
                    rb'encrypt\s*\([^{]+{([^}]+)}',
                    rb'cipher\s*\.[^;]+;',
                    rb'Crypto\.(?:encrypt|decrypt)',
                    rb'CryptoStream'
                ],
                'data_handling': [
                    rb'readBytes\([^)]+\)',
                    rb'writeBytes\([^)]+\)',
                    rb'position\s*=\s*0',
                    rb'ByteArray\.length'
                ]
            }
            
            # Check for critical vulnerabilities
            for vuln_type, patterns in critical_patterns.items():
                for pattern in patterns:
                    try:
                        matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
                        if matches:
                            for match in matches:
                                # Get full line context
                                line_start = content.rfind(b'\n', 0, match.start()) + 1
                                line_end = content.find(b'\n', match.end())
                                if line_end == -1:
                                    line_end = len(content)
                                
                                # Get broader context (up to 3 lines before and after)
                                context_start = content.rfind(b'\n', 0, line_start)
                                for _ in range(2):
                                    temp = content.rfind(b'\n', 0, context_start)
                                    if temp == -1:
                                        break
                                    context_start = temp
                                
                                context_end = line_end
                                for _ in range(3):
                                    temp = content.find(b'\n', context_end + 1)
                                    if temp == -1:
                                        break
                                    context_end = temp
                                
                                context = content[context_start:context_end].strip()
                                
                                # Extract function name and class name if possible
                                func_name = "unknown"
                                class_name = "unknown"
                                
                                # Look for function
                                func_start = content.rfind(b'function', 0, match.start())
                                if func_start != -1:
                                    func_name_match = re.search(rb'function\s+(\w+)', content[func_start:match.start()])
                                    if func_name_match:
                                        func_name = func_name_match.group(1).decode('utf-8', errors='ignore')
                                
                                # Look for class
                                class_start = content.rfind(b'class', 0, match.start())
                                if class_start != -1:
                                    class_name_match = re.search(rb'class\s+(\w+)', content[class_start:match.start()])
                                    if class_name_match:
                                        class_name = class_name_match.group(1).decode('utf-8', errors='ignore')
                                
                                results['critical_vulnerabilities'].append({
                                    'type': vuln_type,
                                    'pattern': pattern,
                                    'context': context.decode('utf-8', errors='ignore'),
                                    'class': class_name,
                                    'function': func_name,
                                    'line': content.count(b'\n', 0, match.start()) + 1,
                                    'severity': 'HIGH' if vuln_type in ['key_exposure', 'weak_encryption'] else 'MEDIUM'
                                })
                    except Exception as e:
                        self.logger.error(f"Error matching critical pattern {pattern}: {str(e)}")
            
            # Analyze crypto operations (similar structure as above)
            for op_type, patterns in crypto_patterns.items():
                for pattern in patterns:
                    try:
                        matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
                        if matches:
                            for match in matches:
                                # Similar context extraction as above
                                line_start = content.rfind(b'\n', 0, match.start()) + 1
                                line_end = content.find(b'\n', match.end())
                                if line_end == -1:
                                    line_end = len(content)
                                
                                context_start = content.rfind(b'\n', 0, line_start)
                                for _ in range(2):
                                    temp = content.rfind(b'\n', 0, context_start)
                                    if temp == -1:
                                        break
                                    context_start = temp
                                
                                context_end = line_end
                                for _ in range(3):
                                    temp = content.find(b'\n', context_end + 1)
                                    if temp == -1:
                                        break
                                    context_end = temp
                                
                                context = content[context_start:context_end].strip()
                                
                                # Extract function name and class name if possible
                                func_name = "unknown"
                                class_name = "unknown"
                                
                                # Look for function
                                func_start = content.rfind(b'function', 0, match.start())
                                if func_start != -1:
                                    func_name_match = re.search(rb'function\s+(\w+)', content[func_start:match.start()])
                                    if func_name_match:
                                        func_name = func_name_match.group(1).decode('utf-8', errors='ignore')
                                
                                # Look for class
                                class_start = content.rfind(b'class', 0, match.start())
                                if class_start != -1:
                                    class_name_match = re.search(rb'class\s+(\w+)', content[class_start:match.start()])
                                    if class_name_match:
                                        class_name = class_name_match.group(1).decode('utf-8', errors='ignore')
                                
                                results[op_type].append({
                                    'pattern': pattern,
                                    'context': context.decode('utf-8', errors='ignore'),
                                    'class': class_name,
                                    'function': func_name,
                                    'line': content.count(b'\n', 0, match.start()) + 1
                                })
                    except Exception as e:
                        self.logger.error(f"Error matching crypto pattern {pattern}: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Error analyzing encryption component in {file_path}: {str(e)}")
        
        return results

    def analyze(self) -> AnalysisResult:
        """Main analysis function"""
        self.logger.info(f"Starting analysis of {self.swf_path}")
        
        # Initialize results
        patterns_found = []
        analysis_results = self.analyze_decompiled_code()
        
        # Format results
        try:
            if analysis_results.get('encryption'):
                patterns_found.append("\nEncryption Methods Found:")
                for method, details in analysis_results['encryption'].items():
                    patterns_found.append(f"  - {method}: {details['confidence']}%")
                    if details.get('context'):
                        patterns_found.append("  Context:")
                        for line in details['context']:
                            patterns_found.append(f"    {line}")
            
            if analysis_results.get('obfuscation'):
                patterns_found.append("\nObfuscation Techniques Found:")
                for technique, details in analysis_results['obfuscation'].items():
                    patterns_found.append(f"  - {technique}: {details['confidence']}%")
                    if details.get('context'):
                        patterns_found.append("  Context:")
                        for line in details['context']:
                            patterns_found.append(f"    {line}")
            
            if analysis_results.get('evony_specific'):
                patterns_found.append("\nEvony-Specific Components Found:")
                for component, details in analysis_results['evony_specific'].items():
                    patterns_found.append(f"  - {component}: {details['confidence']}%")
                    if details.get('context'):
                        patterns_found.append("  Context:")
                        for line in details['context']:
                            patterns_found.append(f"    {line}")
            
            if analysis_results.get('crypto_implementation'):
                crypto = analysis_results['crypto_implementation']
                patterns_found.append("\n=== CRYPTOGRAPHIC IMPLEMENTATION ANALYSIS ===")
                
                if crypto.get('vulnerabilities'):
                    patterns_found.append("\n⚠️ CRITICAL SECURITY VULNERABILITIES:")
                    for vuln in crypto['vulnerabilities']:
                        patterns_found.append(f"\n[{vuln['severity']}] {vuln['type'].upper()}")
                        patterns_found.append(f"Description: {vuln['description']}")
                        patterns_found.append(f"Line {vuln['line']}:")
                        patterns_found.append("-" * 40)
                        patterns_found.append(vuln['context'])
                        patterns_found.append("-" * 40)
                
                if crypto.get('password_hashing'):
                    patterns_found.append("\nPassword Hashing Implementation:")
                    for impl in crypto['password_hashing']:
                        patterns_found.append(f"\nLine {impl['line']}:")
                        patterns_found.append(f"Vulnerability: {impl['vulnerability']}")
                        patterns_found.append("-" * 40)
                        patterns_found.append(impl['context'])
                        patterns_found.append("-" * 40)
                
                if crypto.get('token_generation'):
                    patterns_found.append("\nToken Generation Implementation:")
                    for impl in crypto['token_generation']:
                        patterns_found.append(f"\nLine {impl['line']}:")
                        patterns_found.append(f"Vulnerability: {impl['vulnerability']}")
                        patterns_found.append("-" * 40)
                        patterns_found.append(impl['context'])
                        patterns_found.append("-" * 40)
                
                if crypto.get('action_verification'):
                    patterns_found.append("\nAction Verification Implementation:")
                    for impl in crypto['action_verification']:
                        patterns_found.append(f"\nLine {impl['line']}:")
                        patterns_found.append(f"Vulnerability: {impl['vulnerability']}")
                        patterns_found.append("-" * 40)
                        patterns_found.append(impl['context'])
                        patterns_found.append("-" * 40)
                
                if crypto.get('api_signing'):
                    patterns_found.append("\nAPI Request Signing Implementation:")
                    for impl in crypto['api_signing']:
                        patterns_found.append(f"\nLine {impl['line']}:")
                        patterns_found.append(f"Vulnerability: {impl['vulnerability']}")
                        patterns_found.append("-" * 40)
                        patterns_found.append(impl['context'])
                        patterns_found.append("-" * 40)
        
            # Write results to file
            output_file = os.path.join(self.output_dir, "analysis_results.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(patterns_found))
            self.logger.info(f"Analysis results saved to {output_file}")
            
            # Print to console with proper encoding
            print("\nANALYSIS RESULTS")
            print("=" * 80)
            
            # Process and print each line with proper encoding
            for line in patterns_found:
                try:
                    # First try to encode as UTF-8
                    encoded_line = line.encode('utf-8', errors='ignore')
                    # Then decode back to string for printing
                    decoded_line = encoded_line.decode('utf-8', errors='ignore')
                    print(decoded_line)
                except Exception as e:
                    # If any error occurs, fall back to ASCII
                    print(line.encode('ascii', errors='replace').decode())
            
            print("=" * 80)
            print(f"\nFull analysis results saved to: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error formatting results: {str(e)}")
            traceback.print_exc()
        
        return AnalysisResult(
            success=True,
            encryption_detected=bool(analysis_results.get('encryption')),
            obfuscation_detected=bool(analysis_results.get('obfuscation')),
            patterns_found=patterns_found
        )

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Evony SWF Master Analyzer")
    parser.add_argument("swf_file", help="Path to the SWF file to analyze")
    args = parser.parse_args()
    
    analyzer = EvonyMasterAnalyzer(args.swf_file)
    result = analyzer.analyze()
    
    if result.success:
        print("\n=== Analysis Results ===")
        print(f"Encryption detected: {result.encryption_detected}")
        print(f"Obfuscation detected: {result.obfuscation_detected}")
        print("\nPatterns found:")
        for pattern in result.patterns_found:
            print(f"  - {pattern}")
        print("\nDecompiled files saved in:")
        for path in result.decrypted_files:
            print(f"  - {path}")
    else:
        print(f"\nAnalysis failed: {result.error}")

if __name__ == "__main__":
    main()
