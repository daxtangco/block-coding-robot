// Train Model panel.
// Upload a YOLOv8-format dataset -> /api/train/* -> train a detector on the
// server. The trained model becomes the live detector, and its class names are
// published on window.__taughtClasses so the `camera sees` block lists them.

import {
    uploadDataset, startTraining, fetchTrainStatus, fetchModelClasses,
} from '../api.js';

const PROJECT = 'default';
const POLL_MS = 1500;

let pollTimer = null;

function setStatus(msg, ok) {
    const el = document.getElementById('teach-status');
    if (!el) return;
    el.textContent = msg;
    el.style.color = ok ? '#0a0' : '#c00';
}

// Publish class names so the camera-sees block dropdown reflects this model.
function publishClasses(classes) {
    window.__taughtClasses = Array.isArray(classes) ? classes.slice() : [];
}

async function refreshClasses() {
    try {
        publishClasses(await fetchModelClasses(PROJECT));
    } catch { /* dropdown keeps built-in classes */ }
}

async function onUpload() {
    const fileInput = document.getElementById('train-file');
    const file = fileInput.files[0];
    if (!file) { setStatus('Choose a .zip dataset file first.', false); return; }

    setStatus('Uploading and validating dataset...', true);
    try {
        const res = await uploadDataset(file, PROJECT);
        const detail = document.getElementById('train-dataset-detail');
        detail.innerHTML =
            `<p><strong>${res.num_classes}</strong> classes · `
            + `<strong>${res.num_images}</strong> images</p>`
            + `<p class="help-text">Classes: ${res.classes.join(', ')}</p>`;
        document.getElementById('train-dataset-info').style.display = '';
        document.getElementById('train-start-btn').disabled = false;
        setStatus('Dataset looks good. Set epochs and start training.', true);
    } catch (e) {
        document.getElementById('train-start-btn').disabled = true;
        setStatus(`Upload failed: ${e.message}`, false);
    }
}

function renderProgress(s) {
    const wrap = document.getElementById('train-progress-wrap');
    const bar = document.getElementById('train-progress');
    const text = document.getElementById('train-progress-text');
    wrap.style.display = '';
    const total = s.total_epochs || 1;
    bar.max = total;
    bar.value = s.epoch || 0;
    text.textContent = s.message || '';
}

async function poll() {
    try {
        const s = await fetchTrainStatus();
        renderProgress(s);

        if (s.state === 'done') {
            clearInterval(pollTimer); pollTimer = null;
            publishClasses(s.classes);
            document.getElementById('train-start-btn').disabled = false;
            setStatus(s.message || 'Training complete — your model is now live.', true);
        } else if (s.state === 'error') {
            clearInterval(pollTimer); pollTimer = null;
            document.getElementById('train-start-btn').disabled = false;
            setStatus(s.message || 'Training failed.', false);
        }
    } catch (e) {
        setStatus(`Lost contact with server: ${e.message}`, false);
    }
}

async function onStart() {
    const epochs = parseInt(document.getElementById('train-epochs').value, 10) || 20;
    document.getElementById('train-start-btn').disabled = true;
    setStatus('Starting training...', true);
    try {
        await startTraining(PROJECT, epochs);
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(poll, POLL_MS);
        poll();
    } catch (e) {
        document.getElementById('train-start-btn').disabled = false;
        setStatus(`Could not start: ${e.message}`, false);
    }
}

export async function initTeachPanel() {
    const uploadBtn = document.getElementById('train-upload-btn');
    if (!uploadBtn) return;  // panel not present

    uploadBtn.addEventListener('click', onUpload);
    document.getElementById('train-start-btn').addEventListener('click', onStart);

    // If a training job is already running (e.g. user switched tabs), resume polling.
    try {
        const s = await fetchTrainStatus();
        if (s.state === 'training') {
            renderProgress(s);
            pollTimer = setInterval(poll, POLL_MS);
        }
    } catch { /* server may not be up yet */ }

    await refreshClasses();
    setStatus('Upload a YOLOv8 dataset (.zip) to begin.', true);
}
