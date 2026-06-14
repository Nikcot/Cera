# 🧠 Cera

Desktop application for audio transcription and creating AI summaries.

## 🎯 Features

- ✅ **System Audio Recording** - record audio from your browser (Zoom, Meet, YouTube)
- ✅ **Microphone Recording** - record your voice
- ✅ **AI Transcription** - Faster-Whisper (offline, private)
- ✅ **4 Models to Choose From** - from the fast Tiny to the highly accurate Large-v3
- ✅ **AI Summarization** - Gemini creates summaries every 3 minutes ⭐ NEW!
- ✅ **Export to HTML** - beautiful notes in Notion style ⭐ NEW!
- ✅ **Export to PDF** - for printing and sharing ⭐ NEW!
- ✅ **Dark Theme** - Notion-style design

## 📦 Installation

### 1. Install dependencies:
```bash
py -m pip install -r requirements.txt
```

### 2. Configure Gemini API:
1. Get an API key: https://aistudio.google.com/apikey
2. Copy `config.example.py` to `config.py`
3. Insert your API key into `config.py`

### 3. Run the application:
```bash
run.bat
```

Or manually:
```bash
py main.py
```

## 🎨 Interface

- **Audio Source**: Choose between system audio or microphone
- **Model**: Select the Whisper model (Base is recommended)
- **Transcription**: Text appears in real-time (every 10 seconds)
- **AI Summary**: Gemini generates a summary every 3 minutes
- **Export**: Save as HTML or PDF

## 🔧 Requirements

- Python 3.11+
- Windows 10/11
- ~500MB RAM for the Base model
- ~2GB RAM for the Large-v3 model
- Gemini API key (Free!)

## 📝 Usage

1. Select an audio source
2. Select a Whisper model
3. Click "Start Recording"
4. Speak or play a video/meeting
5. Text will appear in the transcription window (updates every 10 sec)
6. Every 3 minutes, Gemini will create a summary
7. Save the notes using the "Save HTML" or "Save PDF" buttons

## 🚀 Roadmap

- [x] Gemini API Integration
- [x] Export to HTML/PDF
- [ ] Recording history
- [ ] Support for more languages
- [ ] Chrome Extension (future)

## 📄 License

MIT License
