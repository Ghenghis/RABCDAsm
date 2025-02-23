import subprocess
import os
import shutil
from typing import List, Optional
from pathlib import Path

class RABCDAsmWrapper:
    """
    A Python wrapper for RABCDAsm operations on SWF files.
    Provides high-level interface for common SWF manipulation tasks.
    """
    
    def __init__(self, rabcdasm_path: str = ""):
        """
        Initialize the wrapper with path to RABCDAsm executables.
        
        Args:
            rabcdasm_path: Directory containing RABCDAsm executables. If empty,
                          assumes executables are in system PATH.
        """
        self.rabcdasm_path = Path(rabcdasm_path) if rabcdasm_path else Path("")
        self._validate_installation()

    def _validate_installation(self) -> None:
        """Verify that required RABCDAsm executables are available."""
        required_executables = ['rabcdasm', 'rabcasm', 'abcexport', 'abcreplace', 
                              'swfdecompress', 'swfbinexport']
        
        for exe in required_executables:
            exe_path = self.rabcdasm_path / exe
            if not self._is_executable_available(exe_path):
                raise RuntimeError(f"Required executable '{exe}' not found in {self.rabcdasm_path}")

    def _is_executable_available(self, exe_path: Path) -> bool:
        """Check if an executable is available either in specified path or system PATH."""
        if exe_path.parent != Path(""):
            return exe_path.exists()
        try:
            subprocess.run([exe_path.name, '--help'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         check=False)
            return True
        except FileNotFoundError:
            return False

    def _run_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """Execute a command and handle errors."""
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Command failed: {' '.join(command)}\nError: {e.stderr}")

    def extract_abc(self, swf_path: str) -> List[str]:
        """
        Extract ABC blocks from a SWF file.
        
        Args:
            swf_path: Path to the SWF file
            
        Returns:
            List of paths to extracted ABC files
        """
        command = [str(self.rabcdasm_path / 'abcexport'), swf_path]
        self._run_command(command)
        
        # Get list of generated ABC files
        base_name = Path(swf_path).stem
        abc_files = list(Path(swf_path).parent.glob(f"{base_name}-*.abc"))
        return [str(f) for f in abc_files]

    def disassemble_abc(self, abc_path: str) -> str:
        """
        Disassemble an ABC file to ASM.
        
        Args:
            abc_path: Path to the ABC file
            
        Returns:
            Path to the directory containing disassembled files
        """
        command = [str(self.rabcdasm_path / 'rabcdasm'), abc_path]
        self._run_command(command)
        
        # Return path to generated directory
        output_dir = str(Path(abc_path).with_suffix(''))
        return output_dir

    def assemble_abc(self, asasm_path: str) -> str:
        """
        Assemble an ASM file back to ABC.
        
        Args:
            asasm_path: Path to the main .asasm file
            
        Returns:
            Path to the generated ABC file
        """
        command = [str(self.rabcdasm_path / 'rabcasm'), asasm_path]
        self._run_command(command)
        
        # Return path to generated ABC file
        return str(Path(asasm_path).with_suffix('.abc'))

    def replace_abc(self, swf_path: str, abc_index: int, abc_path: str) -> None:
        """
        Replace an ABC block in a SWF file.
        
        Args:
            swf_path: Path to the SWF file
            abc_index: Index of the ABC block to replace
            abc_path: Path to the new ABC file
        """
        command = [
            str(self.rabcdasm_path / 'abcreplace'),
            swf_path,
            str(abc_index),
            abc_path
        ]
        self._run_command(command)

    def decompress_swf(self, swf_path: str) -> str:
        """
        Decompress a zlib-compressed SWF file.
        
        Args:
            swf_path: Path to the compressed SWF file
            
        Returns:
            Path to the decompressed SWF file
        """
        command = [str(self.rabcdasm_path / 'swfdecompress'), swf_path]
        self._run_command(command)
        
        # Return path to decompressed file
        output_path = str(Path(swf_path).with_suffix('.decompressed.swf'))
        return output_path

    def extract_binary_data(self, swf_path: str) -> List[str]:
        """
        Extract binary data tags from a SWF file.
        
        Args:
            swf_path: Path to the SWF file
            
        Returns:
            List of paths to extracted binary data files
        """
        command = [str(self.rabcdasm_path / 'swfbinexport'), swf_path]
        self._run_command(command)
        
        # Get list of generated bin files
        base_name = Path(swf_path).stem
        bin_files = list(Path(swf_path).parent.glob(f"{base_name}-*.bin"))
        return [str(f) for f in bin_files]

    def modify_actionscript(self, swf_path: str, modification_func) -> None:
        """
        Modify ActionScript code in a SWF file using a custom function.
        
        Args:
            swf_path: Path to the SWF file
            modification_func: Function that takes the path to a .asasm file
                             and modifies it as needed
        """
        # Extract ABC blocks
        abc_files = self.extract_abc(swf_path)
        
        for i, abc_file in enumerate(abc_files):
            # Disassemble each ABC block
            asm_dir = self.disassemble_abc(abc_file)
            main_asm = Path(asm_dir) / f"{Path(abc_file).stem}.main.asasm"
            
            # Apply modifications
            modification_func(str(main_asm))
            
            # Reassemble and replace
            new_abc = self.assemble_abc(str(main_asm))
            self.replace_abc(swf_path, i, new_abc)

def example_usage():
    """Example of how to use the RABCDAsm wrapper."""
    # Initialize wrapper
    rabcdasm = RABCDAsmWrapper()
    
    # Example modification function
    def modify_hello_world(asasm_path: str):
        with open(asasm_path, 'r') as f:
            content = f.read()
        
        # Example: Replace "Hello World" with "Modified Hello World"
        modified = content.replace('"Hello World"', '"Modified Hello World"')
        
        with open(asasm_path, 'w') as f:
            f.write(modified)
    
    # Modify a SWF file
    rabcdasm.modify_actionscript("example.swf", modify_hello_world)

if __name__ == "__main__":
    example_usage()
