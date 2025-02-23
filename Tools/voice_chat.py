import speech_recognition as sr
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTextEdit, QLineEdit, QComboBox, QLabel)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QDateTime
from PyQt6.QtGui import QIcon
import queue
import threading
import json
import re
from mic_settings import MicSettingsDialog
from ai_response_handler import AIResponseHandler

class VoiceRecognitionThread(QThread):
    text_received = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recognizer = sr.Recognizer()
        self.mic = None
        self.running = True
        self.paused = False
        
    def set_mic(self, device_index):
        self.mic = sr.Microphone(device_index=device_index)
        
    def run(self):
        while self.running:
            if not self.paused and self.mic:
                try:
                    with self.mic as source:
                        self.recognizer.adjust_for_ambient_noise(source)
                        audio = self.recognizer.listen(source)
                        text = self.recognizer.recognize_google(audio)
                        self.text_received.emit(text)
                except Exception as e:
                    print(f"Error in voice recognition: {str(e)}")
            self.msleep(100)
            
    def stop(self):
        self.running = False
        
    def pause(self):
        self.paused = True
        
    def resume(self):
        self.paused = False

class CommandProcessor:
    def __init__(self):
        self.commands = {
            r"open (ghidra|ida|binary ninja)": self.open_tool,
            r"switch to (static|dynamic|network)( tab)?": self.switch_tab,
            r"analyze( this)?( file)?": self.analyze_file,
            r"clear( (chat|output))?": self.clear_output
        }

    def process_command(self, text):
        text = text.lower()
        for pattern, handler in self.commands.items():
            match = re.match(pattern, text)
            if match:
                return handler(match.groups())
        return None

    def open_tool(self, groups):
        tool = groups[0]
        return {
            "action": "open_tool",
            "tool": tool
        }

    def switch_tab(self, groups):
        tab = groups[0]
        return {
            "action": "switch_tab",
            "tab": tab
        }

    def analyze_file(self, groups):
        return {
            "action": "analyze_file"
        }

    def clear_output(self, groups):
        target = groups[0].strip() if groups[0] else "output"
        return {
            "action": "clear",
            "target": target
        }

class ChatWidget(QWidget):
    command_received = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.voice_thread = VoiceRecognitionThread()
        self.voice_thread.text_received.connect(self.on_voice_input)
        self.ai_handler = AIResponseHandler()
        self.command_processor = CommandProcessor()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #1D2B3A;
                color: #E6E6E6;
                border: 1px solid #4A90E2;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #1D2B3A;
                color: #E6E6E6;
                border: 1px solid #4A90E2;
                border-radius: 2px;
                padding: 4px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
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
        
        # Voice control buttons
        self.voice_button = QPushButton("🎤")
        self.voice_button.setCheckable(True)
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
            QPushButton:hover {
                background: #5BA1E2;
            }
        """)
        self.voice_button.clicked.connect(self.toggle_voice)
        input_layout.addWidget(self.voice_button)
        
        # Settings button
        self.settings_button = QPushButton("⚙️")
        self.settings_button.setStyleSheet("""
            QPushButton {
                background: #4A90E2;
                color: black;
                border: 1px solid #2A3F5A;
                border-radius: 2px;
                padding: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #5BA1E2;
            }
        """)
        self.settings_button.clicked.connect(self.show_settings)
        input_layout.addWidget(self.settings_button)
        
        layout.addLayout(input_layout)
        
        # AI Model selection
        model_layout = QHBoxLayout()
        model_label = QLabel("AI Model:")
        model_label.setStyleSheet("color: #4A90E2;")
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229"
        ])
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #1D2B3A;
                color: #E6E6E6;
                border: 1px solid #4A90E2;
                border-radius: 2px;
                padding: 4px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        self.model_combo.currentTextChanged.connect(self.change_model)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        
        # Clear history button
        self.clear_button = QPushButton("Clear History")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background: #4A90E2;
                color: black;
                border: 1px solid #2A3F5A;
                border-radius: 2px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #5BA1E2;
            }
        """)
        self.clear_button.clicked.connect(self.clear_chat)
        model_layout.addWidget(self.clear_button)
        
        layout.addLayout(model_layout)
        
        self.setLayout(layout)
        
    def send_message(self):
        text = self.input_field.text().strip()
        if text:
            self.process_input(text)
            self.input_field.clear()
            
    def process_input(self, text):
        # Add user message to chat
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.chat_display.append(f"[{timestamp}] You: {text}")
        
        # Check if input is a command
        command = self.command_processor.process_command(text)
        if command:
            self.command_received.emit(command)
            self.add_message("System", f"🔵 Executing command: {command['action']}")
        else:
            # Get AI response
            response = self.ai_handler.get_ai_response(text)
            
            # Add AI response to chat
            timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
            self.chat_display.append(f"[{timestamp}] Assistant: {response}\n")
        
    def on_voice_input(self, text):
        if text:
            self.input_field.setText(text)
            self.send_message()
            
    def toggle_voice(self, checked):
        if checked:
            self.voice_thread.resume()
            if not self.voice_thread.isRunning():
                self.voice_thread.start()
        else:
            self.voice_thread.pause()
            
    def show_settings(self):
        dialog = MicSettingsDialog(self)
        if dialog.exec():
            settings = dialog.get_settings()
            self.voice_thread.recognizer.energy_threshold = settings['sensitivity']
            self.voice_thread.set_mic(settings['device_index'])
            
    def change_model(self, model_name):
        self.ai_handler.set_model(model_name)
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.chat_display.append(f"[{timestamp}] System: Switched to {model_name}\n")
        
    def clear_chat(self):
        self.chat_display.clear()
        self.ai_handler.clear_history()
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.chat_display.append(f"[{timestamp}] System: Chat history cleared\n")
        
    def add_message(self, sender, message):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        if sender == "System":
            self.chat_display.append(f"<span style='color: #4A90E2;'>[{timestamp}] {message}</span>")
        else:
            self.chat_display.append(f"<span style='color: #888;'>[{timestamp}]</span> <b>{sender}:</b> {message}")
        
    def closeEvent(self, event):
        self.voice_thread.stop()
        self.voice_thread.wait()
        super().closeEvent(event)
