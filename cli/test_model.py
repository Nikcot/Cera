# -*- coding: utf-8 -*-
"""
Тест загрузки модели Whisper
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from faster_whisper import WhisperModel

print("Starting model load test...")

try:
    print("Loading base model...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    print("SUCCESS! Model loaded!")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
