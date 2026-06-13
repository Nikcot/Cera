"""
Интеграция с Gemini API для создания AI саммари
"""

import google.generativeai as genai
from typing import Optional


class GeminiAPI:
    """Класс для работы с Gemini API"""
    
    def __init__(self, api_key: str):
        """
        Инициализация Gemini API
        
        Args:
            api_key: API ключ от Google AI Studio
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def create_summary(self, transcription_text: str) -> Optional[str]:
        """
        Создание саммари из транскрипции
        
        Args:
            transcription_text: Текст транскрипции
        
        Returns:
            Текст саммари или None в случае ошибки
        """
        if not transcription_text.strip():
            return None
        
        # Промпт для Gemini
        prompt = f"""Ты - профессиональный помощник для создания конспектов.

Твоя задача: проанализировать транскрипцию аудио и создать краткое, структурированное саммари.

ВАЖНО:
1. Исправь все ошибки транскрибации (до 30% текста может содержать неточности)
2. Выдели основные тезисы
3. Структурируй информацию
4. Используй эмодзи для наглядности
5. Пиши на том же языке, что и транскрипция

Формат ответа:
📝 Основные тезисы:
• Тезис 1
• Тезис 2
• Тезис 3

💡 Ключевые моменты:
[Краткое описание главного]

---

ТРАНСКРИПЦИЯ:
{transcription_text}

---

САММАРИ:"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Oshibka Gemini API: {e}")
            return f"Oshibka sozdaniya summary: {str(e)}"
    
    def improve_transcription(self, transcription_text: str) -> Optional[str]:
        """
        Улучшение транскрипции (исправление ошибок)
        
        Args:
            transcription_text: Текст транскрипции
        
        Returns:
            Исправленный текст или None в случае ошибки
        """
        if not transcription_text.strip():
            return None
        
        prompt = f"""Исправь ошибки в этой транскрипции аудио. 
Транскрибатор мог допустить до 30% ошибок.

Твоя задача:
1. Исправить неправильно распознанные слова
2. Сохранить исходный смысл
3. Улучшить читабельность
4. НЕ добавлять новую информацию

ТРАНСКРИПЦИЯ:
{transcription_text}

ИСПРАВЛЕННЫЙ ТЕКСТ:"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Ошибка Gemini API: {e}")
            return None
