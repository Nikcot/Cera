import asyncio
import json
import time
import sys
import os
import numpy as np
from faster_whisper import WhisperModel
import websockets
import threading
import queue
import re

# ── Настройки ──
SAMPLE_RATE = 16000
MODEL_SIZE = "base"
LANGUAGE = "ru"
MIN_DURATION = 5.0  # Копим 5 секунд
HOST = "localhost"
PORT = 8765

# Регулярка для фильтрации галлюцинаций Whisper
HALLUCINATION_REGEX = re.compile(r"^\s*(\[.*?\]|\(.*?\)|Субтитры|Музыка|Продолжение следует|СПОКОЙ.*?|Редактор.*?)\s*$", re.IGNORECASE)

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

class WhisperTranscriber:
    def __init__(self):
        self.model = None
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.clients = set()
        self.lock = threading.Lock()
        self.accumulated_audio = np.array([], dtype=np.float32)

    def load_model(self):
        print(f"⏳ Загрузка модели {MODEL_SIZE}...")
        try:
            self.model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
            print("✅ Модель загружена! (CPU int8)")
            return True
        except Exception as e:
            print(f"❌ Ошибка модели: {e}")
            return False

    def transcribe_worker(self):
        print("🎙️ Воркер транскрибации запущен")
        while self.is_running:
            try:
                item = self.audio_queue.get(timeout=0.5)
                chunk = item["audio"]
                
                self.accumulated_audio = np.concatenate((self.accumulated_audio, chunk))

                duration = len(self.accumulated_audio) / SAMPLE_RATE
                
                if duration >= MIN_DURATION:
                    self.process_audio(self.accumulated_audio)
                    # Очищаем буфер ПОСЛЕ обработки
                    self.accumulated_audio = np.array([], dtype=np.float32)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing audio: {e}")

    def process_audio(self, audio_data):
        try:
            # 1. Проверка громкости (RMS)
            rms = np.sqrt(np.mean(audio_data**2))
            if rms < 0.001: 
                # Тишина - игнорируем
                return

            # 2. Транскрибация
            segments, _ = self.model.transcribe(
                audio_data,
                language=LANGUAGE,
                vad_filter=True, 
                vad_parameters=dict(min_silence_duration_ms=1000),
                beam_size=5,
                condition_on_previous_text=False # Не зацикливаться
            )

            text_segments = []
            for segment in segments:
                t = segment.text.strip()
                # 3. Фильтр галлюцинаций и мусора
                if t and len(t) > 1 and not HALLUCINATION_REGEX.match(t):
                    text_segments.append(t)

            if text_segments:
                full_text = " ".join(text_segments)
                timestamp = time.strftime("%H:%M:%S")
                print(f"📝 [{timestamp}] {full_text}")

                msg = json.dumps({
                    "type": "transcription",
                    "text": full_text
                }, ensure_ascii=False)

                with self.lock:
                    for client in self.clients:
                        asyncio.run_coroutine_threadsafe(client.send(msg), self.loop)
                
        except Exception as e:
            print(f"Transcribe Error: {e}")

    def start(self, loop):
        self.loop = loop
        self.is_running = True
        threading.Thread(target=self.transcribe_worker, daemon=True).start()

transcriber = WhisperTranscriber()

async def handler(websocket):
    print("🔗 Клиент подключен")
    with transcriber.lock:
        transcriber.clients.add(websocket)
    
    await websocket.send(json.dumps({"type": "connected"}))

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                audio_np = np.frombuffer(message, dtype=np.float32)
                transcriber.audio_queue.put({"audio": audio_np})
    except:
        pass
    finally:
        print("❌ Клиент отключен")
        with transcriber.lock:
             transcriber.clients.discard(websocket)

async def main():
    clear_console()
    print("╔═════════════════════════════════════╗")
    print("║   🧠 ЦЕРА — СЕРВЕР ТРАНСКРИБАЦИИ    ║")
    print("╠═════════════════════════════════════╣")
    print("║  Режим: Накопление 5 сек + VAD      ║")
    print("╚═════════════════════════════════════╝")
    
    if not transcriber.load_model():
        return

    transcriber.start(asyncio.get_event_loop())

    print(f"\n🚀 WS Server: ws://{HOST}:{PORT}")
    
    async with websockets.serve(handler, HOST, PORT):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
