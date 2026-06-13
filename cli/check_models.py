# -*- coding: utf-8 -*-
"""
Проверка доступных моделей Gemini
"""
import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

print("Доступные модели Gemini:")
print("=" * 60)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        print(f"   Описание: {model.display_name}")
        print()
