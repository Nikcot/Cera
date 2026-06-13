"""
Cera Web - Веб-интерфейс для транскрибации с AI саммари
"""

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import time
import pyaudiowpatch as pyaudio
import numpy as np
import queue
from faster_whisper import WhisperModel
from gemini_api import GeminiAPI
from config import GEMINI_API_KEY
import webbrowser

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cera-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Глобальные переменные
transcriber = None
is_recording = False

class CeraWebTranscriber:
    def __init__(self, model_size="base"):
        self.model_size = model_size
        self.model = None
        self.gemini = None
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.accumulated_text = ""
        self.last_gemini_time = 0
        self.p = pyaudio.PyAudio()
        
        # Статистика
        self.start_time = 0
        self.word_count = 0
    
    def initialize(self):
        """Инициализация моделей"""
        socketio.emit('status', {'message': f'Загрузка модели Whisper ({self.model_size})...'})
        self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        socketio.emit('status', {'message': 'Модель Whisper загружена!'})
        
        socketio.emit('status', {'message': 'Инициализация Gemini API...'})
        try:
            self.gemini = GeminiAPI(GEMINI_API_KEY)
            socketio.emit('status', {'message': 'Gemini API готов!'})
        except Exception as e:
            socketio.emit('status', {'message': f'Ошибка Gemini: {e}'})
            self.gemini = None
    
    def get_system_audio_device(self):
        """Находит устройство для записи системного звука"""
        try:
            wasapi_info = self.p.get_default_wasapi_loopback()
            if wasapi_info:
                socketio.emit('status', {'message': f'Найдено устройство: {wasapi_info["name"]}'})
                return wasapi_info
            else:
                socketio.emit('error', {'message': 'Не найдено WASAPI loopback устройство!'})
                return None
        except Exception as e:
            socketio.emit('error', {'message': f'Ошибка поиска устройства: {e}'})
            return None
    
    def audio_capture_thread(self, device_info):
        """Поток для захвата аудио"""
        SAMPLE_RATE = 16000
        CHUNK_DURATION = 10
        CHUNK_SIZE = 1024
        
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
                    
                    if device_info['maxInputChannels'] == 2:
                        audio_chunk = audio_chunk.reshape(-1, 2).mean(axis=1)
                    
                    if int(device_info['defaultSampleRate']) != SAMPLE_RATE:
                        ratio = SAMPLE_RATE / device_info['defaultSampleRate']
                        new_length = int(len(audio_chunk) * ratio)
                        audio_chunk = np.interp(
                            np.linspace(0, len(audio_chunk), new_length),
                            np.arange(len(audio_chunk)),
                            audio_chunk
                        )
                    
                    audio_buffer.extend(audio_chunk)
                    
                    if len(audio_buffer) >= frames_needed:
                        audio_data = np.array(audio_buffer[:frames_needed], dtype=np.float32)
                        audio_data = audio_data / 32768.0
                        self.audio_queue.put(audio_data)
                        audio_buffer = audio_buffer[frames_needed:]
                
                except Exception as e:
                    continue
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            socketio.emit('error', {'message': f'Ошибка записи: {e}'})
            self.is_recording = False
    
    def transcription_thread(self):
        """Поток для транскрибации"""
        CHUNK_DURATION = 10
        GEMINI_INTERVAL = 180
        
        while self.is_recording or not self.audio_queue.empty():
            try:
                audio_data = self.audio_queue.get(timeout=1)
                
                segments, info = self.model.transcribe(
                    audio_data,
                    language="ru",
                    vad_filter=True,
                    beam_size=5,
                    word_timestamps=True
                )
                
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
                
                if all_words:
                    full_text = "".join(all_words).strip()
                    if full_text:
                        timestamp = time.strftime("%H:%M:%S")
                        
                        # Отправляем транскрипцию в браузер
                        socketio.emit('transcription', {
                            'timestamp': timestamp,
                            'text': full_text
                        })
                        
                        # Обновляем статистику
                        self.word_count += len(full_text.split())
                        elapsed = int(time.time() - self.start_time)
                        socketio.emit('stats', {
                            'words': self.word_count,
                            'time': elapsed
                        })
                        
                        self.accumulated_text += " " + full_text
                        
                        current_time = time.time()
                        if self.gemini and (current_time - self.last_gemini_time) >= GEMINI_INTERVAL:
                            self.send_to_gemini()
                            self.last_gemini_time = current_time
            
            except queue.Empty:
                continue
            except Exception as e:
                socketio.emit('error', {'message': f'Ошибка транскрибации: {e}'})
    
    def send_to_gemini(self):
        """Отправка в Gemini для создания саммари"""
        if not self.accumulated_text.strip():
            return
        
        socketio.emit('status', {'message': 'Создание AI саммари...'})
        
        try:
            summary = self.gemini.create_summary(self.accumulated_text)
            if summary:
                socketio.emit('summary', {'text': summary})
            else:
                socketio.emit('error', {'message': 'Не удалось создать саммари'})
        except Exception as e:
            socketio.emit('error', {'message': f'Ошибка Gemini: {e}'})
        
        self.accumulated_text = ""
    
    def start(self):
        """Запуск транскрибации"""
        device = self.get_system_audio_device()
        if not device:
            return False
        
        self.is_recording = True
        self.start_time = time.time()
        self.last_gemini_time = time.time()
        self.word_count = 0
        self.accumulated_text = ""
        
        capture_thread = threading.Thread(target=self.audio_capture_thread, args=(device,))
        transcribe_thread = threading.Thread(target=self.transcription_thread)
        
        capture_thread.start()
        transcribe_thread.start()
        
        socketio.emit('recording_started', {})
        return True
    
    def stop(self):
        """Остановка транскрибации"""
        self.is_recording = False
        
        # Финальное саммари
        if self.accumulated_text.strip() and self.gemini:
            self.send_to_gemini()
        
        socketio.emit('recording_stopped', {})

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('status', {'message': 'Подключено к серверу'})

@socketio.on('start_recording')
def handle_start_recording(data):
    global transcriber, is_recording
    
    if is_recording:
        emit('error', {'message': 'Запись уже идёт!'})
        return
    
    model_size = data.get('model', 'base')
    
    # Создаем транскрибер в отдельном потоке
    def init_and_start():
        global transcriber, is_recording
        transcriber = CeraWebTranscriber(model_size=model_size)
        transcriber.initialize()
        if transcriber.start():
            is_recording = True
    
    thread = threading.Thread(target=init_and_start)
    thread.start()

@socketio.on('stop_recording')
def handle_stop_recording():
    global transcriber, is_recording
    
    if not is_recording or not transcriber:
        emit('error', {'message': 'Запись не идёт!'})
        return
    
    transcriber.stop()
    is_recording = False

if __name__ == '__main__':
    print("=" * 60)
    print("  CERA WEB - Запуск сервера...")
    print("=" * 60)
    print()
    print("Открываю браузер...")
    
    # Открываем браузер через 1 секунду
    threading.Timer(1.0, lambda: webbrowser.open('http://localhost:5000')).start()
    
    # Запускаем сервер
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
