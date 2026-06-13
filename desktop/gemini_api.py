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
    
    def update_summary(self, new_transcription: str, previous_context: str = "") -> Optional[str]:
        """
        Дописывание конспекта с учетом контекста
        """
        # Context window: last 1000 chars of likely summary
        context_snippet = previous_context[-1000:] if previous_context else ""
        
        is_fresh_start = not previous_context
        
        special_instruction = ""
        if is_fresh_start:
            special_instruction = "ВАЖНО: Так как это начало лекции, придумай и напиши ЗАГОЛОВОК (# Тема) первой строкой."

        prompt = f"""Ты — профессиональный конспектолог.
Твоя задача — ДОПИСАТЬ продолжение конспекта лекции, основываясь на новом фрагменте аудио.

ВВОДНЫЕ ДАННЫЕ:
1. КОНТЕКСТ (На чем мы остановились): 
"...{context_snippet}"
(это уже написано, НЕ ПОВТОРЯЙ ЭТО, просто продолжай мысль).

2. НОВЫЙ ФРАГМЕНТ ТРАНСКРИПЦИИ (Сырой текст):
"{new_transcription}"

ИНСТРУКЦИЯ:
- В транскрипции 30% ошибок/мусора. Если предложение бессмысленно — ИГНОРИРУЙ ЕГО.
- Выдели главное и допиши к конспекту.
- Язык: Строго РУССКИЙ.
- Формат: Markdown (списки, **жирный**, ### заголовки).
{special_instruction}

ПРОДОЛЖЕНИЕ КОНСПЕКТА (только новые пункты):"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Gemini Update Error: {e}")
            return f"Oshibka обновлений: {str(e)}"

    def finalize_summary(self, raw_summary: str) -> Optional[str]:
        """
        Финальная обработка ("Причесать")
        """
        prompt = f"""Ты — главный редактор издательства.
Твоя задача — "ПРИЧЕСАТЬ" черновой конспект лекции.

ВХОДНОЙ ТЕКСТ (Черновик):
{raw_summary}

ИНСТРУКЦИЯ:
1. Объедини разрозненные куски в связный текст.
2. Удали повторы.
3. Исправь стиль и структуру (Введение, Тезисы, Детали, Выводы).
4. Язык: РУССКИЙ.

ФИНАЛЬНЫЙ КОНСПЕКТ:"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Gemini Finalize Error: {e}")
            return f"Oshibka финализации: {str(e)}"

    def improve_transcription(self, transcription_text: str) -> Optional[str]:
        """
        Улучшение транскрипции (исправление ошибок)
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
            import traceback
            traceback.print_exc()
            print(f"Ошибка Gemini API: {e}")
            return None

    def generate_filename_title(self, summary_text: str) -> str:
        """Генерация названия файла на основе саммари"""
        if not summary_text:
            return "Cera_Summary"
            
        prompt = f"""Придумай короткое, понятное название для файла конспекта (без расширения).
        Максимум 4-5 слов. Используй только буквы, цифры и пробелы.
        
        Текст конспекта:
        {summary_text[:1000]}...
        
        Название файла (только текст):"""
        
        try:
            response = self.model.generate_content(prompt)
            # Clean
            text = response.text.replace("\n", "").strip()
            # Remove forbidden chars for filenames
            import re
            clean_name = re.sub(r'[\\/*?:"<>|]', "", text)
            return clean_name or "Cera_Summary"
        except Exception as e:
            print(f"Title Gen Error: {e}")
            return "Cera_Summary"
