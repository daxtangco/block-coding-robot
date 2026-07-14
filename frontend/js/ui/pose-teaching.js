// Pose teaching interface
import { fetchPoses, savePose, deletePose } from '../api.js';
import { connectRobot, sendServo, isConnected, onRobotMessage,
         GRIPPER_CH, GRIPPER_OPEN,
         GRIPPER_CLOSE_NARROW, GRIPPER_CLOSE_WIDE } from './robot-link.js';

let currentPoses = {};

// Slider order maps to firmware servo channels: base=0 … wrist=3. The gripper
// (channel 4) is open/close buttons, not a slider — GRIPPER_* come from
// robot-link.js so this tab, the program runner, and the firmware all agree.
const SLIDER_SERVOS = ['base', 'shoulder', 'elbow', 'wrist'];
// Current gripper state the user has chosen via the buttons. Default to the
// wide close so a manual grip never stalls on an unknown piece.
let gripperAngle = GRIPPER_CLOSE_WIDE;

const SEND_INTERVAL = 50;          // throttle slider output (ms)
const lastSent = [0, 0, 0, 0, 0];

function setConnStatus(text, state) {
    const el = document.getElementById('pose-conn-status');
    if (!el) return;
    el.textContent = text;
    el.className = `pose-conn-status ${state}`;
}

// Reflect the shared robot-link connection state in the pose-tab status pill, and
// push the current slider values once connected so the arm matches the UI.
function handleConn(msg) {
    if (msg.type !== '__conn') return;
    if (msg.connected) {
        setConnStatus('🟢 Connected — sliders now move the real arm', 'connected');
        SLIDER_SERVOS.forEach((servo, i) => {
            sendServo(i, parseInt(document.getElementById(`pose-${servo}`).value));
        });
        sendServo(GRIPPER_CH, gripperAngle);
    } else if (msg.reason === 'connecting') {
        setConnStatus('Connecting to robot…', 'connecting');
    } else if (msg.reason === 'unreachable' || msg.reason === 'error') {
        setConnStatus('Could not reach robot. Join the RobotArm-XXXX WiFi first.', 'disconnected');
    } else {
        setConnStatus('Disconnected — reconnecting…', 'disconnected');
    }
}

function wsConnected() {
    return isConnected();
}

export async function initPoseTeaching() {
    // Connect button + reflect shared connection state in the status pill.
    document.getElementById('pose-connect-btn')?.addEventListener('click', connectRobot);
    onRobotMessage(handleConn);

    // Initialize servo control sliders (base..wrist; gripper is buttons)
    SLIDER_SERVOS.forEach((servo, i) => {
        const slider = document.getElementById(`pose-${servo}`);
        const display = slider.nextElementSibling;

        slider.addEventListener('input', (e) => {
            const angle = parseInt(e.target.value);
            display.textContent = `${angle}°`;
            // Throttle live commands so a drag doesn't flood the robot.
            const now = Date.now();
            if (wsConnected() && now - lastSent[i] >= SEND_INTERVAL) {
                lastSent[i] = now;
                sendServo(i, angle);
            }
        });
        // Always send the final value when the drag ends.
        slider.addEventListener('change', (e) => {
            if (wsConnected()) sendServo(i, parseInt(e.target.value));
        });
    });

    // Gripper buttons: Open, Close (narrow) and Close (wide). The jaws have a
    // narrow usable arc, so it's preset angles only — arbitrary angles jam the
    // linkage. Two close presets let you hand-test both grip widths: narrow
    // grips thin 1-stud pieces firmly; wide stops short so the servo doesn't
    // stall against a thick 2-stud piece (which would starve the shoulder).
    const gripOpenBtn = document.getElementById('pose-grip-open');
    const gripCloseNarrowBtn = document.getElementById('pose-grip-close-narrow');
    const gripCloseWideBtn = document.getElementById('pose-grip-close-wide');
    function setGripper(angle) {
        gripperAngle = angle;
        gripOpenBtn.classList.toggle('active', angle === GRIPPER_OPEN);
        gripCloseNarrowBtn.classList.toggle('active', angle === GRIPPER_CLOSE_NARROW);
        gripCloseWideBtn.classList.toggle('active', angle === GRIPPER_CLOSE_WIDE);
        if (wsConnected()) sendServo(GRIPPER_CH, angle);
    }
    gripOpenBtn.addEventListener('click', () => setGripper(GRIPPER_OPEN));
    gripCloseNarrowBtn.addEventListener('click', () => setGripper(GRIPPER_CLOSE_NARROW));
    gripCloseWideBtn.addEventListener('click', () => setGripper(GRIPPER_CLOSE_WIDE));

    // Save pose button
    document.getElementById('save-pose-btn').addEventListener('click', async () => {
        const name = prompt('Enter a name for this pose:');
        if (!name) return;

        // Validate name
        if (!/^[A-Z_][A-Z0-9_]*$/i.test(name)) {
            alert('Pose name must start with a letter and contain only letters, numbers, and underscores.');
            return;
        }

        const angles = [
            parseInt(document.getElementById('pose-base').value),
            parseInt(document.getElementById('pose-shoulder').value),
            parseInt(document.getElementById('pose-elbow').value),
            parseInt(document.getElementById('pose-wrist').value),
            gripperAngle
        ];

        try {
            currentPoses = await savePose(name, angles);
            await renderPosesList();
            updatePoseCount();
            syncPoseGlobals();
            alert(`✅ Pose "${name}" saved successfully!`);
        } catch (error) {
            alert('❌ Error saving pose: ' + error.message);
        }
    });

    // Load and render existing poses
    await loadPoses();
}

async function loadPoses() {
    try {
        currentPoses = await fetchPoses();
        await renderPosesList();
        updatePoseCount();
        syncPoseGlobals();
    } catch (error) {
        console.error('Failed to load poses:', error);
    }
}

// Keep window.getPoseOptions current so the arm.js dropdown generator
// and Blockly's updatePoseDropdowns always see the latest saved poses.
function syncPoseGlobals() {
    window.getPoseOptions = () => Object.keys(currentPoses).map(n => [n, n]);
    window.updatePoseDropdowns?.();
}

async function renderPosesList() {
    const list = document.getElementById('poses-list');
    list.innerHTML = '';

    if (Object.keys(currentPoses).length === 0) {
        list.innerHTML = '<p style="color: #64748b;">No poses saved yet. Create one using the sliders above!</p>';
        return;
    }

    for (const [name, angles] of Object.entries(currentPoses)) {
        const card = document.createElement('div');
        card.className = 'pose-card';
        card.innerHTML = `
            <div class="pose-card-header">
                <span class="pose-card-name">${name}</span>
                ${name !== 'HOME' ? `<button class="pose-card-delete" data-pose="${name}">🗑️</button>` : ''}
            </div>
            <div class="pose-card-angles">
                [${angles.join(', ')}]
            </div>
        `;

        // Delete button handler
        const deleteBtn = card.querySelector('.pose-card-delete');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', async () => {
                if (!confirm(`Delete pose "${name}"?`)) return;

                try {
                    currentPoses = await deletePose(name);
                    await renderPosesList();
                    updatePoseCount();
                    syncPoseGlobals();
                } catch (error) {
                    alert('❌ Error deleting pose: ' + error.message);
                }
            });
        }

        list.appendChild(card);
    }
}

function updatePoseCount() {
    const count = Object.keys(currentPoses).length;
    document.getElementById('pose-count').textContent = `${count} pose${count !== 1 ? 's' : ''}`;
}

// Export current poses for use by Blockly
export function getPoses() {
    return currentPoses;
}
