import './background.js'; // Just a placeholder, we will overwrite

const WS_URL = 'ws://localhost:8765';
let socket = null;
let isConnected = false;

// ── WebSocket Logic ──
function connectServer() {
    if (socket && socket.readyState === WebSocket.OPEN) return;

    console.log('Connecting to server...');
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
        console.log('✅ Connected to Whisper Server');
        isConnected = true;
        chrome.runtime.sendMessage({ type: 'SERVER_STATUS', ok: true });
    };

    socket.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'transcription') {
                // Прямая транскрипция с сервера (VAD filtered)
                handleTranscription(msg.text);
            }
        } catch (e) {
            console.error('WS Error:', e);
        }
    };

    socket.onclose = () => {
        console.log('❌ Disconnected');
        isConnected = false;
        chrome.runtime.sendMessage({ type: 'SERVER_STATUS', ok: false });
        // Reconnect logic
        setTimeout(connectServer, 3000);
    };

    socket.onerror = (e) => {
        console.error('WebSocket Error:', e);
        isConnected = false;
    };
}

// ── Audio Source ──
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === 'AUDIO_CHUNK') {
        if (isConnected && socket.readyState === WebSocket.OPEN) {
            // Convert array back to typed array and send binary
            const audioData = new Float32Array(msg.data);
            socket.send(audioData.buffer); // Send ArrayBuffer directly
        }
    }
    else if (msg.type === 'CHECK_SERVER') {
        sendResponse({ ok: isConnected });
    }
    // ... keep existing UI/state logic
});

connectServer();
