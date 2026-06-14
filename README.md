# Cera

A suite of tools for local audio transcription using Whisper and AI-powered summarization using Gemini. Includes three versions:

- **CLI / Web**: The base version featuring scripts and a web interface.
- **Desktop**: A fully-featured desktop application built with Python (PySide6/Qt).
- **Extension**: An autonomous Chrome extension (Whisper WASM + Gemini).

## 🚀 Features
- 🎤 Record from microphone and system audio
- 🧠 Local transcription (Whisper / Faster-Whisper / Transformers.js)
- 📝 Automatic summaries and notes powered by Gemini AI
- 💾 Export to beautiful HTML and PDF formats (in the Desktop version)

## 📁 Project Structure
- `/cli` — scripts and web version
- `/desktop` — desktop application
- `/extension` — browser extension

## ⚙️ Setup & Usage
Each directory contains its own `README.md` with detailed installation and running instructions.

> **Note:** For the AI-summarization to work, you will need a free [Gemini API Key](https://aistudio.google.com/apikey).

## 📄 License
MIT License
