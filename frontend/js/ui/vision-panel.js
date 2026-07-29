// Live detection panel.
// Supports two camera sources:
//   "webcam"  — browser getUserMedia (PC webcam, existing behaviour)
//   "espcam"  — ESP32-CAM /capture polled via the backend proxy /api/camera/frame
//
// The detection loop is identical for both: grab a JPEG blob, POST to /api/detect,
// draw boxes. Switching source just changes how the blob is obtained.

import { fetchDetectStatus, detectImage, pingCamera, fetchCameraFrame } from '../api.js';
import { setLatestDetection, clearLatestDetection } from './vision-state.js';

const DETECT_GAP_MS = 60;   // ms between detections (self-scheduling loop)

let stream    = null;   // MediaStream when using webcam
let running   = false;
let firstFrame = true;
let source    = 'webcam';   // 'webcam' | 'espcam'
let espcamUrl = '';

export function isCameraRunning() { return running; }

// ── status helper ─────────────────────────────────────────────────────────────
function setStatus(msg, ok) {
    const el = document.getElementById('vision-model-status');
    if (!el) return;
    el.textContent = msg;
    el.style.color = ok ? '#0a0' : '#c00';
}

// ── draw bounding boxes on canvas ─────────────────────────────────────────────
function drawDetections(imgEl, canvas, detections, pickupZone) {
    const ctx = canvas.getContext('2d');
    canvas.width  = imgEl.videoWidth  || imgEl.naturalWidth  || 640;
    canvas.height = imgEl.videoHeight || imgEl.naturalHeight || 480;
    ctx.drawImage(imgEl, 0, 0, canvas.width, canvas.height);

    // Draw the pickup zone (region of interest). Only pieces inside it are
    // detected; anything outside — e.g. already-sorted bricks — is ignored.
    // Shown so you can calibrate PICKUP_ZONE in detection.py to hug your pickup area.
    if (pickupZone && pickupZone.enabled) {
        const zx = pickupZone.left   * canvas.width;
        const zy = pickupZone.top    * canvas.height;
        const zw = (pickupZone.right - pickupZone.left) * canvas.width;
        const zh = (pickupZone.bottom - pickupZone.top) * canvas.height;
        ctx.save();
        ctx.strokeStyle = '#facc15';   // amber
        ctx.lineWidth = 2;
        ctx.setLineDash([8, 5]);
        ctx.strokeRect(zx, zy, zw, zh);
        ctx.setLineDash([]);
        ctx.fillStyle = '#facc15';
        ctx.font = '13px sans-serif';
        ctx.fillText('pickup zone', zx + 4, zy + 16);
        ctx.restore();
    }

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

// ── mirror the annotated feed into the Program tab's inline panel ────────────
// The Program tab shows a live copy of the same annotated canvas while a program
// runs, so you can watch detections without switching tabs. No-op if that panel
// isn't on screen (canvas hidden), so it costs nothing when unused.
function mirrorToProgramFeed(sourceCanvas) {
    const dest = document.getElementById('program-feed-canvas');
    if (!dest || dest.offsetParent === null) return;   // panel not visible
    if (dest.width !== sourceCanvas.width || dest.height !== sourceCanvas.height) {
        dest.width  = sourceCanvas.width;
        dest.height = sourceCanvas.height;
    }
    dest.getContext('2d').drawImage(sourceCanvas, 0, 0);
    const status = document.getElementById('program-feed-status');
    if (status) status.style.display = 'none';
}

// ── render text results list ──────────────────────────────────────────────────
function renderResults(result) {
    const el = document.getElementById('vision-detections');
    if (!el) return;
    if (!result.count) {
        el.innerHTML = '<p class="help-text">No objects detected in frame.</p>';
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

// ── grab a JPEG blob from whichever source is active ─────────────────────────
async function grabBlob(video, canvas) {
    if (source === 'espcam') {
        // Backend proxies the frame from the ESP32-CAM, rotating it if the
        // camera is mounted sideways so boxes stay aligned with the image.
        const rotate = parseInt(document.getElementById('espcam-rotate').value, 10) || 0;
        return await fetchCameraFrame(espcamUrl, rotate);
    }
    // Webcam: draw current video frame to offscreen canvas, encode to JPEG.
    const tmp = document.createElement('canvas');
    tmp.width  = video.videoWidth  || 640;
    tmp.height = video.videoHeight || 480;
    tmp.getContext('2d').drawImage(video, 0, 0, tmp.width, tmp.height);
    return new Promise(res => tmp.toBlob(res, 'image/jpeg', 0.85));
}

// ── draw a blob onto the canvas (for ESP32-CAM preview) ──────────────────────
async function blobToImage(blob) {
    return new Promise((resolve, reject) => {
        const url = URL.createObjectURL(blob);
        const img = new Image();
        img.onload  = () => { URL.revokeObjectURL(url); resolve(img); };
        img.onerror = reject;
        img.src = url;
    });
}

// ── main detection loop ───────────────────────────────────────────────────────
async function detectLoop(video, canvas) {
    if (!running) return;
    try {
        const blob = await grabBlob(video, canvas);
        if (!blob) { if (running) setTimeout(() => detectLoop(video, canvas), DETECT_GAP_MS); return; }

        if (firstFrame) setStatus('Loading model & detecting (first frame may take a few seconds)...', true);

        const conf   = parseFloat(document.getElementById('vision-conf').value);
        const result = await detectImage(blob, conf);

        if (firstFrame) { firstFrame = false; setStatus('Camera running — detecting...', true); }

        // For ESP32-CAM, decode the blob to draw it on the canvas first.
        if (source === 'espcam') {
            const img = await blobToImage(blob);
            drawDetections(img, canvas, result.detections, result.pickup_zone);
        } else {
            drawDetections(video, canvas, result.detections, result.pickup_zone);
        }

        setLatestDetection(result);
        renderResults(result);
        mirrorToProgramFeed(canvas);
    } catch (e) {
        setStatus(`Detection error: ${e.message}`, false);
    } finally {
        if (running) setTimeout(() => detectLoop(video, canvas), DETECT_GAP_MS);
    }
}

// ── start webcam ──────────────────────────────────────────────────────────────
async function startWebcam(video, canvas) {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        await video.play();
        video.style.display = 'none';   // canvas shows the annotated feed
        canvas.style.display = '';
    } catch (e) {
        throw new Error(`Cannot access webcam: ${e.message}`);
    }
}

// ── start ESP32-CAM ───────────────────────────────────────────────────────────
async function startEspcam(canvas) {
    const url = document.getElementById('espcam-url').value.trim();
    if (!url) throw new Error('Enter the ESP32-CAM IP address first (e.g. http://192.168.4.2)');
    espcamUrl = url;
    // Quick reachability check before committing to the loop.
    const ping = await pingCamera(url);
    if (!ping.reachable) throw new Error(`ESP32-CAM not reachable at ${url} — check IP and WiFi`);
    canvas.style.display = '';
}

// ── public start / stop ───────────────────────────────────────────────────────
export async function startCamera() {
    // Guard against stacking loops: startCamera() can be triggered from the Vision
    // Start button, the Program tab's Run (auto-start), and mobile. Without this,
    // each call spawns ANOTHER detectLoop while the old one keeps running, so the
    // browser runs several detect loops at once and the feed slows progressively.
    if (running) return;

    const video  = document.getElementById('vision-video');
    const canvas = document.getElementById('vision-canvas');
    // Camera source: USB/PC webcam only. (ESP32-CAM support kept in the code path
    // below for reference, but the UI no longer offers it — a wired USB webcam has
    // better optics/focus/low-light, which detection depends on.)
    const srcRadio = document.querySelector('input[name="vision-source"]:checked');
    source = srcRadio ? srcRadio.value : 'webcam';

    setStatus('Connecting...', true);
    try {
        if (source === 'webcam') {
            await startWebcam(video, canvas);
        } else {
            await startEspcam(canvas);
        }
    } catch (e) {
        setStatus(e.message, false);
        return;
    }

    document.getElementById('vision-start-btn').style.display = 'none';
    document.getElementById('vision-stop-btn').style.display  = '';
    running    = true;
    firstFrame = true;
    detectLoop(video, canvas);
}

export function stopCamera() {
    running = false;
    clearLatestDetection();
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    const video = document.getElementById('vision-video');
    if (video) { video.srcObject = null; }
    document.getElementById('vision-start-btn').style.display = '';
    document.getElementById('vision-stop-btn').style.display  = 'none';
    setStatus('Camera stopped.', true);
}

// ── init ──────────────────────────────────────────────────────────────────────
export async function initVisionPanel() {
    const startBtn = document.getElementById('vision-start-btn');
    if (!startBtn) return;

    // ESP32-CAM source selector + ping button are optional — the UI now ships
    // webcam-only, so guard these so init doesn't crash when they're absent.
    document.querySelectorAll('input[name="vision-source"]').forEach(radio => {
        radio.addEventListener('change', () => {
            const selected = document.querySelector('input[name="vision-source"]:checked').value;
            const row = document.getElementById('espcam-url-row');
            if (row) row.style.display = selected === 'espcam' ? '' : 'none';
        });
    });

    const pingBtn = document.getElementById('espcam-ping-btn');
    if (pingBtn) pingBtn.addEventListener('click', async () => {
        const url    = document.getElementById('espcam-url').value.trim();
        const result = document.getElementById('espcam-ping-result');
        if (!url) { result.textContent = 'Enter an IP first.'; return; }
        result.textContent = 'Testing...';
        try {
            const ping = await pingCamera(url);
            result.textContent = ping.reachable ? 'Reachable!' : 'Not reachable — check IP and WiFi';
            result.style.color = ping.reachable ? '#0a0' : '#c00';
        } catch {
            result.textContent = 'Request failed';
            result.style.color = '#c00';
        }
    });

    // Confidence slider display
    const confSlider = document.getElementById('vision-conf');
    const confValue  = document.getElementById('vision-conf-value');
    confSlider.addEventListener('input', () => {
        confValue.textContent = parseFloat(confSlider.value).toFixed(2);
    });

    startBtn.addEventListener('click', startCamera);
    document.getElementById('vision-stop-btn').addEventListener('click', stopCamera);

    // Check model availability
    const available = await fetchDetectStatus();
    if (available) {
        setStatus('Model loaded. Choose a camera source and click Start Camera.', true);
    } else {
        setStatus('No trained model found. Place best.pt at models/lego_detector.pt or train one in the Train Model tab.', false);
        startBtn.disabled = true;
    }
}
