// Mobile Auto-Sort controller.
//
// A thin phone UI that REUSES the tested desktop modules rather than
// reimplementing them: the same detection loop (vision-panel), the same block
// interpreter (program-runner), the same arm link (robot-link) and pose data
// (pose-teaching). The hidden scaffold in mobile.html supplies the DOM element
// IDs those modules expect, so they run unchanged.
//
// Flow when AUTO is pressed:
//   load saved program -> headless Blockly workspace
//   start ESP32-CAM detection loop (populates vision-state)
//   runProgram(workspace) — walks blocks, reads live detections, drives the arm

import { initBlockly } from './blocks/index.js';
import { initPoseTeaching } from './ui/pose-teaching.js';
import { initVisionPanel, startCamera, stopCamera, isCameraRunning } from './ui/vision-panel.js';
import { connectRobot, isConnected, onRobotMessage } from './ui/robot-link.js';
import { runProgram, stopProgram, setRunnerCallbacks } from './ui/program-runner.js';
import { getLatestDetection } from './ui/vision-state.js';
import { fetchPrograms } from './api.js';

const el = (id) => document.getElementById(id);

let programs = {};

// ── logging ────────────────────────────────────────────────────────────────
function log(message, isError) {
    const box = el('m-log');
    const line = document.createElement('div');
    if (isError) line.className = 'error';
    line.textContent = message;
    box.appendChild(line);
    while (box.childElementCount > 60) box.removeChild(box.firstChild);
    box.scrollTop = box.scrollHeight;
}

// ── status pills ─────────────────────────────────────────────────────────────
function setRobotPill(connected) {
    const pill = el('m-robot-pill');
    pill.textContent = connected ? 'Robot: connected' : 'Robot: connecting…';
    pill.className = 'm-pill ' + (connected ? 'ok' : 'bad');
    refreshAutoEnabled();
}

function setCamPill(state) {
    const pill = el('m-cam-pill');
    pill.textContent = `Camera: ${state}`;
    pill.className = 'm-pill ' + (state === 'running' ? 'ok' : '');
}

function refreshAutoEnabled() {
    // Auto is available once the robot is connected and a program is selected.
    const ready = isConnected() && !!el('m-program-select').value;
    el('m-auto-btn').disabled = !ready;
}

// ── program picker ───────────────────────────────────────────────────────────
async function loadProgramList() {
    try {
        programs = await fetchPrograms();
    } catch (e) {
        log(`Could not load programs: ${e.message}`, true);
        programs = {};
    }
    const select = el('m-program-select');
    const names = Object.keys(programs);
    select.innerHTML = names.length
        ? names.map((n) => `<option value="${n}">${n}</option>`).join('')
        : '<option value="">No saved programs — build one in the IDE first</option>';
    refreshAutoEnabled();
}

// ── visible preview: mirror the hidden detection canvas + results ─────────────
function startPreviewMirror() {
    const src = el('vision-canvas');   // vision-panel draws boxes here (hidden)
    const dst = el('m-canvas');
    const dctx = dst.getContext('2d');

    function tick() {
        if (src.width && src.height) {
            if (dst.width !== src.width || dst.height !== src.height) {
                dst.width = src.width;
                dst.height = src.height;
            }
            dctx.drawImage(src, 0, 0);
        }
        renderDetections(getLatestDetection());
        requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

function renderDetections(result) {
    const box = el('m-detections');
    if (!result || !result.count) {
        box.innerHTML = '<p class="help-text">No objects detected.</p>';
        return;
    }
    const rows = result.detections
        .map((d) =>
            `<li><strong>${d.class_name}</strong> `
            + `(${(d.confidence * 100).toFixed(0)}%) &rarr; ${d.target_bin || 'no bin'}</li>`,
        )
        .join('');
    box.innerHTML = `<ul>${rows}</ul>`;
}

// ── auto / stop ────────────────────────────────────────────────────────────
function reflectRunning(active) {
    el('m-auto-btn').style.display = active ? 'none' : '';
    el('m-stop-btn').style.display = active ? '' : 'none';
}

async function onAuto() {
    const name = el('m-program-select').value;
    if (!name || !programs[name]) { log('Select a program first.', true); return; }
    if (!isConnected()) { log('Robot not connected yet.', true); return; }

    // Load the saved program into the headless Blockly workspace.
    try {
        window.blocklyWorkspace.clear();
        Blockly.serialization.workspaces.load(programs[name], window.blocklyWorkspace);
    } catch (e) {
        log(`Could not load program "${name}": ${e.message}`, true);
        return;
    }
    if (!window.blocklyWorkspace.getTopBlocks(true).length) {
        log('That program has no blocks.', true);
        return;
    }

    // Start the ESP32-CAM detection loop so camera_sees has live data.
    if (!isCameraRunning()) {
        log('Starting camera…');
        await startCamera();
        // startCamera reports failures via the (hidden) status element; detect
        // it by checking whether the loop actually came up.
        if (!isCameraRunning()) {
            log('Camera did not start — check it is powered and at 192.168.4.50.', true);
            return;
        }
        setCamPill('running');
    }

    log(`▶ Auto-sort started with "${name}".`);
    try {
        await runProgram(window.blocklyWorkspace);
    } catch (e) {
        log(`${e.message}`, true);
    }
}

function onStop() {
    stopProgram();
    stopCamera();
    setCamPill('idle');
    log('⏹ Stopped.');
}

// ── init ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await initBlockly();          // registers blocks + headless workspace
        await initPoseTeaching();     // loads poses so getPoses() is populated
        await initVisionPanel();      // wires the detection loop + model status

        setRunnerCallbacks({ log, stateChange: reflectRunning });

        onRobotMessage((msg) => {
            if (msg.type === '__conn') setRobotPill(msg.connected);
        });

        await loadProgramList();
        el('m-program-select').addEventListener('change', refreshAutoEnabled);
        el('m-auto-btn').addEventListener('click', onAuto);
        el('m-stop-btn').addEventListener('click', onStop);

        startPreviewMirror();

        // Auto-connect to the arm; robot-link retries on its own.
        setRobotPill(false);
        connectRobot();

        log('Ready. Pick a program and press AUTO.');
    } catch (e) {
        log(`Init error: ${e.message}`, true);
        console.error(e);
    }
});
