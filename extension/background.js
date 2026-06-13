/**
 * Цера — Background Service Worker (Server Version)
 * Connects to local Python server for Whisper transcription.
 */

// ── State ──
let isRecording = false;
let audioSource = 'tab'; // 'tab' | 'mic'
let accumulatedText = []; // Array of segments
let summaryLog = [];
let wordCount = 0;
let startTime = 0;
let summaryTimerId = null;

let socket = null;
let isConnected = false;
const WS_URL = 'ws://localhost:8765';

// Settings
let settings = {
    apiKey: 'YOUR_GEMINI_API_KEY_HERE',
    summaryInterval: 180, // seconds
};

// Load settings
chrome.storage.local.get(['ceraSettings'], (res) => {
    if (res.ceraSettings) settings = { ...settings, ...res.ceraSettings };
});

// ── WebSocket Connection ──
function connectServer() {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return;

    console.log('[Cera] Converting to server...');
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
        console.log('✅ Server Connected');
        broadcast({ type: 'SERVER_STATUS', ok: true });
        isConnected = true;
    };

    socket.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'transcription' && msg.text) {
                handleTranscription(msg.text);
            }
        } catch (e) {
            console.error('WS Message Error:', e);
        }
    };

    socket.onclose = () => {
        console.log('❌ Server Disconnected');
        isConnected = false;
        broadcast({ type: 'SERVER_STATUS', ok: false });
        if (isRecording) stopRecording(); // Stop if server dies
        setTimeout(connectServer, 3000); // Auto reconnect
    };

    socket.onerror = (e) => {
        console.error('WS Error:', e);
    };
}

// ── Audio Handling ──
function handleTranscription(text) {
    const timestamp = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    // Add to log
    accumulatedText.push({ time: timestamp, text });

    // Count words
    const words = text.split(/\s+/).length;
    wordCount += words;

    // Broadcast update
    broadcast({
        type: 'TRANSCRIPTION_UPDATE',
        data: {
            text,
            timestamp,
            fullLog: accumulatedText,
            wordCount
        }
    });

    console.log(`📝 [${timestamp}] ${text}`);
}

// ── Offscreen Management ──
async function ensureOffscreen() {
    const existing = await chrome.offscreen.hasDocument();
    if (!existing) {
        await chrome.offscreen.createDocument({
            url: 'offscreen.html',
            reasons: ['USER_MEDIA'],
            justification: 'Capture tab audio for transcription'
        });
    }
}

async function startRecording(source) {
    if (isRecording) return;
    if (!isConnected) {
        broadcast({ type: 'ERROR', data: { message: 'Нет подключения к серверу!' } });
        return;
    }

    try {
        await ensureOffscreen();

        let streamId = null;
        if (source === 'tab') {
            streamId = await chrome.tabCapture.getMediaStreamId({ consumerTabId: null });
        }

        // Send command to offscreen
        chrome.runtime.sendMessage({
            target: 'offscreen',
            type: 'START_CAPTURE',
            data: { source, streamId }
        });

        isRecording = true;
        audioSource = source;
        startTime = Date.now();
        accumulatedText = [];
        wordCount = 0;

        chrome.action.setBadgeText({ text: "REC" });
        chrome.action.setBadgeBackgroundColor({ color: "#FF0000" });

        broadcast({ type: 'RECORDING_STARTED' });

        // Start Auto-Summary Timer
        startSummaryTimer();

    } catch (e) {
        console.error('Start Recording Error:', e);
        broadcast({ type: 'ERROR', data: { message: e.message } });
    }
}

function stopRecording() {
    if (!isRecording) return;

    chrome.runtime.sendMessage({
        target: 'offscreen',
        type: 'STOP_CAPTURE'
    });

    isRecording = false;
    chrome.action.setBadgeText({ text: "" });
    broadcast({ type: 'RECORDING_STOPPED' });

    stopSummaryTimer();
}

// ── Messages ──
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    // 1. Audio Data from Offscreen -> Server
    if (msg.type === 'AUDIO_CHUNK') {
        if (socket && socket.readyState === WebSocket.OPEN) {
            // Convert Array back to Float32Array buffer
            const floatArr = new Float32Array(msg.data);
            socket.send(floatArr.buffer);
        }
        return;
    }

    // 2. UI Commands
    switch (msg.type) {
        case 'START_RECORDING':
            startRecording(msg.data?.source || 'tab');
            break;
        case 'STOP_RECORDING':
            stopRecording();
            break;
        case 'GET_STATE':
            sendResponse({
                isRecording,
                isConnected,
                audioSource,
                transcriptionLog: accumulatedText,
                wordCount,
                elapsed: isRecording ? Math.floor((Date.now() - startTime) / 1000) : 0,
                settings
            });
            break;
        case 'SAVE_SETTINGS':
            settings = { ...settings, ...msg.data };
            chrome.storage.local.set({ ceraSettings: settings });
            break;
        case 'COPY_TEXT':
            const text = accumulatedText.map(t => `[${t.time}] ${t.text}`).join('\n');
            const summary = summaryLog.map(s => s.text).join('\n\n');
            sendResponse({ text, summary });
            break;
    }
});

// ── Helpers ──
function broadcast(msg) {
    chrome.runtime.sendMessage(msg).catch(() => { });
}

function startSummaryTimer() {
    if (summaryTimerId) clearInterval(summaryTimerId);
    summaryTimerId = setInterval(() => {
        // Placeholder for Gemini Summary Logic
        // (Can be added later or kept simple)
    }, settings.summaryInterval * 1000);
}

function stopSummaryTimer() {
    if (summaryTimerId) clearInterval(summaryTimerId);
    summaryTimerId = null;
}

// Initialize
connectServer();
