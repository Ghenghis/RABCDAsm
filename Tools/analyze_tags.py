"""Analyze special encrypted tags in Evony SWF."""
import logging
import os
import json
from evony_swf.utils.encryption import EncryptionAnalyzer
from evony_swf.analyzers.abc_analyzer import ABCAnalyzer

class BytesEncoder(json.JSONEncoder):
    """Custom JSON encoder that can handle bytes objects."""
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.hex()
        return super().default(obj)

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def analyze_tag(tag_path: str, tag_code: int, output_dir: str) -> dict:
    """Analyze a specific tag file."""
    logger = logging.getLogger(__name__)
    encryption_analyzer = EncryptionAnalyzer()
    abc_analyzer = ABCAnalyzer()
    
    try:
        with open(tag_path, 'rb') as f:
            tag_data = f.read()
            
        logger.debug(f"Read {len(tag_data)} bytes from {tag_path}")
        
        # First check encryption
        encryption_info = encryption_analyzer.analyze_tag(tag_data, tag_code)
        logger.debug(f"Encryption analysis result: {encryption_info}")
        
        result = {
            'tag_code': tag_code,
            'path': tag_path,
            'size': len(tag_data),
            'encryption': encryption_info
        }
        
        # If encrypted, try to decrypt
        if encryption_info['encrypted']:
            logger.info(f"Attempting to decrypt tag {tag_code} using {encryption_info['method']}")
            decrypted_data = encryption_analyzer.decrypt_tag(tag_data, encryption_info)
            result['decrypted_size'] = len(decrypted_data)
            
            # If it's an ABC tag (82), analyze the ActionScript
            if tag_code == 82:  # DoABC tag
                logger.info("Processing ABC tag content")
                abc_result = abc_analyzer.process_abc_tag(decrypted_data, output_dir)
                result['abc_analysis'] = abc_result
                
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing tag {tag_path}: {str(e)}", exc_info=True)
        return {
            'tag_code': tag_code,
            'path': tag_path,
            'error': str(e)
        }

def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Setup paths
        tags_dir = "j:/robobuilder/test_output_v2/tags"
        output_dir = "j:/robobuilder/analysis_output"
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Analyzing tags from {tags_dir}")
        logger.info(f"Output directory: {output_dir}")
        
        # Special tags to analyze
        special_tags = [233, 396, 449, 82]  # Including DoABC (82)
        results = []
        
        # Process each tag
        for tag_code in special_tags:
            logger.info(f"Analyzing tags with code {tag_code}")
            
            # Find all instances of this tag
            tag_files = [f for f in os.listdir(tags_dir) 
                        if f.startswith(f"tag_{tag_code}_")]
            
            logger.info(f"Found {len(tag_files)} files for tag {tag_code}")
            
            for tag_file in tag_files:
                tag_path = os.path.join(tags_dir, tag_file)
                logger.info(f"Processing {tag_file}")
                
                result = analyze_tag(tag_path, tag_code, output_dir)
                results.append(result)
                
        # Save results using custom encoder
        output_file = os.path.join(output_dir, "tag_analysis.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, cls=BytesEncoder)
            
        logger.info(f"Analysis complete. Results saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
