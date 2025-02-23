# RABCDAsm

RABCDAsm is a collection of utilities for working with ActionScript 3 bytecode, including an assembler/disassembler and tools for manipulating SWF files.

## Features

- Parse and manipulate ABC (ActionScript Byte Code) files
- Extract and modify SWF file contents
- Assemble and disassemble ActionScript 3 bytecode
- Python API for programmatic access to all features

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from rabcdasm import ABCFile, SWFFile, Assembler

# Load and parse a SWF file
swf = SWFFile()
swf.load('example.swf')

# Extract ABC blocks
abc_blocks = swf.extract_abc()

# Parse ABC file
abc = ABCFile()
abc.load('script.abc')

# Assemble ActionScript
assembler = Assembler()
bytecode = assembler.assemble('script.asasm')
```

### Command Line Interface

```bash
# Extract ABC from SWF
python -m rabcdasm extract example.swf

# Disassemble ABC file
python -m rabcdasm disassemble script.abc

# Assemble ABC file
python -m rabcdasm assemble script.asasm
```

## Documentation

The syntax of the disassembly is designed to be simple and allow fast and easy parsing. It closely represents the ABC file format while remaining human-readable.

### Key Concepts

- **ABC File Format**: The compiled bytecode format for ActionScript 3
- **SWF File Format**: The container format for Flash content
- **Assembly Syntax**: A human-readable representation of ABC bytecode

For more details, see the [AVM2 Overview](https://www.adobe.com/content/dam/acom/en/devnet/pdf/avm2overview.pdf).

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -am 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Adobe's AVM2 Overview documentation
- The Flash/ActionScript community
