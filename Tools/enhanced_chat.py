from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QTextEdit, QLineEdit, QComboBox, QLabel, QSplitter,
                            QTabWidget, QPlainTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCursor, QSyntaxHighlighter, QTextCharFormat, QColor
from ai_response_handler import AIResponseHandler
from code_chat_handler import CodeChatManager, CodeAssistant
import re

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1D2B3A;
                color: #E6E6E6;
                border: 1px solid #4A90E2;
                border-radius: 2px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        self.code_assistant = CodeAssistant()
        self.setup_auto_indent()
    
    def setup_auto_indent(self):
        """Setup auto-indentation"""
        self.textChanged.connect(self.handle_text_changed)
    
    def handle_text_changed(self):
        """Handle text changes for auto-indentation"""
        cursor = self.textCursor()
        current_line = cursor.block().text()
        
        # Auto-indent after colon
        if current_line.rstrip().endswith(':'):
            self.indent_next_line()
        
        # Maintain indentation on new line
        elif current_line.strip() == '':
            prev_line = cursor.block().previous().text()
            if prev_line:
                indent = len(prev_line) - len(prev_line.lstrip())
                cursor.insertText(' ' * indent)
    
    def indent_next_line(self):
        """Add indentation for the next line"""
        cursor = self.textCursor()
        current_line = cursor.block().text()
        indent = len(current_line) - len(current_line.lstrip())
        # Add 4 spaces for Python indentation
        cursor.insertText('\n' + ' ' * (indent + 4))
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Tab:
            # Insert 4 spaces instead of tab
            self.insertPlainText('    ')
        else:
            super().keyPressEvent(event)

class ChatDisplay(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.code_manager = CodeChatManager()
        self.document().setDefaultStyleSheet(self.code_manager.get_chunk_css())
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1D2B3A;
                color: #E6E6E6;
                border: 1px solid #4A90E2;
                border-radius: 2px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
        """)
    
    def append_message(self, sender: str, content: str, is_code: bool = False):
        """Append a message to the chat display"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Add sender info
        format = QTextCharFormat()
        if sender == "You":
            format.setForeground(QColor("#4A90E2"))
        elif sender == "Assistant":
            format.setForeground(QColor("#FF6B00"))
        else:
            format.setForeground(QColor("#E6E6E6"))
        
        cursor.insertText(f"{sender}: ", format)
        
        if is_code:
            # Process code through code manager
            chunks = self.code_manager.process_code(content)
            for chunk in chunks:
                html = self.code_manager.format_chunk_html(chunk)
                cursor.insertHtml(html)
        else:
            # Regular message
            format = QTextCharFormat()
            format.setForeground(QColor("#E6E6E6"))
            cursor.insertText(f"{content}\n", format)
        
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

class EnhancedChatWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.ai_handler = AIResponseHandler()
        self.code_assistant = CodeAssistant()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Chat area
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        
        # Chat display
        self.chat_display = ChatDisplay()
        chat_layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        # Text input with auto-completion
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #1D2B3A;
                color: #E6E6E6;
                border: 1px solid #4A90E2;
                border-radius: 2px;
                padding: 4px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        # Voice input button
        self.voice_button = QPushButton("🎤")
        self.voice_button.setStyleSheet("""
            QPushButton {
                background: #4A90E2;
                color: black;
                border: 1px solid #2A3F5A;
                border-radius: 2px;
                padding: 8px;
                font-size: 16px;
            }
            QPushButton:checked {
                background: #FF6B00;
            }
        """)
        self.voice_button.setCheckable(True)
        self.voice_button.clicked.connect(self.toggle_voice)
        input_layout.addWidget(self.voice_button)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF7B1C,
                    stop:1 #FF6B00);
                color: black;
                border: 1px solid #4A90E2;
                border-radius: 2px;
                padding: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF9B4C,
                    stop:1 #FF8533);
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        chat_layout.addLayout(input_layout)
        
        # Code editor tabs
        self.code_tabs = QTabWidget()
        self.code_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #4A90E2;
                background: #1D2B3A;
            }
            QTabBar::tab {
                background: #4A90E2;
                color: black;
                padding: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #FF6B00;
            }
        """)
        
        # Add initial code editor
        self.add_code_editor("main.py")
        
        # Add widgets to splitter
        splitter.addWidget(chat_widget)
        splitter.addWidget(self.code_tabs)
        
        # Set initial sizes
        splitter.setSizes([300, 200])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    def add_code_editor(self, name: str):
        """Add a new code editor tab"""
        editor = CodeEditor()
        self.code_tabs.addTab(editor, name)
    
    def send_message(self):
        """Send a message or code snippet"""
        text = self.input_field.text().strip()
        if not text:
            return
        
        # Check if it's a code snippet
        is_code = bool(re.match(r'^```.*', text) and re.search(r'```$', text))
        
        if is_code:
            # Extract code from markdown code block
            code = re.sub(r'^```.*\n|```$', '', text)
            self.chat_display.append_message("You", code, is_code=True)
            
            # Process code with AI
            response = self.ai_handler.get_ai_response(
                f"Please review and improve this code:\n{code}"
            )
            
            # Extract code from AI response
            code_match = re.search(r'```.*?\n(.*?)```', response, re.DOTALL)
            if code_match:
                improved_code = code_match.group(1)
                self.chat_display.append_message("Assistant", improved_code, is_code=True)
                
                # Add improved code to editor
                current_editor = self.code_tabs.currentWidget()
                if current_editor:
                    current_editor.setPlainText(improved_code)
            else:
                self.chat_display.append_message("Assistant", response)
        else:
            # Regular message
            self.chat_display.append_message("You", text)
            response = self.ai_handler.get_ai_response(text)
            self.chat_display.append_message("Assistant", response)
        
        self.input_field.clear()
    
    def toggle_voice(self, checked):
        """Toggle voice input"""
        # TODO: Implement voice recognition
        pass
