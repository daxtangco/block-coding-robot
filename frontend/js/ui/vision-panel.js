// Live detection panel.
// Supports two camera sources:
//   "webcam"  — browser getUserMedia (PC webcam, existing behaviour)
//   "espcam"  — ESP32-CAM /capture polled via the backend proxy /api/camera/frame
//
// The detection loop is identical for both: grab a JPEG blob, POST to /api/detect,
// draw boxes. Switching source just changes how the blob is obtained.

import { fetchDetectStatus, detectImage, pingCamera, fetchCameraFrame,
         fetchDropZones, saveDropZones } from '../api.js';
import { setLatestDetection, clearLatestDetection } from './vision-state.js';

const DETECT_GAP_MS = 60;   // ms between detections (self-scheduling loop)

let stream    = null;   // MediaStream when using webcam
let running   = false;
let firstFrame = true;
let source    = 'webcam';   // 'webcam' | 'espcam'
let espcamUrl = '';

// ── Drop-zone editor state ──────────────────────────────────────────────────
// dropZones is the single source of truth for the masks; zones are in FRACTIONS
// of the frame (0..1) so they're resolution-independent. editMode toggles the
// interactive editor (draw/move/resize/delete on the canvas).
let dropZones = { enabled: true, zones: [] };
let editMode  = false;
let dzDirty   = false;      // unsaved changes
let drag      = null;       // active gesture: {type, index, handle, startX, startY, orig}
const HANDLE_PX = 10;       // corner-resize hit radius (screen px)

export function isCameraRunning() { return running; }
export function isDropZoneEditing() { return editMode; }

// ── status helper ─────────────────────────────────────────────────────────────
function setStatus(msg, ok) {
    const el = document.getElementById('vision-model-status');
    if (!el) return;
    el.textContent = msg;
    el.style.color = ok ? '#0a0' : '#c00';
}

// ── draw bounding boxes on canvas ─────────────────────────────────────────────
function drawDetections(imgEl, canvas, detections) {
    const ctx = canvas.getContext('2d');
    canvas.width  = imgEl.videoWidth  || imgEl.naturalWidth  || 640;
    canvas.height = imgEl.videoHeight || imgEl.naturalHeight || 480;
    ctx.drawImage(imgEl, 0, 0, canvas.width, canvas.height);

    // Draw the drop-zone masks (exclusion ROI). The whole frame is valid pickup
    // space EXCEPT these zones — pieces whose center lands inside one (e.g. bricks
    // already dropped into a bin) are ignored. Uses the module-level dropZones so
    // the interactive editor's live edits are reflected immediately. When masks
    // are toggled off they're still drawn (faded) while editing, so you can see
    // what you're placing.
    const showZones = dropZones && (dropZones.enabled || editMode);
    if (showZones) {
        ctx.save();
        const active = dropZones.enabled;
        (dropZones.zones || []).forEach((z, i) => {
            const zx = z.left * canvas.width;
            const zy = z.top  * canvas.height;
            const zw = (z.right - z.left) * canvas.width;
            const zh = (z.bottom - z.top) * canvas.height;
            ctx.fillStyle = active ? 'rgba(239, 68, 68, 0.18)' : 'rgba(148, 163, 184, 0.15)';
            ctx.fillRect(zx, zy, zw, zh);
            ctx.strokeStyle = active ? '#ef4444' : '#94a3b8';
            ctx.lineWidth = 2;
            ctx.setLineDash([8, 5]);
            ctx.strokeRect(zx, zy, zw, zh);
            ctx.setLineDash([]);
            ctx.fillStyle = active ? '#ef4444' : '#94a3b8';
            ctx.font = '13px sans-serif';
            ctx.fillText(active ? 'drop zone (ignored)' : 'drop zone (off)', zx + 4, zy + 16);

            // Editor affordances: corner resize handles + a delete hint.
            if (editMode) {
                ctx.fillStyle = '#ffffff';
                ctx.strokeStyle = active ? '#ef4444' : '#64748b';
                for (const [hx, hy] of [[zx, zy], [zx + zw, zy], [zx, zy + zh], [zx + zw, zy + zh]]) {
                    ctx.beginPath();
                    ctx.rect(hx - HANDLE_PX / 2, hy - HANDLE_PX / 2, HANDLE_PX, HANDLE_PX);
                    ctx.fill();
                    ctx.stroke();
                }
            }
        });
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

        // Sync server-side masks into the module state EXCEPT while editing or when
        // there are unsaved edits — otherwise the loop would overwrite the user's
        // in-progress drag every frame.
        if (!editMode && !dzDirty && result.drop_zones) dropZones = result.drop_zones;

        // For ESP32-CAM, decode the blob to draw it on the canvas first.
        if (source === 'espcam') {
            const img = await blobToImage(blob);
            drawDetections(img, canvas, result.detections);
        } else {
            drawDetections(video, canvas, result.detections);
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

// ── drop-zone editor ──────────────────────────────────────────────────────────
// All geometry is kept in FRACTIONS (0..1). Pointer events arrive in canvas
// pixels, so we convert against the canvas's intrinsic size (which tracks the
// video resolution), then clamp back to 0..1. This keeps zones correct no matter
// the display size or camera resolution.
function canvasFrac(canvas, evt) {
    const rect = canvas.getBoundingClientRect();
    const x = (evt.clientX - rect.left) / rect.width;
    const y = (evt.clientY - rect.top)  / rect.height;
    return { fx: Math.max(0, Math.min(1, x)), fy: Math.max(0, Math.min(1, y)) };
}

// Which zone/handle (if any) is under the pointer. Returns {index, handle} where
// handle is 'nw'|'ne'|'sw'|'se' for a corner, 'body' for inside, or null.
function hitTest(canvas, fx, fy) {
    const hx = HANDLE_PX / canvas.width;   // handle radius in fraction units
    const hy = HANDLE_PX / canvas.height;
    // Iterate top-most (last drawn) first so overlapping zones pick the visible one.
    for (let i = dropZones.zones.length - 1; i >= 0; i--) {
        const z = dropZones.zones[i];
        const corners = { nw: [z.left, z.top], ne: [z.right, z.top],
                          sw: [z.left, z.bottom], se: [z.right, z.bottom] };
        for (const [h, [cx, cy]] of Object.entries(corners)) {
            if (Math.abs(fx - cx) <= hx && Math.abs(fy - cy) <= hy) return { index: i, handle: h };
        }
        if (fx >= z.left && fx <= z.right && fy >= z.top && fy <= z.bottom) return { index: i, handle: 'body' };
    }
    return null;
}

function cursorFor(handle) {
    return handle === 'nw' || handle === 'se' ? 'nwse-resize'
         : handle === 'ne' || handle === 'sw' ? 'nesw-resize'
         : handle === 'body' ? 'move' : 'crosshair';
}

function normalizeZone(z) {
    const [left, right] = [z.left, z.right].sort((a, b) => a - b);
    const [top, bottom] = [z.top, z.bottom].sort((a, b) => a - b);
    return { left, top, right, bottom };
}

function onDzDown(canvas, evt) {
    if (!editMode) return;
    const { fx, fy } = canvasFrac(canvas, evt);
    const hit = hitTest(canvas, fx, fy);
    if (hit) {
        drag = { type: hit.handle === 'body' ? 'move' : 'resize', index: hit.index,
                 handle: hit.handle, startX: fx, startY: fy,
                 orig: { ...dropZones.zones[hit.index] } };
    } else {
        // Start a brand-new zone; grows as the pointer drags.
        dropZones.zones.push({ left: fx, top: fy, right: fx, bottom: fy });
        drag = { type: 'create', index: dropZones.zones.length - 1,
                 handle: 'se', startX: fx, startY: fy };
    }
    evt.preventDefault();
}

function onDzMove(canvas, evt) {
    if (!editMode) return;
    const { fx, fy } = canvasFrac(canvas, evt);
    if (!drag) {                       // just hovering → cursor feedback
        const hit = hitTest(canvas, fx, fy);
        canvas.style.cursor = cursorFor(hit ? hit.handle : null);
        return;
    }
    const z = dropZones.zones[drag.index];
    if (drag.type === 'move') {
        const dx = fx - drag.startX, dy = fy - drag.startY;
        const w = drag.orig.right - drag.orig.left, h = drag.orig.bottom - drag.orig.top;
        let left = Math.max(0, Math.min(1 - w, drag.orig.left + dx));
        let top  = Math.max(0, Math.min(1 - h, drag.orig.top  + dy));
        z.left = left; z.top = top; z.right = left + w; z.bottom = top + h;
    } else {   // resize or create: move the dragged corner
        if (drag.handle.includes('w')) z.left  = fx; else z.right  = fx;
        if (drag.handle.includes('n')) z.top   = fy; else z.bottom = fy;
    }
    dzDirty = true;
    updateDzButtons();
}

function onDzUp() {
    if (!drag) return;
    // Commit: normalize orientation and drop zero-area rectangles (stray clicks).
    const z = normalizeZone(dropZones.zones[drag.index]);
    if (z.right - z.left < 0.01 || z.bottom - z.top < 0.01) {
        dropZones.zones.splice(drag.index, 1);
    } else {
        dropZones.zones[drag.index] = z;
    }
    drag = null;
    updateDzButtons();
}

function onDzDblClick(canvas, evt) {
    if (!editMode) return;
    const { fx, fy } = canvasFrac(canvas, evt);
    const hit = hitTest(canvas, fx, fy);
    if (hit) {
        dropZones.zones.splice(hit.index, 1);
        dzDirty = true;
        updateDzButtons();
        evt.preventDefault();
    }
}

function updateDzButtons() {
    const save  = document.getElementById('dropzone-save-btn');
    const clear = document.getElementById('dropzone-clear-btn');
    const hint  = document.getElementById('dropzone-hint');
    if (save)  { save.style.display  = editMode ? '' : 'none';
                 save.textContent = dzDirty ? '💾 Save zones *' : '💾 Save zones'; }
    if (clear) clear.style.display = editMode ? '' : 'none';
    if (hint)  hint.style.display  = editMode ? '' : 'none';
}

function wireDropZoneEditor(canvas) {
    const editToggle    = document.getElementById('dropzone-edit-toggle');
    const enabledToggle = document.getElementById('dropzone-enabled-toggle');
    const clearBtn      = document.getElementById('dropzone-clear-btn');
    const saveBtn       = document.getElementById('dropzone-save-btn');
    if (!editToggle) return;

    editToggle.addEventListener('change', () => {
        editMode = editToggle.checked;
        canvas.style.cursor = editMode ? 'crosshair' : 'default';
        updateDzButtons();
    });
    if (enabledToggle) {
        enabledToggle.checked = dropZones.enabled !== false;
        enabledToggle.addEventListener('change', () => {
            dropZones.enabled = enabledToggle.checked;
            dzDirty = true;
            updateDzButtons();
        });
    }
    clearBtn.addEventListener('click', () => {
        dropZones.zones = [];
        dzDirty = true;
        updateDzButtons();
    });
    saveBtn.addEventListener('click', async () => {
        try {
            dropZones.zones = dropZones.zones.map(normalizeZone);
            dropZones = await saveDropZones(dropZones);
            dzDirty = false;
            updateDzButtons();
            setStatus('Drop zones saved.', true);
        } catch (e) {
            setStatus(`Could not save drop zones: ${e.message}`, false);
        }
    });

    canvas.addEventListener('mousedown', e => onDzDown(canvas, e));
    canvas.addEventListener('mousemove', e => onDzMove(canvas, e));
    window.addEventListener('mouseup', onDzUp);
    canvas.addEventListener('dblclick', e => onDzDblClick(canvas, e));
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

    // Drop-zone editor: load the saved masks, then wire the canvas interactions.
    try {
        dropZones = await fetchDropZones();
    } catch { /* keep default empty zones if load fails */ }
    wireDropZoneEditor(document.getElementById('vision-canvas'));
    updateDzButtons();

    // Check model availability
    const available = await fetchDetectStatus();
    if (available) {
        setStatus('Model loaded. Choose a camera source and click Start Camera.', true);
    } else {
        setStatus('No trained model found. Place best.pt at models/lego_detector.pt or train one in the Train Model tab.', false);
        startBtn.disabled = true;
    }
}
