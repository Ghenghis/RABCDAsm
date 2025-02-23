import os
import shutil
from pathlib import Path

def setup_tools():
    # Project root directory
    project_root = Path(os.path.dirname(os.path.dirname(__file__)))
    tools_dir = project_root / "Tools"

    # Create tool directories
    tool_dirs = {
        "swf_analysis": tools_dir / "swf_analysis",
        "decompilers": tools_dir / "decompilers",
        "crypto": tools_dir / "crypto",
        "binary": tools_dir / "binary",
        "utilities": tools_dir / "utilities",
    }

    for dir_path in tool_dirs.values():
        dir_path.mkdir(exist_ok=True)

    # Source directories from MEMORIES
    source_dirs = {
        "robobuilder": Path("J:/evony_1921/useful_Scripts/script5/robobuilder"),
        "action_script": Path("J:/Projects/Action_Script_Tool"),
        "evony_tools": Path("J:/evony_1921"),
    }

    # Tool mappings - what to copy where
    tool_mappings = {
        # SWF Analysis Tools
        "swf_analysis": [
            (source_dirs["evony_tools"] / "evony_unpack_build_tools/tools/evony_swf_analyzer.py", "swf_analyzer.py"),
            (source_dirs["evony_tools"] / "evony_unpack_build_tools/tools/analyze_swf_tags.py", "tag_analyzer.py"),
            (source_dirs["evony_tools"] / "evony_unpack_build_tools/tools/evony_abc_analyzer.py", "abc_analyzer.py"),
        ],
        
        # Decompilers
        "decompilers": [
            (source_dirs["evony_tools"] / "AS3_Sorcerer", "as3_sorcerer"),
            (source_dirs["evony_tools"] / "evony_unpack_build_tools/tools/extract_abc.py", "abc_extractor.py"),
        ],
        
        # Crypto Tools
        "crypto": [
            (source_dirs["evony_tools"] / "evony_unpack_build_tools/tools/evony_crypto.py", "crypto_utils.py"),
            (source_dirs["evony_tools"] / "evony_unpack_build_tools/tools/evony_decryptor.py", "decryptor.py"),
            (source_dirs["evony_tools"] / "evony_unpack_build_tools/tools/evony_crypto_analyzer.py", "crypto_analyzer.py"),
        ],
        
        # Binary Analysis
        "binary": [
            (source_dirs["evony_tools"] / "evony_unpack_build_tools/tools/evony_master_analyzer.py", "master_analyzer.py"),
            (source_dirs["evony_tools"] / "evony_unpack_build_tools/tools/evony_master_toolkit.py", "master_toolkit.py"),
        ],
        
        # Utilities
        "utilities": [
            (source_dirs["robobuilder"] / "tools/analyze_encryption.py", "encryption_analyzer.py"),
            (source_dirs["robobuilder"] / "tools/analyze_special_tags.py", "tag_analyzer.py"),
            (source_dirs["evony_tools"] / "cleanup_backups.py", "cleanup.py"),
        ]
    }

    # Copy tools
    for category, tools in tool_mappings.items():
        dest_dir = tool_dirs[category]
        for src, dest_name in tools:
            if src.exists():
                dest_path = dest_dir / dest_name
                if src.is_dir():
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(src, dest_path)
                else:
                    shutil.copy2(src, dest_path)
                print(f"Copied {src.name} to {dest_path}")
            else:
                print(f"Warning: Source not found - {src}")

    # Create tool index
    index_content = "# RABCDAsm Tool Suite\n\n"
    for category, dir_path in tool_dirs.items():
        if dir_path.exists():
            index_content += f"\n## {category.replace('_', ' ').title()}\n\n"
            for item in dir_path.glob("*"):
                if item.is_file():
                    index_content += f"- {item.name}\n"
                elif item.is_dir():
                    index_content += f"- {item.name}/\n"

    with open(tools_dir / "TOOLS.md", "w") as f:
        f.write(index_content)

if __name__ == "__main__":
    setup_tools()
