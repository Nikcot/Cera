/**
 * Цера — Side Panel Controller
 */

// ── DOM ──
const spStatusDot = document.getElementById('spStatusDot');
const spStatusText = document.getElementById('spStatusText');
const spTimer = document.getElementById('spTimer');
const waveAnim = document.getElementById('waveAnim');

const spRecordBtn = document.getElementById('spRecordBtn');
const spSummaryBtn = document.getElementById('spSummaryBtn');
const spCopyBtn = document.getElementById('spCopyBtn');
const spClearBtn = document.getElementById('spClearBtn');

const tabTranscript = document.getElementById('tabTranscript');
const tabSummary = document.getElementById('tabSummary');
const contentTranscript = document.getElementById('contentTranscript');
const contentSummary = document.getElementById('contentSummary');
const emptyTranscript = document.getElementById('emptyTranscript');
const emptySummary = document.getElementById('emptySummary');

let isRecording = false;
let timerInterval = null;
let elapsedSeconds = 0;

// ── Init ──
document.addEventListener('DOMContentLoaded', async () => {
    const state = await sendMsg({ type: 'GET_STATE' });
    if (state) {
        isRecording = state.isRecording;

        // Restore transcription log
        if (state.transcriptionLog?.length) {
            emptyTranscript?.remove();
            state.transcriptionLog.forEach(e => appendTranscript(e, false));
        }

        // Restore summary log
        if (state.summaryLog?.length) {
            emptySummary?.remove();
            state.summaryLog.forEach(e => appendSummary(e, false));
        }

        if (isRecording) {
            setRecordingUI(true);
            startTimer(state.elapsed || 0);
        }
    }
});

// ── Tabs ──
tabTranscript.addEventListener('click', () => switchTab('transcript'));
tabSummary.addEventListener('click', () => switchTab('summary'));

function switchTab(tab) {
    tabTranscript.classList.toggle('active', tab === 'transcript');
    tabSummary.classList.toggle('active', tab === 'summary');
    contentTranscript.classList.toggle('hidden', tab !== 'transcript');
    contentSummary.classList.toggle('hidden', tab !== 'summary');
}

// ── Record ──
spRecordBtn.addEventListener('click', async () => {
    if (!isRecording) {
        await sendMsg({ type: 'START_RECORDING', data: { source: 'tab' } });
    } else {
        await sendMsg({ type: 'STOP_RECORDING' });
    }
});

function setRecordingUI(recording) {
    isRecording = recording;

    spStatusDot.classList.toggle('active', recording);
    spStatusText.textContent = recording ? 'Запись идёт...' : 'Готово к записи';
    spTimer.classList.toggle('hidden', !recording);
    waveAnim.classList.toggle('hidden', !recording);
    waveAnim.classList.toggle('recording', recording);

    if (recording) {
        spRecordBtn.className = 'sp-ctrl-btn danger';
        spRecordBtn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
        <rect x="6" y="6" width="12" height="12" rx="2"/>
      </svg>
      Стоп`;
    } else {
        spRecordBtn.className = 'sp-ctrl-btn primary';
        spRecordBtn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="9" y="2" width="6" height="12" rx="3"/>
        <path d="M5 10a7 7 0 0 0 14 0"/>
        <path d="M12 18v4"/>
        <path d="M8 22h8"/>
      </svg>
      Записать`;
    }
}

// ── Timer ──
function startTimer(initial) {
    elapsedSeconds = initial || 0;
    updateTimerDisplay();
    timerInterval = setInterval(() => {
        elapsedSeconds++;
        updateTimerDisplay();
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function updateTimerDisplay() {
    const m = String(Math.floor(elapsedSeconds / 60)).padStart(2, '0');
    const s = String(elapsedSeconds % 60).padStart(2, '0');
    spTimer.textContent = `${m}:${s}`;
}

// ── Content renderers ──
function appendTranscript(entry, animate = true) {
    // Remove empty state
    const empty = contentTranscript.querySelector('.empty-state');
    if (empty) empty.remove();

    const div = document.createElement('div');
    div.className = 'transcript-item';
    if (!animate) div.style.animation = 'none';
    div.innerHTML = `
    <div class="transcript-time">${entry.timestamp}</div>
    <div class="transcript-text">${escapeHtml(entry.text)}</div>
  `;
    contentTranscript.appendChild(div);
    contentTranscript.scrollTop = contentTranscript.scrollHeight;
}

function appendSummary(entry, animate = true) {
    const empty = contentSummary.querySelector('.empty-state');
    if (empty) empty.remove();

    const div = document.createElement('div');
    div.className = 'summary-item';
    if (!animate) div.style.animation = 'none';
    div.innerHTML = `
    <div class="summary-time">✨ Саммари · ${entry.timestamp}</div>
    <div class="summary-text">${escapeHtml(entry.text)}</div>
  `;
    contentSummary.appendChild(div);
    contentSummary.scrollTop = contentSummary.scrollHeight;
}

function showSummaryLoading() {
    const empty = contentSummary.querySelector('.empty-state');
    if (empty) empty.remove();

    // Remove previous spinner if exists
    const oldSpinner = contentSummary.querySelector('.loading-indicator');
    if (oldSpinner) oldSpinner.remove();

    const div = document.createElement('div');
    div.className = 'summary-item loading-indicator';
    div.innerHTML = `
    <div class="summary-time" style="display:flex;align-items:center;gap:8px;">
      <div class="spinner"></div>
      Создание саммари...
    </div>
  `;
    contentSummary.appendChild(div);
    contentSummary.scrollTop = contentSummary.scrollHeight;
}

function removeSummaryLoading() {
    const loader = contentSummary.querySelector('.loading-indicator');
    if (loader) loader.remove();
}

// ── Quick actions ──
spSummaryBtn.addEventListener('click', async () => {
    await sendMsg({ type: 'REQUEST_SUMMARY' });
    showToast('Создание саммари...');
    switchTab('summary');
});

spCopyBtn.addEventListener('click', async () => {
    const res = await sendMsg({ type: 'COPY_TEXT' });
    if (res) {
        const full = (res.text || '') + (res.summary ? '\n\n=== AI Саммари ===\n\n' + res.summary : '');
        if (full.trim()) {
            await navigator.clipboard.writeText(full);
            showToast('Скопировано в буфер обмена!');
        } else {
            showToast('Нет текста для копирования');
        }
    }
});

spClearBtn.addEventListener('click', async () => {
    await sendMsg({ type: 'CLEAR_ALL' });
});

// ── Messages from background ──
chrome.runtime.onMessage.addListener((msg) => {
    switch (msg.type) {
        case 'RECORDING_STARTED':
            setRecordingUI(true);
            startTimer(0);
            break;

        case 'RECORDING_STOPPED':
            setRecordingUI(false);
            stopTimer();
            break;

        case 'TRANSCRIPTION_UPDATE':
            if (msg.data?.entry) {
                appendTranscript(msg.data.entry);
            }
            break;

        case 'SUMMARY':
            removeSummaryLoading();
            if (msg.data) {
                appendSummary(msg.data);
                // Flash tab to indicate new summary
                tabSummary.style.color = 'var(--accent)';
                setTimeout(() => { tabSummary.style.color = ''; }, 2000);
            }
            break;

        case 'SUMMARY_LOADING':
            showSummaryLoading();
            break;

        case 'SUMMARY_ERROR':
            removeSummaryLoading();
            showToast(msg.data?.message || 'Ошибка саммари');
            break;

        case 'CLEARED':
            // Reset content areas
            contentTranscript.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📝</div>
          <div class="empty-title">Транскрипция появится здесь</div>
          <div class="empty-desc">Нажмите «Записать» чтобы начать распознавание речи</div>
        </div>`;
            contentSummary.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">✨</div>
          <div class="empty-title">AI саммари</div>
          <div class="empty-desc">Саммари будет создано автоматически или нажмите кнопку «Саммари»</div>
        </div>`;
            showToast('Всё очищено');
            break;

        case 'ERROR':
            spStatusText.textContent = '⚠ ' + (msg.data?.message || 'Ошибка');
            if (isRecording) {
                setRecordingUI(false);
                stopTimer();
            }
            break;
    }
});

// ── Helpers ──
function sendMsg(msg) {
    return new Promise((resolve) => {
        chrome.runtime.sendMessage(msg, (response) => {
            resolve(response);
        });
    });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function showToast(text) {
    const toast = document.getElementById('toast');
    toast.textContent = text;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
}
