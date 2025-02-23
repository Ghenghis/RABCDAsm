from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QSlider, QProgressBar)
from PyQt6.QtCore import Qt, QTimer
import speech_recognition as sr

class MicSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Microphone Settings")
        self.setFixedSize(400, 300)
        self.init_ui()
        self.recognizer = sr.Recognizer()
        self.current_settings = {}

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Device selection
        device_layout = QHBoxLayout()
        device_label = QLabel("Microphone:")
        device_label.setStyleSheet("color: #4A90E2;")
        self.device_combo = QComboBox()
        self.device_combo.setStyleSheet("""
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
        self.populate_devices()
        device_layout.addWidget(device_label)
        device_layout.addWidget(self.device_combo)
        layout.addLayout(device_layout)
        
        # Sensitivity slider
        sensitivity_layout = QVBoxLayout()
        sensitivity_label = QLabel("Microphone Sensitivity:")
        sensitivity_label.setStyleSheet("color: #4A90E2;")
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setMinimum(0)
        self.sensitivity_slider.setMaximum(100)
        self.sensitivity_slider.setValue(50)
        self.sensitivity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #1D2B3A;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #FF6B00;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
        """)
        sensitivity_layout.addWidget(sensitivity_label)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        layout.addLayout(sensitivity_layout)
        
        # Volume meter
        meter_layout = QVBoxLayout()
        meter_label = QLabel("Input Level:")
        meter_label.setStyleSheet("color: #4A90E2;")
        self.volume_meter = QProgressBar()
        self.volume_meter.setStyleSheet("""
            QProgressBar {
                background-color: #1D2B3A;
                border: 1px solid #4A90E2;
                border-radius: 2px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #FF6B00;
                border-radius: 1px;
            }
        """)
        meter_layout.addWidget(meter_label)
        meter_layout.addWidget(self.volume_meter)
        layout.addLayout(meter_layout)
        
        # Test button
        test_layout = QHBoxLayout()
        self.test_button = QPushButton("Test Microphone")
        self.test_button.setStyleSheet("""
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
        self.test_button.clicked.connect(self.test_microphone)
        test_layout.addWidget(self.test_button)
        layout.addLayout(test_layout)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #4A90E2;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        apply_button.setStyleSheet("""
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
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
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
        apply_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_volume_meter)
        self.update_timer.start(100)

    def populate_devices(self):
        """Populate microphone devices"""
        self.device_combo.clear()
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            self.device_combo.addItem(name, index)

    def test_microphone(self):
        """Test microphone input"""
        try:
            device_index = self.device_combo.currentData()
            with sr.Microphone(device_index=device_index) as source:
                self.status_label.setText("Listening... Say something!")
                self.status_label.setStyleSheet("color: #FF6B00;")
                audio = self.recognizer.listen(source, timeout=3)
                self.status_label.setText("Processing...")
                
                try:
                    text = self.recognizer.recognize_google(audio)
                    self.status_label.setText(f"Heard: {text}")
                    self.status_label.setStyleSheet("color: #4A90E2;")
                except sr.UnknownValueError:
                    self.status_label.setText("Could not understand audio")
                    self.status_label.setStyleSheet("color: #FF0000;")
                except sr.RequestError:
                    self.status_label.setText("Could not reach recognition service")
                    self.status_label.setStyleSheet("color: #FF0000;")
                
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: #FF0000;")

    def update_volume_meter(self):
        """Update volume meter"""
        try:
            device_index = self.device_combo.currentData()
            with sr.Microphone(device_index=device_index) as source:
                level = self.recognizer.energy_threshold
                self.volume_meter.setValue(min(int(level / 10), 100))
        except:
            pass

    def get_settings(self):
        """Get current settings"""
        return {
            'device_index': self.device_combo.currentData(),
            'sensitivity': self.sensitivity_slider.value() * 10
        }
