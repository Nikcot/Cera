# 🧠 Cera (Цера)

Your personal AI secretary and digital "second brain." Cera is a suite of tools for local audio transcription using Whisper and AI-powered summarization using Gemini.

## 🌟 Our Mission

Imagine having a dedicated friend who never forgets a single word from your meetings, lectures, or spontaneous thoughts. Cera is designed to act as an extension of your own neural connections. We believe that your thoughts and conversations are deeply personal. That's why Cera processes all audio **locally** on your machine—your voice never leaves your device. Only the raw text is sent to the AI to forge beautiful, structured insights. It's your second brain, completely under your control.

## 🚀 Features

- 🎤 **Universal Recording:** Capture audio directly from your microphone or system audio (Zoom, Google Meet, YouTube, etc.).
- 🧠 **Local Transcription:** Powered by Whisper (Faster-Whisper / Transformers.js) for 100% private, offline speech-to-text.
- 📝 **Smart Neural Summaries:** Automatically generates structured notes and summaries using Google's Gemini AI every 3 minutes.
- 💾 **Beautiful Exports:** Export your digital memories to Notion-style HTML or PDF formats (available in the Desktop version).

## 📁 Project Structure

Cera is built to fit seamlessly into any workflow. The repository contains three distinct versions:

- **`/desktop`** — A sleek, fully-featured desktop application built with Python (PySide6/Qt).
- **`/extension`** — An autonomous Chrome extension running entirely in the browser (Whisper WASM + Gemini).
- **`/cli`** — The foundational CLI scripts and a lightweight web interface.

## ⚙️ Installation & Setup

Each component is completely independent. Choose the flavor of Cera that suits you best:

### Desktop Version (Recommended)
1. Navigate to the `desktop` directory.
2. Install Python dependencies: `pip install -r requirements.txt`
3. Get a free [Gemini API Key](https://aistudio.google.com/apikey).
4. Copy `.env.example` to `.env` and paste your API key.
5. Run the app: `python main.py` or use `run.bat`.

### Chrome Extension
1. Navigate to the `extension` directory.
2. Install Node dependencies and build: `npm install && npm run build`
3. Open Chrome and go to `chrome://extensions/`.
4. Enable **Developer mode** and click **Load unpacked**, then select the `extension` folder.

### CLI Version
Detailed instructions can be found inside the `cli/README.md` file.

## 🗺️ Roadmap

- [x] Integrate local Whisper transcription
- [x] Implement Gemini AI automatic summaries
- [x] Build Notion-style HTML/PDF export
- [x] Create standalone Chrome Extension (WASM)
- [ ] Implement a searchable history database ("Second Brain Memory")
- [ ] Add support for multiple AI providers (OpenAI, Claude, local LLMs)
- [ ] Introduce multi-language real-time translation features
- [ ] Cloud sync options for encrypted notes

## 📄 License
This project is licensed under the MIT License.
