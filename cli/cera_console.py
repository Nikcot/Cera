"""
Cera Console - Транскрибация с AI саммари (консольная версия)
"""

import pyaudiowpatch as pyaudio
import numpy as np
import queue
import threading
import time
from faster_whisper import WhisperModel
from gemini_api import GeminiAPI
from config import GEMINI_API_KEY

# Настройки
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 10
CHUNK_SIZE = 1024
GEMINI_INTERVAL = 180  # 3 минуты в секундах

class CeraConsole:
    def __init__(self, model_size="base"):
        print("=" * 60)
        print("  CERA - AI Транскрибация и Саммари")
        print("=" * 60)
        print()
        
        # Загружаем модель Whisper
        print(f"Загрузка модели Whisper ({model_size})...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("Модель загружена!")
        
        # Инициализация Gemini
        print("Инициализация Gemini API...")
        try:
            self.gemini = GeminiAPI(GEMINI_API_KEY)
            print("Gemini API готов!")
        except Exception as e:
            print(f"Ошибка Gemini: {e}")
            self.gemini = None
        
        # Очередь для аудио
        self.audio_queue = queue.Queue()
        self.is_recording = False
        
        # Накопленный текст для Gemini
        self.accumulated_text = ""
        self.last_gemini_time = 0
        
        # PyAudio
        self.p = pyaudio.PyAudio()
        
        print()
    
    def get_system_audio_device(self):
        """Находит устройство для записи системного звука"""
        print("Поиск устройств вывода звука...")
        
        try:
            wasapi_info = self.p.get_default_wasapi_loopback()
            if wasapi_info:
                print(f"Найдено устройство: {wasapi_info['name']}")
                return wasapi_info
            else:
                print("Не найдено WASAPI loopback устройство!")
                return None
        except Exception as e:
            print(f"Ошибка поиска устройства: {e}")
            return None
    
    def audio_capture_thread(self, device_info):
        """Поток для захвата аудио"""
        print()
        print("=" * 60)
        print("  ЗАПИСЬ НАЧАТА")
        print("=" * 60)
        print()
        
        audio_buffer = []
        frames_needed = int(SAMPLE_RATE * CHUNK_DURATION)
        
        try:
            stream = self.p.open(
                format=pyaudio.paInt16,
                channels=device_info['maxInputChannels'],
                rate=int(device_info['defaultSampleRate']),
                input=True,
                input_device_index=device_info['index'],
                frames_per_buffer=CHUNK_SIZE
            )
            
            while self.is_recording:
                try:
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    audio_chunk = np.frombuffer(data, dtype=np.int16)
                    
                    # Конвертируем в моно если стерео
                    if device_info['maxInputChannels'] == 2:
                        audio_chunk = audio_chunk.reshape(-1, 2).mean(axis=1)
                    
                    # Ресемплинг до 16kHz если нужно
                    if int(device_info['defaultSampleRate']) != SAMPLE_RATE:
                        ratio = SAMPLE_RATE / device_info['defaultSampleRate']
                        new_length = int(len(audio_chunk) * ratio)
                        audio_chunk = np.interp(
                            np.linspace(0, len(audio_chunk), new_length),
                            np.arange(len(audio_chunk)),
                            audio_chunk
                        )
                    
                    audio_buffer.extend(audio_chunk)
                    
                    # Если накопили достаточно - отправляем на транскрибацию
                    if len(audio_buffer) >= frames_needed:
                        audio_data = np.array(audio_buffer[:frames_needed], dtype=np.float32)
                        audio_data = audio_data / 32768.0
                        
                        self.audio_queue.put(audio_data)
                        audio_buffer = audio_buffer[frames_needed:]
                
                except Exception as e:
                    print(f"Ошибка чтения данных: {e}")
                    continue
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"Ошибка записи: {e}")
            self.is_recording = False
    
    def transcription_thread(self):
        """Поток для транскрибации"""
        while self.is_recording or not self.audio_queue.empty():
            try:
                audio_data = self.audio_queue.get(timeout=1)
                
                # Транскрибируем
                segments, info = self.model.transcribe(
                    audio_data,
                    language="ru",
                    vad_filter=True,
                    beam_size=5,
                    word_timestamps=True
                )
                
                # Собираем слова
                all_words = []
                for segment in segments:
                    if hasattr(segment, 'words') and segment.words:
                        for word in segment.words:
                            if word.start < CHUNK_DURATION - 0.5:
                                all_words.append(word.word)
                    else:
                        text = segment.text.strip()
                        if text:
                            all_words.append(text)
                
                # Выводим результат
                if all_words:
                    full_text = "".join(all_words).strip()
                    if full_text:
                        timestamp = time.strftime("%H:%M:%S")
                        print(f"[{timestamp}] {full_text}")
                        
                        # Накапливаем для Gemini
                        self.accumulated_text += " " + full_text
                        
                        # Проверяем нужно ли отправить в Gemini
                        current_time = time.time()
                        if self.gemini and (current_time - self.last_gemini_time) >= GEMINI_INTERVAL:
                            self.send_to_gemini()
                            self.last_gemini_time = current_time
            
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Ошибка транскрибации: {e}")
    
    def send_to_gemini(self):
        """Отправка в Gemini для создания саммари"""
        if not self.accumulated_text.strip():
            return
        
        print()
        print("=" * 60)
        print("  AI САММАРИ (Gemini)")
        print("=" * 60)
        
        try:
            summary = self.gemini.create_summary(self.accumulated_text)
            if summary:
                print(summary)
            else:
                print("Не удалось создать саммари")
        except Exception as e:
            print(f"Ошибка Gemini: {e}")
        
        print("=" * 60)
        print()
        
        # Очищаем накопленный текст
        self.accumulated_text = ""
    
    def start(self):
        """Запуск транскрибации"""
        # Находим устройство
        device = self.get_system_audio_device()
        if not device:
            self.cleanup()
            return
        
        # Запускаем потоки
        self.is_recording = True
        self.last_gemini_time = time.time()
        
        capture_thread = threading.Thread(target=self.audio_capture_thread, args=(device,))
        transcribe_thread = threading.Thread(target=self.transcription_thread)
        
        capture_thread.start()
        transcribe_thread.start()
        
        print("Нажмите Ctrl+C для остановки...")
        print()
        
        try:
            while self.is_recording:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print()
            print()
            print("=" * 60)
            print("  ОСТАНОВКА ЗАПИСИ...")
            print("=" * 60)
            self.is_recording = False
        
        # Ждем завершения потоков
        capture_thread.join()
        transcribe_thread.join()
        
        # Финальное саммари если есть текст
        if self.accumulated_text.strip() and self.gemini:
            print()
            print("Создание финального саммари...")
            self.send_to_gemini()
        
        self.cleanup()
        print()
        print("Транскрибация завершена!")
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.p.terminate()

def select_model():
    """Выбор модели"""
    print()
    print("=" * 60)
    print("  ВЫБОР МОДЕЛИ WHISPER")
    print("=" * 60)
    print()
    print("Доступные модели:")
    print("  [1] Tiny   - Самая быстрая (~75MB)")
    print("  [2] Base   - Золотая середина (~142MB) [Рекомендуется]")
    print("  [3] Small  - Высокая точность (~466MB)")
    print("  [4] Large-v3 - Максимальная точность (~2.9GB)")
    print()
    
    while True:
        choice = input("Выберите модель (1-4) [2]: ").strip()
        
        if choice == "" or choice == "2":
            return "base"
        elif choice == "1":
            return "tiny"
        elif choice == "3":
            return "small"
        elif choice == "4":
            return "large-v3"
        else:
            print("Неверный выбор! Введите 1, 2, 3 или 4")

if __name__ == "__main__":
    model_size = select_model()
    cera = CeraConsole(model_size=model_size)
    cera.start()
