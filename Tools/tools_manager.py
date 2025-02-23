import os
import subprocess
import json
from pathlib import Path

class ToolManager:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.tools_dir = self.project_root / "Tools"
        self.config_file = self.tools_dir / "tools_config.json"
        self.load_config()

    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "tools": {
                    "ghidra": {
                        "path": str(self.tools_dir / "ghidra_11.3"),
                        "version": "11.3",
                        "launch_script": "ghidraRun.bat",
                        "file_types": [".exe", ".dll", ".bin", ".so"],
                        "installed": False
                    },
                    "ida": {
                        "path": str(self.tools_dir / "ida_pro"),
                        "version": "8.3",
                        "launch_script": "ida64.exe",
                        "file_types": [".exe", ".dll", ".bin", ".so"],
                        "installed": False
                    },
                    "binary_ninja": {
                        "path": str(self.tools_dir / "binary_ninja"),
                        "version": "3.5",
                        "launch_script": "binaryninja.exe",
                        "file_types": [".exe", ".dll", ".bin", ".so"],
                        "installed": False
                    },
                    "rabcdasm": {
                        "path": str(self.tools_dir / "rabcdasm"),
                        "version": "1.18",
                        "launch_script": "rabcdasm.exe",
                        "file_types": [".abc", ".swf"],
                        "installed": True
                    },
                    "ffdec": {
                        "path": str(self.tools_dir / "ffdec_22.0.2"),
                        "version": "22.0.2",
                        "launch_script": "ffdec.bat",
                        "file_types": [".swf"],
                        "installed": True
                    },
                    "resource_hacker": {
                        "path": str(self.tools_dir / "resource_hacker"),
                        "version": "5.1.8",
                        "launch_script": "ResourceHacker.exe",
                        "file_types": [".exe", ".dll", ".res"],
                        "installed": True
                    }
                }
            }
            self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_tool_path(self, tool_name):
        tool = self.config["tools"].get(tool_name.lower())
        if tool and tool["installed"]:
            return Path(tool["path"]) / tool["launch_script"]
        return None

    def is_tool_installed(self, tool_name):
        tool = self.config["tools"].get(tool_name.lower())
        return tool and tool["installed"]

    def get_supported_tools_for_file(self, file_path):
        file_ext = Path(file_path).suffix.lower()
        supported_tools = []
        for tool_name, tool in self.config["tools"].items():
            if tool["installed"] and file_ext in tool["file_types"]:
                supported_tools.append(tool_name)
        return supported_tools

    def launch_tool(self, tool_name, file_path=None):
        tool_path = self.get_tool_path(tool_name)
        if not tool_path:
            return False, f"{tool_name} is not installed"

        try:
            cmd = [str(tool_path)]
            if file_path:
                cmd.append(file_path)
            subprocess.Popen(cmd, cwd=str(tool_path.parent))
            return True, f"Launched {tool_name}"
        except Exception as e:
            return False, f"Error launching {tool_name}: {str(e)}"

    def get_tool_info(self, tool_name):
        return self.config["tools"].get(tool_name.lower())
