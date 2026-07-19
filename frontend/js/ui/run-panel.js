// Run/Stop controls for the Program workspace.
//
// Wires the toolbar buttons to the live block interpreter (program-runner),
// gates Run on the robot being connected and the webcam detection loop being
// active, renders the run log, and auto-stops when leaving the Program tab.

import { runProgram, stopProgram, isRunning, setRunnerCallbacks } from './program-runner.js';
import { isConnected } from './robot-link.js';
import { isCameraRunning } from './vision-panel.js';

const MAX_LOG_LINES = 100;

function appendLog(message, isError) {
    const log = document.getElementById('run-log');
    if (!log) return;
    const line = document.createElement('div');
    line.className = 'run-log-line' + (isError ? ' error' : '');
    line.textContent = message;
    log.appendChild(line);
    while (log.childElementCount > MAX_LOG_LINES) log.removeChild(log.firstChild);
    log.scrollTop = log.scrollHeight;
}

function reflectRunning(active) {
    const runBtn = document.getElementById('run-program-btn');
    const stopBtn = document.getElementById('stop-program-btn');
    if (runBtn) runBtn.style.display = active ? 'none' : '';
    if (stopBtn) stopBtn.style.display = active ? '' : 'none';
}

export function initRunPanel() {
    const runBtn = document.getElementById('run-program-btn');
    const stopBtn = document.getElementById('stop-program-btn');
    if (!runBtn) return;

    setRunnerCallbacks({ log: appendLog, stateChange: reflectRunning });

    runBtn.addEventListener('click', async () => {
        // Preconditions checked here so we can give a specific, actionable message
        // rather than a generic failure.
        if (!isConnected()) {
            appendLog('Robot not connected. Go to Teach Poses → Connect to Robot first.', true);
            return;
        }
        if (!isCameraRunning()) {
            appendLog('Camera is off. Go to the Vision tab → Start Camera so the program can see.', true);
            return;
        }
        if (!window.blocklyWorkspace) {
            appendLog('No program workspace found.', true);
            return;
        }
        if (!window.blocklyWorkspace.getTopBlocks(true).length) {
            appendLog('No blocks to run. Add some blocks first.', true);
            return;
        }
        try {
            await runProgram(window.blocklyWorkspace);
        } catch (e) {
            appendLog(`${e.message}`, true);
        }
    });

    stopBtn.addEventListener('click', stopProgram);

    // Stop a running program when leaving the Program tab.
    document.querySelectorAll('.workspace-tabs .tab').forEach((tab) => {
        tab.addEventListener('click', () => {
            if (tab.dataset.workspace !== 'program' && isRunning()) stopProgram();
        });
    });
}
