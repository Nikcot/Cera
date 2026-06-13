"""
Модуль экспорта конспектов в HTML и PDF
"""

import os
from datetime import datetime
from fpdf import FPDF


class NotesExporter:
    """Экспорт конспектов в красивые HTML и PDF файлы"""
    
    @staticmethod
    def get_html_template(title, date, summary, transcription):
        """Генерация HTML с Notion-style дизайном"""
        return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 
                         'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            background: #191919;
            color: #e3e3e3;
            padding: 40px 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #1e1e1e;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }}
        
        .header {{
            border-bottom: 2px solid #2e2e2e;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        h1 {{
            font-size: 2.5em;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 10px;
        }}
        
        .date {{
            color: #9b9b9b;
            font-size: 0.95em;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.5em;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .summary-box {{
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            border-left: 4px solid #5e9fff;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
        }}
        
        .summary-box p {{
            margin-bottom: 12px;
            font-size: 1.05em;
            line-height: 1.7;
        }}
        
        .summary-box ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .summary-box li {{
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
        }}
        
        .summary-box li:before {{
            content: "•";
            position: absolute;
            left: 10px;
            color: #5e9fff;
            font-weight: bold;
            font-size: 1.2em;
        }}
        
        .transcription-box {{
            background: #252525;
            border-radius: 8px;
            padding: 20px;
            max-height: 600px;
            overflow-y: auto;
        }}
        
        .transcription-line {{
            padding: 10px 0;
            border-bottom: 1px solid #2e2e2e;
        }}
        
        .transcription-line:last-child {{
            border-bottom: none;
        }}
        
        .timestamp {{
            color: #5e9fff;
            font-weight: 600;
            font-family: 'Courier New', monospace;
            margin-right: 10px;
        }}
        
        .text {{
            color: #d4d4d4;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #2e2e2e;
            text-align: center;
            color: #6b6b6b;
            font-size: 0.9em;
        }}
        
        /* Для печати */
        @media print {{
            body {{
                background: white;
                color: black;
            }}
            .container {{
                box-shadow: none;
                background: white;
            }}
            .summary-box {{
                background: #f5f5f5;
                border-left-color: #3b82f6;
            }}
            .transcription-box {{
                background: #fafafa;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 {title}</h1>
            <div class="date">📅 {date}</div>
        </div>
        
        <div class="section">
            <div class="section-title">✨ AI Саммари</div>
            <div class="summary-box">
                {summary if summary.strip() else '<p style="color: #6b6b6b;">Саммари пока не создано</p>'}
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📝 Полная транскрипция</div>
            <div class="transcription-box">
                {transcription if transcription.strip() else '<p style="color: #6b6b6b;">Транскрипция пуста</p>'}
            </div>
        </div>
        
        <div class="footer">
            Создано с помощью Цера • {date}
        </div>
    </div>
</body>
</html>
"""
    
    @staticmethod
    def format_transcription_html(transcription_text):
        """Форматирование транскрипции для HTML"""
        if not transcription_text.strip():
            return ""
        
        lines = transcription_text.strip().split('\n')
        html_lines = []
        
        for line in lines:
            if line.strip():
                # Разделяем timestamp и текст
                if ']' in line:
                    parts = line.split(']', 1)
                    timestamp = parts[0].replace('[', '').strip()
                    text = parts[1].strip() if len(parts) > 1 else ""
                    
                    html_lines.append(
                        f'<div class="transcription-line">'
                        f'<span class="timestamp">[{timestamp}]</span>'
                        f'<span class="text">{text}</span>'
                        f'</div>'
                    )
                else:
                    html_lines.append(
                        f'<div class="transcription-line">'
                        f'<span class="text">{line}</span>'
                        f'</div>'
                    )
        
        return '\n'.join(html_lines)
    
    @staticmethod
    def format_summary_html(summary_text):
        """Форматирование саммари для HTML"""
        if not summary_text.strip():
            return ""
        
        # Простое форматирование - разбиваем на параграфы
        paragraphs = summary_text.strip().split('\n\n')
        html_parts = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # Если строка начинается с "•" или "-", делаем список
                if para.startswith('•') or para.startswith('-'):
                    items = [item.strip().lstrip('•-').strip() for item in para.split('\n')]
                    html_parts.append('<ul>')
                    for item in items:
                        if item:
                            html_parts.append(f'<li>{item}</li>')
                    html_parts.append('</ul>')
                else:
                    html_parts.append(f'<p>{para}</p>')
        
        return '\n'.join(html_parts)
    
    @classmethod
    def save_html(cls, transcription_text, summary_text, output_path=None):
        """
        Сохранение конспекта в HTML
        
        Args:
            transcription_text: Текст транскрипции
            summary_text: Текст AI саммари
            output_path: Путь для сохранения (если None, создается автоматически)
        
        Returns:
            Путь к сохраненному файлу
        """
        # Генерируем имя файла если не указано
        if output_path is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_path = f"Конспект_Цера_{timestamp}.html"
        
        # Форматируем данные
        title = "Конспект Цера"
        date = datetime.now().strftime("%d %B %Y, %H:%M")
        
        formatted_transcription = cls.format_transcription_html(transcription_text)
        formatted_summary = cls.format_summary_html(summary_text)
        
        # Генерируем HTML
        html_content = cls.get_html_template(
            title=title,
            date=date,
            summary=formatted_summary,
            transcription=formatted_transcription
        )
        
        # Сохраняем
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    @classmethod
    def save_pdf(cls, transcription_text, summary_text, output_path=None):
        """
        Сохранение конспекта в PDF
        
        Args:
            transcription_text: Текст транскрипции
            summary_text: Текст AI саммари
            output_path: Путь для сохранения (если None, создается автоматически)
        
        Returns:
            Путь к сохраненному файлу
        """
        # Генерируем имя файла если не указано
        if output_path is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_path = f"Конспект_Цера_{timestamp}.pdf"
        
        # Создаем PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Заголовок
        pdf.set_font('Helvetica', 'B', 24)
        pdf.cell(0, 15, 'Konspekt Cera', ln=True, align='C')
        
        # Дата
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(128, 128, 128)
        date_str = datetime.now().strftime("%d.%m.%Y, %H:%M")
        pdf.cell(0, 8, date_str, ln=True, align='C')
        pdf.ln(10)
        
        # AI Саммари
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, 'AI Summary', ln=True)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 11)
        if summary_text.strip():
            # Транслитерация для PDF (так как нет русских шрифтов)
            summary_latin = cls._transliterate(summary_text)
            for line in summary_latin.strip().split('\n'):
                if line.strip():
                    pdf.multi_cell(0, 6, line.strip())
        else:
            pdf.set_text_color(128, 128, 128)
            pdf.cell(0, 8, 'Summary not created yet', ln=True)
            pdf.set_text_color(0, 0, 0)
        
        pdf.ln(10)
        
        # Транскрипция
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, 'Full Transcription', ln=True)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 10)
        if transcription_text.strip():
            # Транслитерация для PDF
            trans_latin = cls._transliterate(transcription_text)
            for line in trans_latin.strip().split('\n'):
                if line.strip():
                    pdf.multi_cell(0, 5, line.strip())
        else:
            pdf.set_text_color(128, 128, 128)
            pdf.cell(0, 8, 'Transcription is empty', ln=True)
        
        # Сохраняем
        pdf.output(output_path)
        
        return output_path
    
    @staticmethod
    def _transliterate(text):
        """Простая транслитерация русского текста в латиницу"""
        translit_dict = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
            'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
            'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
            'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
            'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
        }
        result = []
        for char in text:
            result.append(translit_dict.get(char, char))
        return ''.join(result)
