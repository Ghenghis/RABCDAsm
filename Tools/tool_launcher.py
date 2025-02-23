import os
import subprocess
from pathlib import Path
import json
import shutil

class ToolLauncher:
    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.dirname(__file__)))
        self.tools_dir = self.project_root / "Tools"
        self.load_tool_config()

    def load_tool_config(self):
        """Load tool configurations"""
        self.tools = {
            "ffdec": {
                "path": self.tools_dir / "ffdec_22.0.2" / "ffdec.bat",
                "type": "swf",
                "description": "FFDEC SWF Decompiler"
            },
            "rabcdasm": {
                "path": self.tools_dir / "RABCDAsm-1.18" / "rabcdasm.exe",
                "type": "abc",
                "description": "ABC Code Disassembler"
            },
            "ghidra": {
                "path": self.tools_dir / "ghidra_11.3" / "ghidraRun.bat",
                "type": "binary",
                "description": "Binary Analysis Platform"
            },
            "dnspy": {
                "path": self.tools_dir / "dnSpy64" / "dnSpy.exe",
                "type": "dotnet",
                "description": ".NET Debugger/Decompiler"
            },
            "resource_hacker": {
                "path": self.tools_dir / "resource_hacker" / "ResourceHacker.exe",
                "type": "resource",
                "description": "Resource Editor"
            },
            "sothink": {
                "path": self.tools_dir / "Sothink SWF Decompiler" / "Decompiler.exe",
                "type": "swf",
                "description": "SWF Decompiler"
            }
        }

    def get_tool_path(self, tool_name):
        """Get the path for a specific tool"""
        tool = self.tools.get(tool_name.lower())
        return tool["path"] if tool else None

    def is_tool_available(self, tool_name):
        """Check if a tool is available"""
        path = self.get_tool_path(tool_name)
        return path and path.exists()

    def launch_tool(self, tool_name, file_path=None):
        """Launch a specific tool"""
        path = self.get_tool_path(tool_name)
        if not path or not path.exists():
            return False, f"Tool not found: {tool_name}"

        try:
            cmd = [str(path)]
            if file_path:
                cmd.append(file_path)
            subprocess.Popen(cmd, cwd=str(path.parent))
            return True, f"Launched {tool_name}"
        except Exception as e:
            return False, f"Error launching {tool_name}: {str(e)}"

    def analyze_swf(self, swf_path):
        """Analyze a SWF file with multiple tools"""
        results = []
        
        # FFDEC Analysis
        if self.is_tool_available("ffdec"):
            cmd = [str(self.get_tool_path("ffdec")), "-export", "all", 
                   str(self.project_root / "extracted"), swf_path]
            results.append(("FFDEC", subprocess.run(cmd, capture_output=True)))

        # RABCDAsm Analysis
        if self.is_tool_available("rabcdasm"):
            cmd = [str(self.get_tool_path("rabcdasm")), swf_path]
            results.append(("RABCDAsm", subprocess.run(cmd, capture_output=True)))

        return results

    def extract_resources(self, file_path):
        """Extract resources from a file"""
        if self.is_tool_available("resource_hacker"):
            output_dir = self.project_root / "resources"
            output_dir.mkdir(exist_ok=True)
            cmd = [
                str(self.get_tool_path("resource_hacker")),
                "-open", file_path,
                "-save", str(output_dir / "resources.res"),
                "-action", "extract"
            ]
            return subprocess.run(cmd, capture_output=True)
        return None

    def get_available_tools(self):
        """Get list of available tools"""
        return {name: info for name, info in self.tools.items() 
                if self.is_tool_path(name)}

    def get_tools_for_file(self, file_path):
        """Get suitable tools for a file type"""
        ext = Path(file_path).suffix.lower()
        suitable_tools = []
        
        ext_map = {
            ".swf": ["ffdec", "sothink", "rabcdasm"],
            ".exe": ["ghidra", "resource_hacker"],
            ".dll": ["ghidra", "resource_hacker", "dnspy"],
            ".abc": ["rabcdasm"],
            ".class": ["ghidra", "dnspy"]
        }
        
        return [tool for tool in ext_map.get(ext, []) 
                if self.is_tool_available(tool)]

def main():
    launcher = ToolLauncher()
    
    # Example usage
    print("Available Tools:")
    for name, info in launcher.tools.items():
        status = "✓" if launcher.is_tool_available(name) else "✗"
        print(f"{status} {name}: {info['description']}")

if __name__ == "__main__":
    main()
