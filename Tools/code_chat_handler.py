import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import tiktoken
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.token import Token
import autopep8

class CodeChunk:
    def __init__(self, code: str, start_line: int, language: str = "python"):
        self.code = code
        self.start_line = start_line
        self.language = language
        self.token_count = 0
        self.formatted_code = ""
        self.process_code()
    
    def process_code(self):
        """Format and process the code chunk"""
        if self.language == "python":
            # Auto-format Python code
            self.formatted_code = autopep8.fix_code(
                self.code,
                options={'aggressive': 1}
            )
        else:
            self.formatted_code = self.code
        
        # Count tokens
        enc = tiktoken.encoding_for_model("gpt-4")
        self.token_count = len(enc.encode(self.formatted_code))

class CodeChatManager:
    def __init__(self, max_chunk_size: int = 1000):
        self.max_chunk_size = max_chunk_size
        self.chunks: List[CodeChunk] = []
        self.current_chunk_index = 0
        self.html_formatter = HtmlFormatter(
            style='monokai',
            linenos=True,
            cssclass="source"
        )
        
    def process_code(self, code: str, language: str = "python") -> List[CodeChunk]:
        """Split code into manageable chunks"""
        self.chunks = []
        lines = code.split('\n')
        current_chunk = []
        current_line = 0
        chunk_start = 0
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            # Check if we should create a new chunk
            chunk_code = '\n'.join(current_chunk)
            enc = tiktoken.encoding_for_model("gpt-4")
            if len(enc.encode(chunk_code)) > self.max_chunk_size:
                # Find a good splitting point
                split_point = self.find_split_point(current_chunk)
                if split_point > 0:
                    # Create chunk up to split point
                    chunk_code = '\n'.join(current_chunk[:split_point])
                    self.chunks.append(CodeChunk(chunk_code, chunk_start, language))
                    # Start new chunk
                    current_chunk = current_chunk[split_point:]
                    chunk_start = i - len(current_chunk) + 1
        
        # Add final chunk
        if current_chunk:
            chunk_code = '\n'.join(current_chunk)
            self.chunks.append(CodeChunk(chunk_code, chunk_start, language))
        
        return self.chunks
    
    def find_split_point(self, lines: List[str]) -> int:
        """Find a good point to split the code chunk"""
        # Try to split at class/function definitions first
        for i, line in enumerate(reversed(lines)):
            if re.match(r'^\s*(class|def)\s+', line):
                return len(lines) - i - 1
        
        # Try to split at empty lines
        for i, line in enumerate(reversed(lines)):
            if not line.strip():
                return len(lines) - i - 1
        
        # If no good split point found, split at 80% of chunk
        return int(len(lines) * 0.8)
    
    def format_chunk_html(self, chunk: CodeChunk) -> str:
        """Format code chunk as HTML with syntax highlighting"""
        try:
            lexer = get_lexer_by_name(chunk.language)
        except:
            lexer = guess_lexer(chunk.formatted_code)
        
        highlighted = highlight(
            chunk.formatted_code,
            lexer,
            self.html_formatter
        )
        
        return f"""
        <div class="code-chunk" data-start-line="{chunk.start_line}">
            <div class="chunk-header">
                <span class="language">{chunk.language}</span>
                <span class="tokens">Tokens: {chunk.token_count}</span>
            </div>
            {highlighted}
        </div>
        """
    
    def get_chunk_css(self) -> str:
        """Get CSS for code chunks"""
        return f"""
        {self.html_formatter.get_style_defs('.source')}
        
        .code-chunk {{
            margin: 10px 0;
            border: 1px solid #4A90E2;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .chunk-header {{
            background: #1D2B3A;
            padding: 5px 10px;
            border-bottom: 1px solid #4A90E2;
            display: flex;
            justify-content: space-between;
        }}
        
        .language {{
            color: #FF6B00;
            font-weight: bold;
        }}
        
        .tokens {{
            color: #4A90E2;
        }}
        
        .source {{
            margin: 0 !important;
            padding: 10px;
            background: #1D2B3A !important;
        }}
        
        .source .linenos {{
            color: #4A90E2;
            border-right: 1px solid #4A90E2;
            padding-right: 10px;
            margin-right: 10px;
        }}
        """

class CodeAssistant:
    def __init__(self):
        self.code_manager = CodeChatManager()
        self.context: Dict[str, str] = {}
        self.current_file: Optional[str] = None
    
    def set_context(self, file_path: str, code: str):
        """Set current file context"""
        self.current_file = file_path
        self.context[file_path] = code
    
    def suggest_completion(self, code: str, cursor_pos: int) -> str:
        """Suggest code completion"""
        # TODO: Implement code completion using AI
        pass
    
    def format_code(self, code: str, language: str = "python") -> str:
        """Format code according to language standards"""
        if language == "python":
            return autopep8.fix_code(code, options={'aggressive': 1})
        return code
    
    def analyze_code(self, code: str) -> Dict:
        """Analyze code for potential issues"""
        # TODO: Implement code analysis
        pass
