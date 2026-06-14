# 🧠 Cera — Chrome Extension (Standalone)

A Chrome extension for audio transcription via **standalone Whisper (WASM)** and AI summaries via **Gemini**.

Runs **entirely in the browser**, without requiring Python installations or external servers.

---

## 📦 Installation

### Step 1 — Build the extension

To run the extension, you need to build the bundle (because Transformers.js is used):

1. Install [Node.js](https://nodejs.org/) (if not already installed)
2. Open a terminal in the `extension` folder
3. Run:

```bash
npm install
npm run build
```

This will create `offscreen.bundle.js` — the core of the speech recognition engine.

### Step 2 — Install in Chrome

1. Open `chrome://extensions/` in Chrome
2. Enable **Developer mode** (toggle in the top right)
3. Click **Load unpacked**
4. Select the `extension` folder

And you're done! 🎉

---

## 🚀 Usage

1. Click on the **Cera** icon in the extensions panel.
2. Upon the **first launch**, the extension will automatically download the Whisper base model (~150 MB).
   - *Download progress will be visible in the settings.*
3. Choose the source (Tab / Microphone) and click **Record**.

### Features:
- **Transcription**: Real-time, directly in your browser.
- **AI Summary**: Every 3 minutes (customizable) via the Gemini API.
- **Panel**: Convenient view of your history and summaries.

---

## ⚙️ Settings

| Parameter | Value |
|-----------|-------|
| Engine | Whisper (WASM, Transformers.js) |
| Model | `Xenova/whisper-base` (int8) |
| Language | Russian / English |
| Chunk | 10 seconds |
| Networking | Only for Gemini API and initial model download |

---

## 📁 Structure

```
extension/
├── build.js            ← Build script (esbuild)
├── package.json        ← Dependencies (transformers.js)
├── manifest.json       ← Chrome Extension config
├── background.js       ← Service Worker
├── src/
│   └── offscreen.js    ← Whisper logic (source)
├── offscreen.html      ← Bundle loader
├── popup.html / .js    ← UI window
├── sidepanel.html / .js ← Side panel
└── styles.css          ← Dark theme
```
