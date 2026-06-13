"""
Движок транскрибации для Цера
Использует Faster-Whisper для распознавания речи
"""

import pyaudiowpatch as pyaudio
import numpy as np
import queue
import threading
import time
from faster_whisper import WhisperModel

# Настройки
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 10
CHUNK_SIZE = 1024


class TranscriberEngine:
    def __init__(self, model_size="base", audio_source="system", callback=None):
        """
        Инициализация движка транскрибации
        
        Args:
            model_size: Размер модели (tiny, base, small, large-v3)
            audio_source: Источник звука (system или microphone)
            callback: Функция обратного вызова для получения результатов (timestamp, text)
        """
        self.model_size = model_size
        self.audio_source = audio_source
        self.callback = callback
        
        # Модель будет загружена при старте записи
        self.model = None
        
        # Очередь для аудио
        self.audio_queue = queue.Queue()
        self.is_recording = False
        
        # PyAudio
        self.p = pyaudio.PyAudio()
        
        # Потоки
        self.capture_thread = None
        self.transcribe_thread = None
    
    def get_audio_device(self):
        """Получение аудио устройства"""
        if self.audio_source == "system":
            # Системный звук (WASAPI Loopback)
            try:
                device = self.p.get_default_wasapi_loopback()
                if device:
                    print(f"Найдено устройство: {device['name']}")
                    return device
            except Exception as e:
                print(f"Ошибка получения WASAPI устройства: {e}")
                return None
        else:
            # Микрофон
            try:
                device_index = self.p.get_default_input_device_info()['index']
                device = self.p.get_device_info_by_index(device_index)
                print(f"Найден микрофон: {device['name']}")
                return device
            except Exception as e:
                print(f"Ошибка получения микрофона: {e}")
                return None
    
    def audio_capture_worker(self, device_info):
        """Поток захвата аудио"""
        print("Начинаю запись...")
        
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
            
            print("Поток записи открыт!")
            
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
                        audio_data = audio_data / 32768.0  # Нормализация
                        
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
    
    def transcription_worker(self):
        """Поток транскрибации"""
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
                
                # Собираем все слова
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
                
                # Отправляем результат через callback
                if all_words and self.callback:
                    full_text = "".join(all_words).strip()
                    if full_text:
                        timestamp = time.strftime("%H:%M:%S")
                        self.callback(timestamp, full_text)
            
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Ошибка транскрибации: {e}")
    
    def start_recording(self):
        """Начать запись"""
        # Загружаем модель если еще не загружена
        if self.model is None:
            print(f"Loading Whisper model ({self.model_size})...")
            try:
                self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                print("Model loaded!")
            except Exception as e:
                print(f"Model loading error: {e}")
                return False
        
        device = self.get_audio_device()
        if not device:
            print("Не удалось найти аудио устройство!")
            return False
        
        self.is_recording = True
        
        # Запускаем потоки
        self.capture_thread = threading.Thread(
            target=self.audio_capture_worker,
            args=(device,)
        )
        self.transcribe_thread = threading.Thread(
            target=self.transcription_worker
        )
        
        self.capture_thread.start()
        self.transcribe_thread.start()
        
        return True
    
    def stop_recording(self):
        """Остановить запись"""
        self.is_recording = False
        
        if self.capture_thread:
            self.capture_thread.join()
        if self.transcribe_thread:
            self.transcribe_thread.join()
        
        self.p.terminate()
        print("Запись остановлена!")
