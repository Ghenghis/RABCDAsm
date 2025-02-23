import sys
import os
from pathlib import Path
import subprocess
import hashlib
from typing import List, Dict, Optional, Tuple
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                            QFileDialog, QProgressBar, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import openai
import anthropic
from dotenv import load_dotenv

# Import our RABCDAsm wrapper
from rabcdasm_wrapper import RABCDAsmWrapper

class AIAnalysisThread(QThread):
    """Thread for running AI analysis without blocking GUI"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, model: str, api_key: str, content: str):
        super().__init__()
        self.model = model
        self.api_key = api_key
        self.content = content
        
    def run(self):
        try:
            if "gpt" in self.model.lower():
                response = self._run_openai()
            else:
                response = self._run_anthropic()
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))
            
    def _run_openai(self) -> str:
        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert in Flash SWF analysis and ActionScript. Help analyze and modify SWF files."},
                {"role": "user", "content": self.content}
            ]
        )
        return response.choices[0].message.content
        
    def _run_anthropic(self) -> str:
        client = anthropic.Client(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": self.content
            }]
        )
        return response.content

class SWFAnalyzer:
    """Handles SWF file analysis and modification"""
    
    def __init__(self, rabcdasm: RABCDAsmWrapper):
        self.rabcdasm = rabcdasm
        
    def analyze_swf(self, swf_path: str) -> Dict:
        """Analyze a SWF file and return its structure"""
        result = {
            'size': os.path.getsize(swf_path),
            'sha256': self._get_file_hash(swf_path),
            'abc_files': [],
            'resources': []
        }
        
        # Extract ABC files
        abc_files = self.rabcdasm.extract_abc(swf_path)
        result['abc_files'] = abc_files
        
        # Analyze each ABC file
        for abc_file in abc_files:
            asm_dir = self.rabcdasm.disassemble_abc(abc_file)
            result['resources'].extend(self._analyze_asm_dir(asm_dir))
            
        return result
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _analyze_asm_dir(self, asm_dir: str) -> List[Dict]:
        """Analyze disassembled ABC directory for resources"""
        resources = []
        for root, _, files in os.walk(asm_dir):
            for file in files:
                if file.endswith('.asasm'):
                    with open(os.path.join(root, file), 'r') as f:
                        content = f.read()
                        resources.append({
                            'name': file,
                            'type': 'ActionScript',
                            'path': os.path.join(root, file),
                            'size': len(content)
                        })
        return resources

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.rabcdasm = RABCDAsmWrapper()
        self.analyzer = SWFAnalyzer(self.rabcdasm)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle('AI-Powered RABCDAsm Interface')
        self.setMinimumSize(800, 600)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Add file selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        file_button = QPushButton("Select SWF File")
        file_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(file_button)
        layout.addLayout(file_layout)
        
        # Add AI model selection
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "GPT-4",
            "Claude-3-Sonnet",
            "Local-Ollama"
        ])
        model_layout.addWidget(QLabel("AI Model:"))
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)
        
        # Add operation buttons
        button_layout = QHBoxLayout()
        analyze_button = QPushButton("Analyze SWF")
        analyze_button.clicked.connect(self.analyze_swf)
        extract_button = QPushButton("Extract Resources")
        extract_button.clicked.connect(self.extract_resources)
        modify_button = QPushButton("Modify SWF")
        modify_button.clicked.connect(self.modify_swf)
        button_layout.addWidget(analyze_button)
        button_layout.addWidget(extract_button)
        button_layout.addWidget(modify_button)
        layout.addLayout(button_layout)
        
        # Add progress bar
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        # Add output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)
        
        # Add AI input/output
        self.ai_input = QTextEdit()
        self.ai_input.setPlaceholderText("Enter your question or command for the AI...")
        self.ai_input.setMaximumHeight(100)
        layout.addWidget(self.ai_input)
        
        ai_button = QPushButton("Ask AI")
        ai_button.clicked.connect(self.ask_ai)
        layout.addWidget(ai_button)
        
        # Load environment variables
        load_dotenv()
        
        self.current_file = None
        self.analysis_results = None
        
    def select_file(self):
        """Open file dialog to select SWF file"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select SWF File", "", "SWF Files (*.swf)")
        if file_name:
            self.current_file = file_name
            self.file_label.setText(os.path.basename(file_name))
            
    def analyze_swf(self):
        """Analyze the selected SWF file"""
        if not self.current_file:
            QMessageBox.warning(self, "Error", "Please select a SWF file first")
            return
            
        try:
            self.progress.setRange(0, 0)  # Indeterminate progress
            self.output.clear()
            
            # Run analysis
            results = self.analyzer.analyze_swf(self.current_file)
            self.analysis_results = results
            
            # Display results
            self.output.append("=== SWF Analysis Results ===")
            self.output.append(f"File size: {results['size']} bytes")
            self.output.append(f"SHA256: {results['sha256']}")
            self.output.append("\nABC Files:")
            for abc in results['abc_files']:
                self.output.append(f"- {os.path.basename(abc)}")
            self.output.append("\nResources:")
            for res in results['resources']:
                self.output.append(f"- {res['name']} ({res['type']})")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Analysis failed: {str(e)}")
        finally:
            self.progress.setRange(0, 100)
            self.progress.setValue(100)
            
    def extract_resources(self):
        """Extract resources from the SWF file"""
        if not self.current_file:
            QMessageBox.warning(self, "Error", "Please select a SWF file first")
            return
            
        try:
            output_dir = QFileDialog.getExistingDirectory(
                self, "Select Output Directory")
            if output_dir:
                self.progress.setRange(0, 0)
                
                # Extract ABC files
                abc_files = self.rabcdasm.extract_abc(self.current_file)
                
                # Disassemble each ABC file
                for abc_file in abc_files:
                    self.rabcdasm.disassemble_abc(abc_file)
                    
                self.output.append("\n=== Resource Extraction Complete ===")
                self.output.append(f"Resources extracted to: {output_dir}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Extraction failed: {str(e)}")
        finally:
            self.progress.setRange(0, 100)
            self.progress.setValue(100)
            
    def modify_swf(self):
        """Modify the SWF file based on AI suggestions"""
        if not self.current_file or not self.analysis_results:
            QMessageBox.warning(self, "Error", "Please analyze a SWF file first")
            return
            
        # TODO: Implement SWF modification based on AI suggestions
        pass
        
    def ask_ai(self):
        """Send user query to AI model"""
        if not self.current_file:
            QMessageBox.warning(self, "Error", "Please select a SWF file first")
            return
            
        model = self.model_combo.currentText()
        query = self.ai_input.toPlainText().strip()
        
        if not query:
            QMessageBox.warning(self, "Error", "Please enter a question or command")
            return
            
        # Prepare context for AI
        if self.analysis_results:
            context = f"""
            Analyzing SWF file: {self.current_file}
            File size: {self.analysis_results['size']} bytes
            Number of ABC files: {len(self.analysis_results['abc_files'])}
            Number of resources: {len(self.analysis_results['resources'])}
            
            User query: {query}
            """
        else:
            context = f"Analyzing SWF file: {self.current_file}\n\nUser query: {query}"
            
        # Get appropriate API key
        if "gpt" in model.lower():
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                QMessageBox.critical(self, "Error", "OpenAI API key not found in .env file")
                return
        else:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                QMessageBox.critical(self, "Error", "Anthropic API key not found in .env file")
                return
                
        # Start AI analysis thread
        self.progress.setRange(0, 0)
        self.ai_thread = AIAnalysisThread(model, api_key, context)
        self.ai_thread.finished.connect(self.handle_ai_response)
        self.ai_thread.error.connect(self.handle_ai_error)
        self.ai_thread.start()
        
    def handle_ai_response(self, response: str):
        """Handle AI analysis response"""
        self.output.append("\n=== AI Analysis ===")
        self.output.append(response)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        
    def handle_ai_error(self, error: str):
        """Handle AI analysis error"""
        QMessageBox.critical(self, "AI Error", f"AI analysis failed: {error}")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
