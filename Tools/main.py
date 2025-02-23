import os
import sys
import subprocess
import shutil
from PyQt6.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                           QMessageBox, QSplitter, QFrame, QLineEdit)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RABCDAsm Interface")
        self.setMinimumSize(1200, 800)
        
        # Set up paths
        try:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.tools_dir = os.path.join(self.base_dir, "Tools")
            
            # Create required directories
            self.create_required_directories()
            
            # Initialize UI
            self.setup_ui()
            
            # Log startup info
            self.log_output("System: ⚫ Application started")
            self.log_output(f"System: ⚫ Base directory: {self.base_dir}")
            self.log_output(f"System: ⚫ Tools directory: {self.tools_dir}")
            
        except Exception as e:
            print(f"Error initializing: {str(e)}")
            QMessageBox.critical(self, "Initialization Error", f"Error initializing application: {str(e)}")
            raise

    def create_required_directories(self):
        """Create all required directories"""
        try:
            # Create main directories
            dirs = [
                os.path.join(self.base_dir, "output"),
                os.path.join(self.tools_dir, "ffdec_22.0.2"),
                os.path.join(self.tools_dir, "ghidra_11.3"),
                os.path.join(self.tools_dir, "RABCDAsm-bin")
            ]
            
            for dir_path in dirs:
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                    self.log_output(f"System: ⚫ Created directory: {dir_path}")
            
            # Check for RABCDAsm tools
            self.check_rabcdasm_setup()
                    
        except Exception as e:
            print(f"Error creating directories: {str(e)}")
            raise

    def check_rabcdasm_setup(self):
        """Check and setup RABCDAsm tools"""
        try:
            rabcdasm_bin = os.path.join(self.tools_dir, "RABCDAsm-bin")
            rabcdasm_source = os.path.join(self.tools_dir, "RABCDAsm-1.18")
            
            # Check if binaries exist
            required_tools = ["rabcdasm.exe", "abcexport.exe", "abcreplace.exe", "rabcasm.exe"]
            missing_tools = []
            
            for tool in required_tools:
                if not os.path.exists(os.path.join(rabcdasm_bin, tool)):
                    missing_tools.append(tool)
            
            if missing_tools:
                self.log_output("System: ⚫ Some RABCDAsm tools are missing. Building from source...")
                
                # Check if source exists
                if not os.path.exists(rabcdasm_source):
                    self.log_output("System: ⚫ RABCDAsm source not found. Please download it first.")
                    QMessageBox.warning(self, "Setup Required", 
                        "RABCDAsm source code not found. Please download RABCDAsm-1.18 and extract it to Tools/RABCDAsm-1.18")
                    return
                
                # Run build script
                build_script = os.path.join(self.tools_dir, "build_rabcdasm.bat")
                if os.path.exists(build_script):
                    self.log_output("System: ⚫ Running build script...")
                    try:
                        subprocess.run([build_script], cwd=self.tools_dir, check=True)
                        self.log_output("System: ⚫ RABCDAsm tools built successfully")
                    except subprocess.CalledProcessError as e:
                        self.log_output(f"System: ⚫ Error building RABCDAsm: {str(e)}")
                        QMessageBox.warning(self, "Build Error", 
                            "Failed to build RABCDAsm tools. Please ensure DMD compiler is installed.")
                else:
                    self.log_output("System: ⚫ Build script not found")
                    QMessageBox.warning(self, "Setup Required", "RABCDAsm build script not found")
            else:
                self.log_output("System: ⚫ RABCDAsm tools are ready")
                
        except Exception as e:
            self.log_output(f"System: ⚫ Error checking RABCDAsm setup: {str(e)}")

    def setup_ui(self):
        try:
            # Create main widget and layout
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            main_layout = QHBoxLayout(main_widget)
            
            # Create splitter for tools panel and chat/output
            splitter = QSplitter(Qt.Orientation.Horizontal)
            main_layout.addWidget(splitter)
            
            # Left panel - Tools
            tools_panel = QWidget()
            tools_layout = QVBoxLayout(tools_panel)
            tools_layout.setSpacing(10)
            
            # Style for tool panels
            tool_panel_style = """
                QFrame {
                    background-color: #2A3F5A;
                    border-radius: 8px;
                    padding: 10px;
                }
            """
            
            # Tool configurations
            self.categories = {
                "Flash Analysis": [
                    ("FFDEC", {
                        "name": "FFDEC",
                        "path": os.path.join(self.tools_dir, "ffdec_22.0.2", "ffdec.bat"),
                        "type": "bat",
                        "args": [],
                        "description": "Flash Decompiler tool for analyzing SWF files"
                    }),
                    ("RABCDAsm", {
                        "name": "RABCDAsm",
                        "path": os.path.join(self.tools_dir, "RABCDAsm-bin", "rabcdasm.exe"),
                        "type": "exe",
                        "args": [],
                        "description": "ActionScript Bytecode Disassembler"
                    }),
                    ("Extract ABC", {
                        "name": "ABC Extractor",
                        "path": os.path.join(self.tools_dir, "RABCDAsm-bin", "abcexport.exe"),
                        "type": "exe",
                        "args": [],
                        "description": "Extract ABC (ActionScript Byte Code) from SWF files"
                    })
                ],
                "Binary Analysis": [
                    ("Ghidra", {
                        "name": "Ghidra",
                        "path": os.path.join(self.tools_dir, "ghidra_11.3", "ghidraRun.bat"),
                        "type": "bat",
                        "args": [],
                        "requires": ["java"],
                        "description": "Software reverse engineering framework"
                    })
                ]
            }

            # Create tool buttons by category
            for category_name, tools in self.categories.items():
                # Category panel
                category_panel = QFrame()
                category_panel.setStyleSheet(tool_panel_style)
                category_layout = QVBoxLayout(category_panel)
                
                # Category header
                header = QLabel(category_name)
                header.setStyleSheet("""
                    QLabel {
                        color: #E6E6E6;
                        font-weight: bold;
                        font-size: 16px;
                        padding: 5px;
                        border-bottom: 1px solid #4A90E2;
                    }
                """)
                category_layout.addWidget(header)
                
                for tool_id, tool_config in tools:
                    # Tool container
                    tool_container = QWidget()
                    tool_container_layout = QVBoxLayout(tool_container)
                    tool_container_layout.setSpacing(5)
                    
                    # Tool button
                    btn = QPushButton(tool_config["name"])
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #FF6B00;
                            color: black;
                            border: none;
                            padding: 12px;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 13px;
                            margin: 2px 5px;
                        }
                        QPushButton:hover {
                            background-color: #FF8533;
                        }
                        QPushButton:pressed {
                            background-color: #E65D00;
                        }
                    """)
                    btn.setProperty("tool_config", tool_config)
                    btn.clicked.connect(self.on_tool_button_clicked)
                    
                    # Tool description
                    if "description" in tool_config:
                        desc_label = QLabel(tool_config["description"])
                        desc_label.setStyleSheet("""
                            QLabel {
                                color: #B0B0B0;
                                font-size: 11px;
                                padding: 2px 5px;
                            }
                        """)
                        desc_label.setWordWrap(True)
                        tool_container_layout.addWidget(desc_label)
                    
                    tool_container_layout.addWidget(btn)
                    category_layout.addWidget(tool_container)
                
                tools_layout.addWidget(category_panel)
            
            # Add stretch to push everything up
            tools_layout.addStretch()
            
            # Right panel - Chat and Output
            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)
            
            # Chat input area
            chat_input = QLineEdit()
            chat_input.setPlaceholderText("Ask AI for help (e.g., 'Analyze this SWF file')")
            chat_input.setStyleSheet("""
                QLineEdit {
                    background-color: #1D2B3A;
                    color: #E6E6E6;
                    border: 1px solid #4A90E2;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 13px;
                }
            """)
            chat_input.returnPressed.connect(self.on_chat_input)
            
            # Chat/Output area
            self.output_text = QTextEdit()
            self.output_text.setReadOnly(True)
            self.output_text.setStyleSheet("""
                QTextEdit {
                    background-color: #1D2B3A;
                    color: #E6E6E6;
                    border: none;
                    font-family: Consolas, monospace;
                    font-size: 12px;
                    padding: 10px;
                }
            """)
            
            # Add widgets to right panel
            right_layout.addWidget(chat_input)
            right_layout.addWidget(self.output_text)
            
            # Add panels to splitter
            splitter.addWidget(tools_panel)
            splitter.addWidget(right_panel)
            
            # Set initial splitter sizes (30% tools, 70% chat/output)
            splitter.setSizes([int(self.width() * 0.3), int(self.width() * 0.7)])
            
        except Exception as e:
            print(f"Error setting up UI: {str(e)}")
            QMessageBox.critical(self, "UI Error", f"Error setting up UI: {str(e)}")
            raise

    def on_chat_input(self):
        """Handle chat input"""
        try:
            chat_input = self.sender()
            if chat_input and chat_input.text():
                user_input = chat_input.text()
                self.log_output(f"User: {user_input}")
                
                # Process AI commands
                if "analyze" in user_input.lower() and "swf" in user_input.lower():
                    self.log_output("AI: I'll help you analyze the SWF file. Let me run the appropriate tools:")
                    self.run_swf_analysis_workflow()
                elif "extract" in user_input.lower() and "abc" in user_input.lower():
                    self.log_output("AI: I'll help you extract the ABC code. Running the extraction tools:")
                    self.run_abc_extraction_workflow()
                else:
                    self.log_output("AI: I can help you with the following tasks:")
                    self.log_output("  - Analyze SWF files")
                    self.log_output("  - Extract ABC code")
                    self.log_output("  - Decompile Flash files")
                    self.log_output("  - Reverse engineer binaries")
                    self.log_output("Just let me know what you'd like to do!")
                
                chat_input.clear()
        except Exception as e:
            self.log_output(f"System: ⚫ Error processing chat: {str(e)}")

    def run_swf_analysis_workflow(self):
        """Run the SWF analysis workflow"""
        try:
            # Launch FFDEC for initial analysis
            self.launch_tool(self.categories["Flash Analysis"][0][1])  # FFDEC
            self.log_output("AI: Launched FFDEC for SWF analysis")
            self.log_output("AI: After examining the SWF, I can help you extract specific components")
        except Exception as e:
            self.log_output(f"System: ⚫ Error in SWF analysis workflow: {str(e)}")

    def run_abc_extraction_workflow(self):
        """Run the ABC extraction workflow"""
        try:
            # Launch ABC Extractor
            self.launch_tool(self.categories["Flash Analysis"][2][1])  # ABC Extractor
            self.log_output("AI: Launched ABC Extractor")
            self.log_output("AI: After extraction, we can analyze the bytecode with RABCDAsm")
        except Exception as e:
            self.log_output(f"System: ⚫ Error in ABC extraction workflow: {str(e)}")

    def on_tool_button_clicked(self):
        """Handle tool button clicks"""
        try:
            button = self.sender()
            if button:
                tool_config = button.property("tool_config")
                if tool_config:
                    self.launch_tool(tool_config)
        except Exception as e:
            self.log_output(f"System: ⚫ Error handling button click: {str(e)}")
            QMessageBox.warning(self, "Tool Error", f"Error launching tool: {str(e)}")

    def log_output(self, message):
        """Add message to output text area"""
        try:
            if hasattr(self, 'output_text'):
                self.output_text.append(message)
                # Scroll to bottom
                scrollbar = self.output_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            print(f"Error logging output: {str(e)}")

    def launch_tool(self, tool_config):
        """Launch a tool based on its configuration"""
        try:
            tool_name = tool_config["name"]
            tool_path = tool_config["path"]
            tool_type = tool_config["type"]
            tool_args = tool_config["args"]
            tool_dir = os.path.dirname(tool_path)

            # Debug info
            self.log_output(f"System: ⚫ Attempting to launch {tool_name}")
            self.log_output(f"System: ⚫ Path: {tool_path}")
            self.log_output(f"System: ⚫ Working Dir: {tool_dir}")

            # Check dependencies
            if "requires" in tool_config:
                for req in tool_config["requires"]:
                    if req == "java":
                        # Set JAVA_HOME to JDK 23 path
                        java_home = r"C:\Program Files\Java\jdk-23"
                        if os.path.exists(java_home):
                            os.environ["JAVA_HOME"] = java_home
                            self.log_output(f"System: ⚫ Set JAVA_HOME to {java_home}")
                            
                            # Add Java to PATH
                            java_bin = os.path.join(java_home, "bin")
                            if java_bin not in os.environ["PATH"]:
                                os.environ["PATH"] = f"{java_bin};{os.environ['PATH']}"
                                self.log_output(f"System: ⚫ Added Java bin to PATH: {java_bin}")
                        else:
                            self.log_output("System: ⚫ Error: Java path not found")
                            self.log_output("System: ⚫ Please ensure JDK 23 is installed at the correct path")
                            QMessageBox.warning(self, "Java Error", "Java JDK 23 not found. Please ensure it is installed correctly.")
                            return

            if not os.path.exists(tool_path):
                error_msg = f"{tool_name} not found at {tool_path}"
                self.log_output(f"System: ⚫ Error: {error_msg}")
                QMessageBox.warning(self, "Tool Not Found", error_msg)
                return

            # Launch the tool
            try:
                if tool_type == "exe":
                    process = subprocess.Popen([tool_path] + tool_args, cwd=tool_dir)
                elif tool_type == "bat":
                    process = subprocess.Popen([tool_path] + tool_args, cwd=tool_dir, shell=True)
                self.log_output(f"System: ⚫ Launched {tool_name} with PID {process.pid}")
            except Exception as e:
                error_msg = f"Failed to launch {tool_name}: {str(e)}"
                self.log_output(f"System: ⚫ Error: {error_msg}")
                QMessageBox.critical(self, "Launch Error", error_msg)

        except Exception as e:
            self.log_output(f"System: ⚫ Error launching {tool_name}: {str(e)}")
            import traceback
            self.log_output(f"System: ⚫ Stack trace: {traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"Error launching {tool_name}: {str(e)}")

def main():
    try:
        app = QApplication(sys.argv)
        
        # Set application style
        app.setStyle("Fusion")
        
        window = MainWindow()
        window.show()
        return app.exec()
    except Exception as e:
        print(f"Error in main: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
