from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rabcdasm",
    version="1.0.0",
    author="Codeium",
    author_email="support@codeium.com",
    description="ActionScript 3 Assembler/Disassembler",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/codeium/rabcdasm",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Assemblers",
        "Topic :: Software Development :: Disassemblers",
    ],
    python_requires=">=3.10",
    install_requires=[
        "PyQt6>=6.4.0",
        "openai>=1.0.0",
        "anthropic>=0.8.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "openrouter>=0.3.0",
        "PyQt6-QScintilla>=2.14.1",
        "watchdog>=3.0.0",
        "pytest>=8.0.0",
        "dataclasses;python_version<'3.7'",
    ],
    entry_points={
        "console_scripts": [
            "rabcdasm=rabcdasm.__main__:main",
        ],
    },
)
