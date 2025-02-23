"""Compression utilities for SWF files."""
import zlib
import logging
from typing import Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class CompressionHandler:
    """Handles SWF compression and decompression."""
    
    # Known working parameters for Evony SWF files
    EVONY_WINDOW_BITS = 15
    EVONY_MEM_LEVEL = 8
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def decompress_swf(self, data: bytes) -> Tuple[bytes, dict]:
        """Decompress a SWF file and return decompressed data and compression info."""
        if len(data) < 8:
            raise ValueError("Invalid SWF file: too short")
            
        signature = data[:3]
        version = data[3]
        length = int.from_bytes(data[4:8], 'little')
        
        self.logger.debug(f"SWF Header - Signature: {signature}, Version: {version}, Length: {length}")
        
        compression_info = {
            'signature': signature,
            'version': version,
            'length': length,
            'method': None,
            'window_bits': None,
            'mem_level': None
        }
        
        if signature == b'CWS':
            self.logger.debug("Found ZLIB compressed SWF")
            compression_info['method'] = 'zlib'
            
            # First try default decompression
            try:
                decompressed = zlib.decompress(data[8:])
                self.logger.debug(f"Successfully decompressed {len(decompressed)} bytes")
                
                # Always validate the decompressed data
                if len(decompressed) >= length - 8:
                    self.logger.debug("Decompressed length matches expected length")
                    compression_info.update({
                        'window_bits': self.EVONY_WINDOW_BITS,
                        'mem_level': self.EVONY_MEM_LEVEL
                    })
                    return decompressed, compression_info
                else:
                    self.logger.error("Decompressed length does not match expected length")
                    
            except zlib.error:
                self.logger.debug("Default decompression failed, trying with custom parameters")
                
                # Try with custom parameters
                try:
                    decompressor = zlib.decompressobj(wbits=self.EVONY_WINDOW_BITS)
                    decompressed = decompressor.decompress(data[8:])
                    self.logger.debug(f"Successfully decompressed {len(decompressed)} bytes with custom parameters")
                    
                    # Validate decompressed length
                    if len(decompressed) >= length - 8:
                        self.logger.debug("Decompressed length matches expected length")
                        compression_info.update({
                            'window_bits': self.EVONY_WINDOW_BITS,
                            'mem_level': self.EVONY_MEM_LEVEL
                        })
                        return decompressed, compression_info
                    else:
                        self.logger.error("Decompressed length does not match expected length")
                        
                except Exception as e:
                    self.logger.error(f"Error decompressing ZLIB data with custom parameters: {str(e)}")
                    raise
                    
        elif signature == b'FWS':
            self.logger.debug("Found uncompressed SWF")
            compression_info['method'] = 'none'
            return data[8:], compression_info
            
        elif signature == b'ZWS':
            self.logger.error("LZMA compression not supported yet")
            raise NotImplementedError("LZMA compression not supported yet")
            
        self.logger.error(f"Unknown or invalid compression signature: {signature}")
        raise ValueError(f"Unknown or invalid compression: {signature}")
        
    def compress_swf(self, data: bytes, compression_info: dict) -> bytes:
        """Compress SWF data using the original compression parameters."""
        if not compression_info['method']:
            return data
            
        try:
            if compression_info['method'] == 'zlib':
                self.logger.debug("Compressing with ZLIB")
                # Use Evony-specific compression parameters
                compressor = zlib.compressobj(
                    level=9,  # Maximum compression
                    method=zlib.DEFLATED,
                    wbits=self.EVONY_WINDOW_BITS,
                    memLevel=self.EVONY_MEM_LEVEL,
                    strategy=zlib.Z_DEFAULT_STRATEGY
                )
                compressed = compressor.compress(data) + compressor.flush()
                self.logger.debug(f"Compressed {len(data)} bytes to {len(compressed)} bytes")
                
                # Build header
                header = (
                    b'CWS' +
                    compression_info['version'].to_bytes(1, 'little') +
                    (len(compressed) + 8).to_bytes(4, 'little')
                )
                return header + compressed
                
            elif compression_info['method'] == 'none':
                self.logger.debug("No compression needed")
                header = (
                    b'FWS' +
                    compression_info['version'].to_bytes(1, 'little') +
                    (len(data) + 8).to_bytes(4, 'little')
                )
                return header + data
                
            else:
                self.logger.error(f"Unsupported compression method: {compression_info['method']}")
                raise ValueError(f"Unsupported compression method: {compression_info['method']}")
                
        except Exception as e:
            self.logger.error(f"Error compressing SWF: {str(e)}")
            raise
