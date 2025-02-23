"""SWF file format utilities."""
import logging
import zlib
import lzma
from typing import Optional, Dict, List, Tuple

def read_swf_header(data: bytes) -> dict:
    """Read SWF header and return header info."""
    if len(data) < 8:
        raise ValueError("Invalid SWF file (too small)")
        
    signature = data[:3].decode('ascii')
    version = data[3]
    length = int.from_bytes(data[4:8], 'little')
    
    header = {
        'signature': signature,
        'version': version,
        'length': length,
        'header_size': 8,
        'compression': 'none'
    }
    
    if signature == 'CWS':
        header['compression'] = 'zlib'
    elif signature == 'ZWS':
        header['compression'] = 'lzma'
    elif signature != 'FWS':
        raise ValueError(f"Invalid SWF signature: {signature}")
        
    return header

def parse_swf_tag(data: bytes) -> Tuple[int, int, bytes]:
    """Parse a single SWF tag and return (tag_code, tag_length, tag_data)."""
    if len(data) < 2:
        raise ValueError("Invalid tag data (too small)")
        
    # Read tag code and length
    tag_header = int.from_bytes(data[0:2], 'little')
    tag_code = tag_header >> 6
    tag_length = tag_header & 0x3F
    
    # Check for long tag
    if tag_length == 0x3F:
        if len(data) < 6:
            raise ValueError("Invalid long tag data")
        tag_length = int.from_bytes(data[2:6], 'little')
        tag_data = data[6:6+tag_length]
    else:
        tag_data = data[2:2+tag_length]
        
    return tag_code, tag_length, tag_data

def decompress_swf(data: bytes) -> Optional[bytes]:
    """Decompress SWF file content."""
    try:
        if len(data) < 8:
            return None
            
        signature = data[0:3].decode('ascii')
        
        if signature == 'FWS':
            return data
            
        # Get uncompressed size
        uncompressed_size = int.from_bytes(data[4:8], byteorder='little')
        
        # Decompress based on signature
        if signature == 'CWS':
            # ZLIB compression
            return data[0:8] + zlib.decompress(data[8:])
        elif signature == 'ZWS':
            # LZMA compression
            return data[0:8] + lzma.decompress(data[8:])
            
        return None
        
    except Exception as e:
        logging.error(f"Error decompressing SWF: {str(e)}")
        return None
