/**
 * Цера — Offscreen Document (Легкая версия для сервера)
 */

let isCapturing = false;
let mediaStream = null;
let audioContext = null;
let processorNode = null;
const TARGET_SAMPLE_RATE = 16000;

// ── Messages ──
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.target !== 'offscreen') return false;

    if (msg.type === 'START_CAPTURE') {
        startCapture(msg.data);
        sendResponse({ ok: true });
        return true;
    }
    else if (msg.type === 'STOP_CAPTURE') {
        stopCapture();
        sendResponse({ ok: true });
    }
});

// ── Audio Processing ──
function downsampleToMono16k(inputBuffer, sourceSampleRate, numChannels) {
    const length = inputBuffer.length / numChannels;
    let mono;

    // Stereo -> Mono
    if (numChannels === 2) {
        mono = new Float32Array(length);
        for (let i = 0; i < length; i++) {
            mono[i] = (inputBuffer[i * 2] + inputBuffer[i * 2 + 1]) / 2;
        }
    } else {
        mono = inputBuffer; // Already mono (or handled as such)
    }

    if (sourceSampleRate === TARGET_SAMPLE_RATE) return mono;

    // Resample
    const ratio = TARGET_SAMPLE_RATE / sourceSampleRate;
    const newLength = Math.round(mono.length * ratio);
    const result = new Float32Array(newLength);

    for (let i = 0; i < newLength; i++) {
        const srcIdx = i / ratio;
        const idx0 = Math.floor(srcIdx);
        const idx1 = Math.min(idx0 + 1, mono.length - 1);
        const frac = srcIdx - idx0;
        result[i] = mono[idx0] * (1 - frac) + mono[idx1] * frac;
    }
    return result;
}

// ── Capture Logic ──
async function startCapture(data) {
    if (isCapturing) return;

    const { streamId, source } = data; // Move up

    try {
        if (source === 'tab' && streamId) {
            mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    mandatory: {
                        chromeMediaSource: 'tab',
                        chromeMediaSourceId: streamId
                    }
                }
            });
        } else {
            mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
        }
    } catch (e) {
        console.error('Capture error:', e);
        chrome.runtime.sendMessage({ type: 'ERROR', data: { message: e.message } });
        return;
    }

    isCapturing = true;

    // Setup Audio Context
    const tracks = mediaStream.getAudioTracks();
    const settings = tracks[0].getSettings();
    const sourceRate = settings.sampleRate || 48000;
    const channels = settings.channelCount || 2;

    audioContext = new AudioContext({ sampleRate: sourceRate });

    // 🔥 ВАЖНО: "Пинаем" контекст, чтобы он не спал
    if (audioContext.state === 'suspended') {
        await audioContext.resume();
    }

    const sourceNode = audioContext.createMediaStreamSource(mediaStream);

    // ScriptProcessor (4096 samples)
    processorNode = audioContext.createScriptProcessor(4096, channels, channels);

    let silenceFrames = 0;

    processorNode.onaudioprocess = (e) => {
        if (!isCapturing) return;

        const input = e.inputBuffer;
        let pcm;

        if (channels === 1) {
            pcm = input.getChannelData(0);
        } else {
            // Берем ТОЛЬКО ЛЕВЫЙ канал (надежнее, чем mix)
            pcm = input.getChannelData(0);
        }

        // Усиление x3.0 (чтобы не было RMS 0.006)
        for (let i = 0; i < pcm.length; i++) {
            pcm[i] *= 3.0;
        }

        // 🔍 ЛОГ ГРОМКОСТИ (для отладки)
        // Считаем среднюю громкость (RMS)
        let sum = 0;
        // Берем каждый 100-й сэмпл для скорости
        for (let i = 0; i < pcm.length; i += 100) sum += pcm[i] * pcm[i];
        const rms = Math.sqrt(sum / (pcm.length / 100));

        if (rms < 0.001) {
            silenceFrames++;
            if (silenceFrames % 100 === 0) console.log('[Cera] 🔇 Тишина... (RMS: ' + rms.toFixed(6) + ')');
        } else {
            if (silenceFrames > 0) console.log('[Cera] 🔊 ЗВУК ПОШЕЛ! (RMS: ' + rms.toFixed(4) + ')');
            silenceFrames = 0;
        }

        // Resample & Send (укорочено для надежности)
        const resampled = downsampleToMono16k(pcm, sourceRate, 1); // 1 канал (т.к. мы взяли левый)

        // Send
        chrome.runtime.sendMessage({
            type: 'AUDIO_CHUNK',
            data: Array.from(resampled) // JSON serializable array
        });
    };

    sourceNode.connect(processorNode);
    if (source === 'tab') sourceNode.connect(audioContext.destination); // Hear audio
    processorNode.connect(audioContext.destination);

    console.log(`[Cera] Capture started: ${source}, ${sourceRate}Hz`);
}

function stopCapture() {
    isCapturing = false;
    if (processorNode) processorNode.disconnect();
    if (audioContext) audioContext.close();
    if (mediaStream) mediaStream.getTracks().forEach(t => t.stop());
    console.log('[Cera] Capture stopped');
}
