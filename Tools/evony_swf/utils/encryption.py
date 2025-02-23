"""Encryption utilities for SWF tag analysis."""
import logging
import zlib
import math
from typing import Dict, List, Optional, Tuple
from Crypto.Cipher import ARC4

class EncryptionAnalyzer:
    """Analyzes and handles encrypted SWF tags."""
    
    # Known Evony encryption keys
    EVONY_KEYS = [
        b'Evony',
        b'EvonyAge2',
        b'E2',
        b'age2',
        b'evony_v2'
    ]
    
    # XOR patterns used by Evony
    XOR_PATTERNS = [
        bytes([0x55] * 16),  # Common pattern
        bytes([0xAA] * 16),  # Alternative pattern
        bytes([0xFF] * 16),  # Full mask
        bytes.fromhex('55AA55AA55AA55AA'),  # Alternating pattern
        bytes.fromhex('33CC33CC33CC33CC')   # Another common pattern
    ]
    
    # Tag-specific encryption methods
    TAG_ENCRYPTION = {
        233: {
            'method': 'xor',
            'patterns': [
                bytes([0x55]),  # Common key
                bytes([0xAA]),  # Alternative key
                bytes([0xFF]),  # Full mask
                bytes([0x33]),  # Another common key
                bytes([0xCC])   # Yet another key
            ],
            'header_size': 2  # First 2 bytes are tag header
        },
        396: {
            'method': 'rc4',
            'keys': [
                b'Evony',
                b'EvonyAge2',
                b'E2',
                b'age2'
            ],
            'header_size': 3  # First 3 bytes are tag header
        },
        449: {
            'method': 'multi',
            'layers': [
                {'method': 'xor', 'key': bytes([0x55])},
                {'method': 'rc4', 'key': b'Evony'}
            ],
            'header_size': 4  # First 4 bytes are tag header
        }
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_tag(self, tag_data: bytes, tag_code: int) -> Dict:
        """Analyze a tag for encryption."""
        result = {
            'encrypted': False,
            'method': None,
            'key': None,
            'confidence': 0.0,
            'layers': []
        }
        
        # Skip if tag is too short
        if len(tag_data) < 8:
            return result
            
        # Check for special tag codes
        if tag_code in self.TAG_ENCRYPTION:
            encryption_info = self.TAG_ENCRYPTION[tag_code]
            result['encrypted'] = True
            result['method'] = encryption_info['method']
            result['confidence'] = 0.9  # High confidence for known tags
            
            # Get the data after the header
            header_size = encryption_info.get('header_size', 0)
            encrypted_data = tag_data[header_size:]
            
            if encryption_info['method'] == 'xor':
                # Try each XOR pattern
                for pattern in encryption_info['patterns']:
                    decrypted = self._try_xor_decrypt(encrypted_data, pattern)
                    if self._looks_like_valid_data(decrypted):
                        result['key'] = pattern
                        result['decrypted'] = decrypted
                        break
                        
            elif encryption_info['method'] == 'rc4':
                # Try each RC4 key
                for key in encryption_info['keys']:
                    decrypted = self._try_rc4_decrypt(encrypted_data, key)
                    if self._looks_like_valid_data(decrypted):
                        result['key'] = key
                        result['decrypted'] = decrypted
                        break
                        
            elif encryption_info['method'] == 'multi':
                # Multi-layer encryption
                result['layers'] = encryption_info['layers']
                current_data = encrypted_data
                
                # Apply each layer
                for layer in encryption_info['layers']:
                    if layer['method'] == 'xor':
                        current_data = self._try_xor_decrypt(current_data, layer['key'])
                    elif layer['method'] == 'rc4':
                        current_data = self._try_rc4_decrypt(current_data, layer['key'])
                        
                if self._looks_like_valid_data(current_data):
                    result['decrypted'] = current_data
                    
            return result
            
        # For unknown tags, check entropy and patterns
        entropy = self._calculate_entropy(tag_data[:1024])
        if entropy > 7.0:  # High entropy suggests encryption
            self.logger.debug(f"High entropy detected: {entropy}")
            
            # Try RC4 first
            for key in self.EVONY_KEYS:
                decrypted = self._try_rc4_decrypt(tag_data, key)
                if self._looks_like_valid_data(decrypted):
                    result.update({
                        'encrypted': True,
                        'method': 'rc4',
                        'key': key,
                        'confidence': 0.8,
                        'decrypted': decrypted
                    })
                    return result
                    
            # Try XOR patterns
            for pattern in self.XOR_PATTERNS:
                decrypted = self._try_xor_decrypt(tag_data, pattern)
                if self._looks_like_valid_data(decrypted):
                    result.update({
                        'encrypted': True,
                        'method': 'xor',
                        'key': pattern,
                        'confidence': 0.7,
                        'decrypted': decrypted
                    })
                    return result
                    
        return result
        
    def decrypt_tag(self, tag_data: bytes, encryption_info: Dict) -> bytes:
        """Decrypt a tag using the detected encryption method."""
        if not encryption_info['encrypted']:
            return tag_data
            
        try:
            # If we already have decrypted data, return it
            if 'decrypted' in encryption_info:
                return encryption_info['decrypted']
                
            # Get the header size
            if encryption_info['method'] in self.TAG_ENCRYPTION:
                header_size = self.TAG_ENCRYPTION[encryption_info['method']].get('header_size', 0)
            else:
                header_size = 0
                
            # Split header and encrypted data
            header = tag_data[:header_size]
            encrypted_data = tag_data[header_size:]
            
            if encryption_info['method'] == 'rc4':
                decrypted = self._try_rc4_decrypt(encrypted_data, encryption_info['key'])
                
            elif encryption_info['method'] == 'xor':
                decrypted = self._try_xor_decrypt(encrypted_data, encryption_info['key'])
                
            elif encryption_info['method'] == 'multi':
                decrypted = encrypted_data
                for layer in encryption_info['layers']:
                    if layer['method'] == 'rc4':
                        decrypted = self._try_rc4_decrypt(decrypted, layer['key'])
                    elif layer['method'] == 'xor':
                        decrypted = self._try_xor_decrypt(decrypted, layer['key'])
                        
            else:
                self.logger.warning(f"Unknown encryption method: {encryption_info['method']}")
                return tag_data
                
            # Combine header and decrypted data
            return header + decrypted
            
        except Exception as e:
            self.logger.error(f"Error decrypting tag: {str(e)}")
            return tag_data
            
    def _try_rc4_decrypt(self, data: bytes, key: bytes) -> bytes:
        """Try RC4 decryption."""
        try:
            cipher = ARC4.new(key)
            return cipher.decrypt(data)
        except Exception as e:
            self.logger.debug(f"RC4 decryption failed: {str(e)}")
            return data
            
    def _try_xor_decrypt(self, data: bytes, pattern: bytes) -> bytes:
        """Try XOR decryption."""
        result = bytearray(data)
        for i in range(len(result)):
            result[i] ^= pattern[i % len(pattern)]
        return bytes(result)
        
    def _looks_like_valid_data(self, data: bytes) -> bool:
        """Check if data looks like valid Flash content."""
        if len(data) < 8:
            return False
            
        # Check for common Flash patterns
        patterns = [
            b'TCSO',  # SharedObject
            b'TEXP',  # Export
            b'TSYN',  # Symbol
            b'TABC',  # ABC
            b'DefineSprite',
            b'DefineBits',
            b'\x00\x00\x00',  # Common tag header
            b'\xFF\xFF\xFF',   # Common tag marker
            b'\x40\x00',       # Common ABC tag marker
            b'\x3C\x00'        # Common sprite marker
        ]
        
        # Check first 1KB for patterns
        sample = data[:1024]
        
        # Check for valid patterns
        if any(pattern in sample for pattern in patterns):
            return True
            
        # Check for reasonable byte distribution
        byte_count = {}
        for byte in sample:
            byte_count[byte] = byte_count.get(byte, 0) + 1
            
        # Most valid Flash content has a somewhat even distribution
        # with some common bytes appearing more frequently
        unique_bytes = len(byte_count)
        max_freq = max(byte_count.values()) / len(sample)
        
        return unique_bytes > 20 and max_freq < 0.3  # Reasonable thresholds
        
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data."""
        if not data:
            return 0.0
            
        # Count byte frequencies
        frequencies = {}
        for byte in data:
            frequencies[byte] = frequencies.get(byte, 0) + 1
            
        # Calculate entropy
        entropy = 0
        for count in frequencies.values():
            probability = count / len(data)
            entropy -= probability * math.log2(probability)
            
        return entropy
