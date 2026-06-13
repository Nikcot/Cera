/**
 * Цера — Popup Controller (Server Version)
 */

const serverDot = document.getElementById('serverDot');
const serverStatus = document.getElementById('serverStatus');
const recordBtn = document.getElementById('recordBtn');
const timerValue = document.getElementById('timerValue');
const wordCountEl = document.getElementById('wordCount');

// Init
document.addEventListener('DOMContentLoaded', async () => {
    const state = await sendMsg({ type: 'GET_STATE' });
    if (state) {
        updateServerStatus(state.isConnected);
        setRecordingUI(state.isRecording);
        if (state.isRecording) {
            updateTimer(state.elapsed);
            updateWordCount(state.wordCount);
        }
    }
});

// Update UI
function updateServerStatus(connected) {
    serverDot.className = 'sp-status-dot ' + (connected ? 'active' : 'error');
    serverStatus.textContent = connected ? 'Готово (Whisper)' : 'Сервер не запущен';
    serverStatus.style.color = connected ? 'var(--green)' : 'var(--red)';
    recordBtn.disabled = !connected;
}

function setRecordingUI(recording) {
    recordBtn.classList.toggle('recording', recording);
    document.getElementById('statusLabel').textContent = recording ? 'Запись...' : 'Готово к записи';
    document.getElementById('micIcon').style.display = recording ? 'none' : 'block';
    document.getElementById('stopIcon').style.display = recording ? 'block' : 'none';

    // Timer visibility
    document.getElementById('timerRow').style.visibility = recording ? 'visible' : 'hidden'; // or use class
}

function updateTimer(seconds) {
    const m = String(Math.floor(seconds / 60)).padStart(2, '0');
    const s = String(seconds % 60).padStart(2, '0');
    timerValue.textContent = `${m}:${s}`;
}

function updateWordCount(count) {
    wordCountEl.textContent = `${count} слов`;
}

// Logic
recordBtn.addEventListener('click', async () => {
    const state = await sendMsg({ type: 'GET_STATE' });
    if (state.isRecording) {
        await sendMsg({ type: 'STOP_RECORDING' });
    } else {
        await sendMsg({ type: 'START_RECORDING', data: { source: 'tab' } }); // Default tab
    }
});

// Messages
chrome.runtime.onMessage.addListener((msg) => {
    switch (msg.type) {
        case 'SERVER_STATUS':
            updateServerStatus(msg.ok);
            break;
        case 'RECORDING_STARTED':
            setRecordingUI(true);
            break;
        case 'RECORDING_STOPPED':
            setRecordingUI(false);
            break;
        case 'TRANSCRIPTION_UPDATE':
            const latest = msg.data;
            updateWordCount(latest.wordCount);
            renderLog(latest.fullLog); // 🔥 РИСУЕМ ТЕКСТ
            break;
    }
});

// 🔥 Функция отрисовки (была пропущена)
const transcriptionContainer = document.querySelector('.transcription-container') || document.body;
// (в popup.html может быть другой класс, сейчас проверим, но если что добавит в body или найдем scroll-area)
// В вашем HTML это <div class="scroll-area" id="transcriptionLog">

const logContainer = document.getElementById('transcriptionLog');

function renderLog(log) {
    if (!logContainer) return;

    // Очищаем и перерисовываем (простой вариант)
    // Оптимизация: можно добавлять только новые, но пока так надежнее
    logContainer.innerHTML = '';

    log.forEach(item => {
        const div = document.createElement('div');
        div.className = 'segment';
        div.innerHTML = `
            <div class="segment-time">${item.time}</div>
            <div class="segment-text">${item.text}</div>
        `;
        logContainer.appendChild(div);
    });

    // Автоскролл
    logContainer.scrollTop = logContainer.scrollHeight;
}

function sendMsg(msg) {
    return new Promise(resolve => chrome.runtime.sendMessage(msg, resolve));
}

// Init Render on Load
document.addEventListener('DOMContentLoaded', async () => {
    // ... существующий код init ...
    const state = await sendMsg({ type: 'GET_STATE' });
    if (state) {
        // ...
        if (state.transcriptionLog) renderLog(state.transcriptionLog);
    }
});

// Quick Actions
document.getElementById('btnOpenPanel').addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) chrome.sidePanel.open({ tabId: tab.id });
    window.close(); // Close popup
});
