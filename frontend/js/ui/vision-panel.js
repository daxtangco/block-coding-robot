// Live webcam detection panel.
// Captures webcam frames, posts them to /api/detect, draws boxes + bins.

import { fetchDetectStatus, detectImage } from '../api.js';
import { setLatestDetection, clearLatestDetection } from './vision-state.js';

// Small gap between detections so the UI/event loop can breathe. The loop is
// self-scheduling (next runs only after the previous finishes), so requests
// never stack up regardless of how slow CPU inference is.
const DETECT_GAP_MS = 60;

let stream = null;
let running = false;
let firstFrame = true;

// The program-runner gates Run on this so camera_sees always has fresh data.
export function isCameraRunning() {
    return running;
}

function setStatus(msg, ok) {
    const el = document.getElementById('vision-model-status');
    if (!el) return;
    el.textContent = msg;
    el.style.color = ok ? '#0a0' : '#c00';
}

function drawDetections(video, canvas, detections) {
    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    ctx.lineWidth = 2;
    ctx.font = '16px sans-serif';
    for (const d of detections) {
        const [x1, y1, x2, y2] = d.bbox;
        ctx.strokeStyle = '#00ff00';
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

        const label = `${d.class_name} ${(d.confidence * 100).toFixed(0)}%`
            + (d.target_bin ? ` -> ${d.target_bin}` : '');
        const w = ctx.measureText(label).width + 8;
        ctx.fillStyle = '#00ff00';
        ctx.fillRect(x1, Math.max(0, y1 - 20), w, 20);
        ctx.fillStyle = '#000';
        ctx.fillText(label, x1 + 4, Math.max(14, y1 - 5));
    }
}

function renderResults(result) {
    const el = document.getElementById('vision-detections');
    if (!el) return;
    if (!result.count) {
        el.innerHTML = '<p class="help-text">No bricks detected in frame.</p>';
        return;
    }
    const rows = result.detections.map(d =>
        `<li><strong>${d.class_name}</strong> `
        + `(${(d.confidence * 100).toFixed(0)}%) &rarr; `
        + `${d.target_bin || 'no bin'}</li>`
    ).join('');
    const bins = Object.entries(result.bin_statistics || {})
        .map(([b, n]) => `${b}: ${n}`).join(' · ');
    el.innerHTML = `<ul>${rows}</ul><p class="help-text">${bins}</p>`;
}

async function detectLoop(video, canvas) {
    if (!running || !stream) return;
    try {
        // Grab current frame into an offscreen canvas, encode to JPEG blob.
        const tmp = document.createElement('canvas');
        tmp.width = video.videoWidth || 640;
        tmp.height = video.videoHeight || 480;
        tmp.getContext('2d').drawImage(video, 0, 0, tmp.width, tmp.height);
        const blob = await new Promise(res => tmp.toBlob(res, 'image/jpeg', 0.85));

        if (firstFrame) {
            setStatus('Loading model & detecting (first frame may take a few seconds)...', true);
        }
        const conf = parseFloat(document.getElementById('vision-conf').value);
        const result = await detectImage(blob, conf);
        if (firstFrame) {
            firstFrame = false;
            setStatus('Camera running — detecting...', true);
        }
        // Publish for the program-runner's camera_sees blocks.
        setLatestDetection(result);
        drawDetections(video, canvas, result.detections);
        renderResults(result);
    } catch (e) {
        setStatus(`Detection error: ${e.message}`, false);
    } finally {
        // Self-schedule: next detection only starts after this one finishes,
        // so slow CPU inference never piles up a backlog of requests.
        if (running) setTimeout(() => detectLoop(video, canvas), DETECT_GAP_MS);
    }
}

async function startCamera() {
    const video = document.getElementById('vision-video');
    const canvas = document.getElementById('vision-canvas');
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        await video.play();
        canvas.style.display = '';
        document.getElementById('vision-start-btn').style.display = 'none';
        document.getElementById('vision-stop-btn').style.display = '';
        setStatus('Camera running — detecting...', true);
        running = true;
        firstFrame = true;
        detectLoop(video, canvas);
    } catch (e) {
        setStatus(`Cannot access camera: ${e.message}`, false);
    }
}

function stopCamera() {
    running = false;
    clearLatestDetection();  // stale frames must not drive camera_sees
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    document.getElementById('vision-start-btn').style.display = '';
    document.getElementById('vision-stop-btn').style.display = 'none';
    setStatus('Camera stopped.', true);
}

export async function initVisionPanel() {
    const startBtn = document.getElementById('vision-start-btn');
    const stopBtn = document.getElementById('vision-stop-btn');
    const confSlider = document.getElementById('vision-conf');
    const confValue = document.getElementById('vision-conf-value');
    if (!startBtn) return;  // panel not present

    confSlider.addEventListener('input', () => {
        confValue.textContent = parseFloat(confSlider.value).toFixed(2);
    });
    startBtn.addEventListener('click', startCamera);
    stopBtn.addEventListener('click', stopCamera);


    const available = await fetchDetectStatus();
    if (available) {
        setStatus('Model loaded. Click Start Camera.', true);
    } else {
        setStatus('No trained model found. Place best.pt at models/lego_detector.pt', false);
        startBtn.disabled = true;
    }
}
