import os
import sys
import struct
import logging
from collections import defaultdict

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('swf_tag_analysis.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('SwfTagAnalyzer')

class SwfTagAnalyzer:
    def __init__(self, logger):
        self.logger = logger
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
            23: "DefineButtonCxform",
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
            91: "DefineFont4",
            93: "EnableTelemetry",
            233: "EvonyCustomTag1",
            396: "EvonyCustomTag2",
            449: "EvonyCustomTag3"
        }
        
    def read_ui8(self, f):
        return struct.unpack('B', f.read(1))[0]
        
    def read_ui16(self, f):
        return struct.unpack('<H', f.read(2))[0]
        
    def read_ui32(self, f):
        return struct.unpack('<I', f.read(4))[0]
        
    def read_tag_header(self, f):
        tag_code_and_length = self.read_ui16(f)
        tag_code = tag_code_and_length >> 6
        length = tag_code_and_length & 0x3F
        if length == 0x3F:
            length = self.read_ui32(f)
        return tag_code, length
        
    def analyze_swf(self, swf_path):
        tag_counts = defaultdict(int)
        tag_sizes = defaultdict(int)
        total_size = 0
        
        with open(swf_path, 'rb') as f:
            # Skip SWF header (first 8 bytes)
            f.seek(8)
            
            # Read tags
            while True:
                try:
                    tag_code, length = self.read_tag_header(f)
                    tag_name = self.tag_types.get(tag_code, f"Unknown_{tag_code}")
                    tag_counts[tag_code] += 1
                    tag_sizes[tag_code] += length
                    total_size += length
                    
                    # Skip tag data
                    f.seek(length, 1)
                    
                    if tag_code == 0:  # End tag
                        break
                except Exception as e:
                    self.logger.error(f"Error reading tag: {e}")
                    break
                    
        return tag_counts, tag_sizes, total_size
        
    def compare_swfs(self, original_path, rebuilt_path):
        self.logger.info(f"Analyzing original SWF: {original_path}")
        orig_counts, orig_sizes, orig_total = self.analyze_swf(original_path)
        
        self.logger.info(f"Analyzing rebuilt SWF: {rebuilt_path}")
        rebuilt_counts, rebuilt_sizes, rebuilt_total = self.analyze_swf(rebuilt_path)
        
        # Compare results
        self.logger.info("\nTag Count Comparison:")
        all_tags = sorted(set(orig_counts.keys()) | set(rebuilt_counts.keys()))
        
        for tag_code in all_tags:
            tag_name = self.tag_types.get(tag_code, f"Unknown_{tag_code}")
            orig_count = orig_counts.get(tag_code, 0)
            rebuilt_count = rebuilt_counts.get(tag_code, 0)
            orig_size = orig_sizes.get(tag_code, 0)
            rebuilt_size = rebuilt_sizes.get(tag_code, 0)
            
            if orig_count != rebuilt_count or orig_size != rebuilt_size:
                self.logger.warning(f"{tag_name} (Code {tag_code}):")
                self.logger.warning(f"  Count: {orig_count} -> {rebuilt_count}")
                self.logger.warning(f"  Size: {orig_size} -> {rebuilt_size}")
            else:
                self.logger.info(f"{tag_name} (Code {tag_code}): {orig_count} tags, {orig_size} bytes (unchanged)")
                
        size_diff = rebuilt_total - orig_total
        size_diff_percent = (size_diff / orig_total) * 100 if orig_total > 0 else 0
        
        self.logger.info(f"\nTotal size difference: {size_diff} bytes ({size_diff_percent:.2f}%)")
        
def main():
    logger = setup_logging()
    analyzer = SwfTagAnalyzer(logger)
    
    original_swf = r"j:\evony_1921\EvonyClient1921.swf"
    rebuilt_swf = r"j:\evony_1921\output\EvonyClient1921_rebuilt.swf"
    
    if not os.path.exists(original_swf):
        logger.error(f"Original SWF not found: {original_swf}")
        return
        
    if not os.path.exists(rebuilt_swf):
        logger.error(f"Rebuilt SWF not found: {rebuilt_swf}")
        return
        
    analyzer.compare_swfs(original_swf, rebuilt_swf)
    
if __name__ == '__main__':
    main()
