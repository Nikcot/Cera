"""
Цера - Desktop приложение для транскрибации и AI-саммари
"""

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                             QRadioButton, QButtonGroup, QComboBox, QGroupBox,
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
import time
import os

from transcriber_engine import TranscriberEngine
from exporter import NotesExporter
from gemini_api import GeminiAPI
from config import GEMINI_API_KEY


class TranscriberThread(QThread):
    """Поток для транскрибации в фоне"""
    transcription_ready = pyqtSignal(str, str)  # timestamp, text
    
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.is_running = False
    
    def run(self):
        """Запуск транскрибации"""
        self.is_running = True
        self.engine.start_recording()
    
    def stop(self):
        """Остановка транскрибации"""
        self.is_running = False
        if self.engine:
            self.engine.stop_recording()


class CeraMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.transcriber_thread = None
        self.is_recording = False
        self.accumulated_text = ""  # Накопленный текст для отправки в Gemini
        self.last_gemini_time = 0
        self.engine = None  # Движок будет создан при старте записи
        
        # Инициализация Gemini API
        try:
            self.gemini = GeminiAPI(GEMINI_API_KEY)
            print("Gemini API initialized")
        except Exception as e:
            print(f"Gemini initialization error: {e}")
            self.gemini = None
        
        self.init_ui()
        self.apply_dark_theme()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("🧠 Цера")
        self.setGeometry(100, 100, 900, 700)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # === Настройки ===
        settings_group = QGroupBox("Настройки")
        settings_layout = QVBoxLayout()
        
        # Выбор источника звука
        audio_source_layout = QHBoxLayout()
        audio_source_label = QLabel("Источник звука:")
        audio_source_label.setFont(QFont("Segoe UI", 10))
        
        self.source_group = QButtonGroup()
        self.radio_system = QRadioButton("Системный звук")
        self.radio_mic = QRadioButton("Микрофон")
        self.radio_system.setChecked(True)
        
        self.source_group.addButton(self.radio_system)
        self.source_group.addButton(self.radio_mic)
        
        audio_source_layout.addWidget(audio_source_label)
        audio_source_layout.addWidget(self.radio_system)
        audio_source_layout.addWidget(self.radio_mic)
        audio_source_layout.addStretch()
        
        # Выбор модели
        model_layout = QHBoxLayout()
        model_label = QLabel("Модель:")
        model_label.setFont(QFont("Segoe UI", 10))
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Tiny (быстрая)", "Base (рекомендуется)", "Small (точная)", "Large-v3 (максимум)"])
        self.model_combo.setCurrentIndex(1)  # Base по умолчанию
        self.model_combo.setMaximumWidth(200)
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        
        settings_layout.addLayout(audio_source_layout)
        settings_layout.addLayout(model_layout)
        settings_group.setLayout(settings_layout)
        
        # === Кнопка записи ===
        self.record_button = QPushButton("🔴 Начать запись")
        self.record_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.record_button.setMinimumHeight(50)
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # === Транскрипция ===
        transcription_label = QLabel("📝 Транскрипция")
        transcription_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        
        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setFont(QFont("Segoe UI", 10))
        self.transcription_text.setPlaceholderText("Транскрипция появится здесь...")
        self.transcription_text.setMinimumHeight(200)
        
        # === AI Саммари ===
        summary_label = QLabel("✨ AI Саммари (обновляется каждые 3 минуты)")
        summary_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setFont(QFont("Segoe UI", 10))
        self.summary_text.setPlaceholderText("AI саммари появится здесь после 3 минут записи...")
        self.summary_text.setMinimumHeight(150)
        
        # === Кнопки действий ===
        actions_layout = QHBoxLayout()
        
        self.save_html_button = QPushButton("💾 Сохранить HTML")
        self.save_html_button.setFont(QFont("Segoe UI", 10))
        self.save_html_button.setMinimumHeight(40)
        self.save_html_button.clicked.connect(self.save_as_html)
        self.save_html_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.save_pdf_button = QPushButton("📄 Сохранить PDF")
        self.save_pdf_button.setFont(QFont("Segoe UI", 10))
        self.save_pdf_button.setMinimumHeight(40)
        self.save_pdf_button.clicked.connect(self.save_as_pdf)
        self.save_pdf_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.clear_button = QPushButton("🗑️ Очистить")
        self.clear_button.setFont(QFont("Segoe UI", 10))
        self.clear_button.setMinimumHeight(40)
        self.clear_button.clicked.connect(self.clear_all)
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        actions_layout.addWidget(self.save_html_button)
        actions_layout.addWidget(self.save_pdf_button)
        actions_layout.addWidget(self.clear_button)
        
        # Собираем всё вместе
        main_layout.addWidget(settings_group)
        main_layout.addWidget(self.record_button)
        main_layout.addWidget(transcription_label)
        main_layout.addWidget(self.transcription_text)
        main_layout.addWidget(summary_label)
        main_layout.addWidget(self.summary_text)
        main_layout.addLayout(actions_layout)
        
        central_widget.setLayout(main_layout)
    
    def apply_dark_theme(self):
        """Применение тёмной темы в стиле Notion"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #191919;
            }
            QWidget {
                background-color: #191919;
                color: #e3e3e3;
            }
            QGroupBox {
                border: 1px solid #2e2e2e;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #e3e3e3;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #e3e3e3;
            }
            QPushButton {
                background-color: #2e2e2e;
                color: #e3e3e3;
                border: none;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #3e3e3e;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
            QPushButton#recordButton {
                background-color: #eb5757;
            }
            QPushButton#recordButton:hover {
                background-color: #ff6b6b;
            }
            QTextEdit {
                background-color: #252525;
                color: #e3e3e3;
                border: 1px solid #2e2e2e;
                border-radius: 6px;
                padding: 10px;
            }
            QRadioButton {
                color: #e3e3e3;
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #4e4e4e;
                background-color: #252525;
            }
            QRadioButton::indicator:checked {
                background-color: #5e9fff;
                border: 2px solid #5e9fff;
            }
            QComboBox {
                background-color: #2e2e2e;
                color: #e3e3e3;
                border: 1px solid #3e3e3e;
                border-radius: 6px;
                padding: 5px 10px;
            }
            QComboBox:hover {
                border: 1px solid #5e9fff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2e2e2e;
                color: #e3e3e3;
                selection-background-color: #5e9fff;
            }
        """)
        
        # Специальный стиль для кнопки записи
        self.record_button.setObjectName("recordButton")
    
    def toggle_recording(self):
        """Переключение записи"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Начать запись"""
        # Получаем настройки
        model_map = {
            0: "tiny",
            1: "base",
            2: "small",
            3: "large-v3"
        }
        model = model_map[self.model_combo.currentIndex()]
        audio_source = "system" if self.radio_system.isChecked() else "microphone"
        
        # Показываем индикатор
        self.record_button.setText("⏳ Инициализация...")
        self.record_button.setEnabled(False)
        QApplication.processEvents()
        
        try:
            # Создаем движок (модель загрузится при start_recording)
            self.engine = TranscriberEngine(
                model_size=model,
                audio_source=audio_source,
                callback=self.on_transcription_update
            )
            
            # Запускаем поток
            self.transcriber_thread = TranscriberThread(self.engine)
            self.transcriber_thread.start()
            
            # Обновляем UI
            self.is_recording = True
            self.record_button.setText("⏹️ Остановить запись")
            self.record_button.setEnabled(True)
            self.record_button.setStyleSheet("background-color: #4a4a4a;")
            
            # Блокируем настройки
            self.radio_system.setEnabled(False)
            self.radio_mic.setEnabled(False)
            self.model_combo.setEnabled(False)
            
            self.last_gemini_time = time.time()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка запуска",
                f"Не удалось начать запись:\n{str(e)}"
            )
            self.record_button.setText("🔴 Начать запись")
            self.record_button.setEnabled(True)
    
    def stop_recording(self):
        """Остановить запись"""
        if self.transcriber_thread:
            self.transcriber_thread.stop()
            self.transcriber_thread.wait()
        
        # Обновляем UI
        self.is_recording = False
        self.record_button.setText("🔴 Начать запись")
        self.record_button.setStyleSheet("")
        
        # Разблокируем настройки
        self.radio_system.setEnabled(True)
        self.radio_mic.setEnabled(True)
        self.model_combo.setEnabled(True)
    
    def on_transcription_update(self, timestamp, text):
        """Обработка новой транскрипции"""
        # Добавляем в окно транскрипции
        self.transcription_text.append(f"[{timestamp}] {text}")
        
        # Накапливаем текст для Gemini
        self.accumulated_text += f"{text} "
        
        # Проверяем, прошло ли 3 минуты
        current_time = time.time()
        if current_time - self.last_gemini_time >= 180:  # 180 секунд = 3 минуты
            self.send_to_gemini()
            self.last_gemini_time = current_time
    
    def send_to_gemini(self):
        """Отправка текста в Gemini API"""
        if not self.accumulated_text.strip():
            return
        
        if not self.gemini:
            self.summary_text.append(f"\n⚠️ Gemini API не инициализирован")
            return
        
        try:
            # Показываем индикатор загрузки
            timestamp = time.strftime("%H:%M:%S")
            self.summary_text.append(f"\n⏳ [{timestamp}] Создание AI саммари...")
            
            # Отправляем в Gemini
            summary = self.gemini.create_summary(self.accumulated_text)
            
            if summary:
                # Очищаем индикатор загрузки
                current_text = self.summary_text.toPlainText()
                current_text = current_text.replace(f"⏳ [{timestamp}] Создание AI саммари...", "")
                self.summary_text.setPlainText(current_text)
                
                # Добавляем саммари
                self.summary_text.append(f"\n✨ Саммари ({timestamp}):")
                self.summary_text.append("─" * 50)
                self.summary_text.append(summary)
                self.summary_text.append("─" * 50)
            else:
                self.summary_text.append(f"❌ Не удалось создать саммари")
            
        except Exception as e:
            self.summary_text.append(f"\n❌ Ошибка Gemini API: {str(e)}")
        
        # Очищаем накопленный текст
        self.accumulated_text = ""
    
    def save_as_html(self):
        """Сохранение конспекта в HTML"""
        try:
            # Получаем текст
            transcription = self.transcription_text.toPlainText()
            summary = self.summary_text.toPlainText()
            
            if not transcription.strip() and not summary.strip():
                QMessageBox.warning(
                    self,
                    "Нет данных",
                    "Нечего сохранять! Начните запись или дождитесь транскрипции."
                )
                return
            
            # Диалог сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить конспект как HTML",
                f"Конспект_Цера_{time.strftime('%Y-%m-%d_%H-%M-%S')}.html",
                "HTML Files (*.html)"
            )
            
            if file_path:
                # Сохраняем
                saved_path = NotesExporter.save_html(
                    transcription_text=transcription,
                    summary_text=summary,
                    output_path=file_path
                )
                
                QMessageBox.information(
                    self,
                    "Успешно сохранено",
                    f"Конспект сохранен:\n{saved_path}\n\nОткрыть файл?"
                )
                
                # Открываем файл в браузере
                os.startfile(saved_path)
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить HTML:\n{str(e)}"
            )
    
    def save_as_pdf(self):
        """Сохранение конспекта в PDF"""
        try:
            # Получаем текст
            transcription = self.transcription_text.toPlainText()
            summary = self.summary_text.toPlainText()
            
            if not transcription.strip() and not summary.strip():
                QMessageBox.warning(
                    self,
                    "Нет данных",
                    "Нечего сохранять! Начните запись или дождитесь транскрипции."
                )
                return
            
            # Диалог сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить конспект как PDF",
                f"Конспект_Цера_{time.strftime('%Y-%m-%d_%H-%M-%S')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if file_path:
                # Сохраняем
                saved_path = NotesExporter.save_pdf(
                    transcription_text=transcription,
                    summary_text=summary,
                    output_path=file_path
                )
                
                QMessageBox.information(
                    self,
                    "Успешно сохранено",
                    f"Конспект сохранен:\n{saved_path}\n\nОткрыть файл?"
                )
                
                # Открываем файл
                os.startfile(saved_path)
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить PDF:\n{str(e)}\n\n💡 Совет: Используйте HTML для сохранения с русским текстом.\nPDF использует транслитерацию (русский → латиница)."
            )
    
    def clear_all(self):
        """Очистка всех полей"""
        self.transcription_text.clear()
        self.summary_text.clear()
        self.accumulated_text = ""


def main():
    app = QApplication(sys.argv)
    
    # Устанавливаем шрифт для всего приложения
    app.setFont(QFont("Segoe UI", 9))
    
    window = CeraMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
