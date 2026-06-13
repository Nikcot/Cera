# -*- coding: utf-8 -*-
"""
Тест загрузки в потоке
"""
import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit
from PyQt6.QtCore import QThread, pyqtSignal

class LoaderThread(QThread):
    error_signal = pyqtSignal(str)
    success_signal = pyqtSignal()
    
    def run(self):
        try:
            print("Thread started")
            from faster_whisper import WhisperModel
            print("Loading model...")
            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            print("Model loaded!")
            self.success_signal.emit()
        except Exception as e:
            error_text = f"ERROR: {str(e)}\n\nFull traceback:\n{traceback.format_exc()}"
            print(error_text)
            self.error_signal.emit(error_text)

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Model Loading")
        self.setGeometry(100, 100, 600, 400)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.button = QPushButton("Load Model")
        self.button.clicked.connect(self.load_model)
        
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        
        layout.addWidget(self.button)
        layout.addWidget(self.output)
        widget.setLayout(layout)
        self.setCentralWidget(widget)
    
    def load_model(self):
        self.output.append("Starting model load...")
        self.button.setEnabled(False)
        
        self.thread = LoaderThread()
        self.thread.success_signal.connect(self.on_success)
        self.thread.error_signal.connect(self.on_error)
        self.thread.start()
    
    def on_success(self):
        self.output.append("SUCCESS! Model loaded!")
        self.button.setEnabled(True)
    
    def on_error(self, error_text):
        self.output.append(error_text)
        self.button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
