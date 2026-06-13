# -*- coding: utf-8 -*-
"""
Тест с записью в файл
"""
import sys
import traceback

# Перенаправляем все ошибки в файл
error_file = open("error_log.txt", "w", encoding="utf-8")
sys.stderr = error_file
sys.stdout = error_file

try:
    print("=== STARTING TEST ===")
    print("Importing PyQt6...")
    from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit
    from PyQt6.QtCore import QThread, pyqtSignal
    print("PyQt6 imported OK")
    
    class LoaderThread(QThread):
        error_signal = pyqtSignal(str)
        success_signal = pyqtSignal()
        
        def run(self):
            try:
                print("Thread started")
                from faster_whisper import WhisperModel
                print("Importing WhisperModel OK")
                print("Loading model tiny...")
                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                print("Model loaded!")
                self.success_signal.emit()
            except Exception as e:
                error_text = f"ERROR IN THREAD: {str(e)}\n\nFull traceback:\n{traceback.format_exc()}"
                print(error_text)
                self.error_signal.emit(error_text)

    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            print("Creating window...")
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
            print("Window created OK")
        
        def load_model(self):
            print("Button clicked!")
            self.output.append("Starting model load...")
            self.button.setEnabled(False)
            
            print("Creating thread...")
            self.thread = LoaderThread()
            self.thread.success_signal.connect(self.on_success)
            self.thread.error_signal.connect(self.on_error)
            print("Starting thread...")
            self.thread.start()
            print("Thread started!")
        
        def on_success(self):
            print("SUCCESS callback")
            self.output.append("SUCCESS! Model loaded!")
            self.button.setEnabled(True)
        
        def on_error(self, error_text):
            print(f"ERROR callback: {error_text}")
            self.output.append(error_text)
            self.button.setEnabled(True)

    print("Creating QApplication...")
    app = QApplication(sys.argv)
    print("Creating window...")
    window = TestWindow()
    print("Showing window...")
    window.show()
    print("Starting event loop...")
    sys.exit(app.exec())
    
except Exception as e:
    print(f"\n\n=== FATAL ERROR ===")
    print(f"Error: {str(e)}")
    print(f"\nFull traceback:")
    traceback.print_exc()
    print("=== END ERROR ===")
finally:
    error_file.close()
