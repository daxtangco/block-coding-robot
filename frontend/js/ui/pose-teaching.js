// Pose teaching interface
import { fetchPoses, savePose, deletePose, fetchSettings, saveSettings } from '../api.js';
import { connectRobot, sendServo, sendPose, setMode, sendReset, setJointOrder,
         isConnected, onRobotMessage,
         GRIPPER_CH, GRIPPER_OPEN,
         GRIPPER_CLOSE_NARROW, GRIPPER_CLOSE_WIDE } from './robot-link.js';

let currentPoses = {};

// Human labels for the four reorderable arm joints (by servo channel). The
// gripper (channel 4) is never reordered — it's driven by open/close — so it's
// pinned last in the order sent to the arm and omitted from this UI.
const JOINT_LABELS = { 0: 'Base', 1: 'Shoulder', 2: 'Elbow', 3: 'Wrist' };
// Current arm-joint move order (channels 0..3), top = moves first. Default
// wrist, elbow, shoulder, base — matches the firmware/settings default.
let jointOrder = [3, 2, 1, 0];
// Settings object kept so saving joint_order doesn't drop the other fields.
let currentSettings = {};

// Slider order maps to firmware servo channels: base=0 … wrist=3. The gripper
// (channel 4) is open/close buttons, not a slider — GRIPPER_* come from
// robot-link.js so this tab, the program runner, and the firmware all agree.
const SLIDER_SERVOS = ['base', 'shoulder', 'elbow', 'wrist'];
// Current gripper state the user has chosen via the buttons. Default to the
// wide close so a manual grip never stalls on an unknown piece.
let gripperAngle = GRIPPER_CLOSE_WIDE;

const SEND_INTERVAL = 50;          // throttle slider output (ms)
const lastSent = [0, 0, 0, 0, 0];

// True for a channel while the user is actively dragging its slider. Incoming
// arm state for that channel is ignored so a state broadcast can't yank the
// slider out from under the drag. Cleared on the slider's `change` (drag end).
const dragging = [false, false, false, false];

// Whether manual control is currently allowed (false while the arm is in auto
// mode running its on-board program). Tracked so a poses-list re-render can
// re-apply the disabled state to freshly-created Go buttons.
let manualEnabled = true;

function setConnStatus(text, state) {
    const el = document.getElementById('pose-conn-status');
    if (!el) return;
    el.textContent = text;
    el.className = `pose-conn-status ${state}`;
}

// Reflect the shared robot-link connection state in the pose-tab status pill.
// We intentionally do NOT push slider values on connect: the arm broadcasts its
// real position on connect (handled by handleState below), so the sliders adopt
// where the arm actually is instead of yanking it to the UI's defaults.
function handleConn(msg) {
    if (msg.type !== '__conn') return;
    if (msg.connected) {
        setConnStatus('🟢 Connected — sliders now move the real arm', 'connected');
    } else if (msg.reason === 'connecting') {
        setConnStatus('Connecting to robot…', 'connecting');
    } else if (msg.reason === 'unreachable' || msg.reason === 'error') {
        setConnStatus('Could not reach robot. Join the RobotArm-XXXX WiFi first.', 'disconnected');
    } else {
        setConnStatus('Disconnected — reconnecting…', 'disconnected');
    }
}

// Set a slider + its value display to an angle WITHOUT sending to the arm.
// This is the one-way arm→UI path used when adopting broadcast state.
function applySliderFromArm(i, angle) {
    const slider = document.getElementById(`pose-${SLIDER_SERVOS[i]}`);
    if (!slider) return;  // mobile scaffold may omit it
    slider.value = angle;
    if (slider.nextElementSibling) slider.nextElementSibling.textContent = `${angle}°`;
}

// Adopt the arm's broadcast state into the UI. Fired on connect, mode change,
// reset, and program finish (see arm_controller_ap_mode.ino broadcastState).
function handleState(msg) {
    if (msg.type !== 'state' || !Array.isArray(msg.servos)) return;
    for (let i = 0; i < 4; i++) {
        if (dragging[i]) continue;  // don't fight an active drag
        applySliderFromArm(i, msg.servos[i]);
    }
    if (msg.servos.length > GRIPPER_CH) reflectGripper(msg.servos[GRIPPER_CH]);
    // Reflect the arm's actual joint move order (drop the gripper channel).
    if (Array.isArray(msg.order)) {
        jointOrder = msg.order.filter((ch) => ch !== GRIPPER_CH);
        renderJointOrder();
    }
    // In auto mode the board runs its on-board program and ignores manual
    // servo commands, so disable manual controls and reflect the mode buttons.
    setManualMode(!msg.auto);
}

// Render the reorderable joint list with ▲/▼ buttons. Top = moves first.
function renderJointOrder() {
    const list = document.getElementById('joint-order-list');
    if (!list) return;  // mobile scaffold omits it
    list.innerHTML = '';
    jointOrder.forEach((ch, idx) => {
        const li = document.createElement('li');
        li.className = 'joint-order-item';
        li.innerHTML = `
            <span class="joint-order-name">${JOINT_LABELS[ch]}</span>
            <span class="joint-order-actions">
                <button class="btn-secondary joint-up" ${idx === 0 ? 'disabled' : ''}>▲</button>
                <button class="btn-secondary joint-down" ${idx === jointOrder.length - 1 ? 'disabled' : ''}>▼</button>
            </span>`;
        li.querySelector('.joint-up')?.addEventListener('click', () => moveJoint(idx, -1));
        li.querySelector('.joint-down')?.addEventListener('click', () => moveJoint(idx, +1));
        list.appendChild(li);
    });
}

// Swap the joint at idx with its neighbor (dir -1 up / +1 down), then push the
// new order to the arm (live preview) and persist it in project settings.
function moveJoint(idx, dir) {
    const j = idx + dir;
    if (j < 0 || j >= jointOrder.length) return;
    [jointOrder[idx], jointOrder[j]] = [jointOrder[j], jointOrder[idx]];
    renderJointOrder();
    applyJointOrder();
}

// Send the current order to the arm (with gripper pinned last) and save it.
// The live push always happens; the save only runs when we hold a complete
// settings object, so a failed initial fetch can't POST a partial body (which
// would 422 on the required wifi/blynk fields, or clobber saved values).
async function applyJointOrder() {
    const full = [...jointOrder, GRIPPER_CH];
    setJointOrder(full);  // live preview — never blocked by save state
    if (!settingsComplete(currentSettings)) {
        console.warn('Joint order applied live but not saved (settings unavailable).');
        return;
    }
    try {
        currentSettings = { ...currentSettings, joint_order: full };
        await saveSettings(currentSettings);
    } catch (e) {
        console.error('Failed to save joint order:', e);
    }
}

// True only if the object has every field SettingsModel requires, so saving it
// back won't fail validation or drop real wifi/blynk values.
function settingsComplete(s) {
    return s && ['wifi_ssid', 'wifi_password', 'blynk_template_id',
                 'blynk_template_name', 'blynk_auth_token'].every((k) => k in s);
}

// Highlight the Manual/Auto buttons and enable/disable manual controls.
function setManualMode(isManual) {
    document.getElementById('pose-mode-manual')?.classList.toggle('active', isManual);
    document.getElementById('pose-mode-auto')?.classList.toggle('active', !isManual);
    setControlsEnabled(isManual);
}

// Enable/disable every manual-control widget (sliders, gripper buttons, and the
// per-pose Go buttons). Null-guarded so the mobile scaffold never throws.
function setControlsEnabled(on) {
    manualEnabled = on;
    SLIDER_SERVOS.forEach((servo) => {
        const slider = document.getElementById(`pose-${servo}`);
        if (slider) slider.disabled = !on;
    });
    ['pose-grip-open', 'pose-grip-close-narrow', 'pose-grip-close-wide'].forEach((id) => {
        const btn = document.getElementById(id);
        if (btn) btn.disabled = !on;
    });
    document.querySelectorAll('.pose-card-go').forEach((btn) => { btn.disabled = !on; });
}

// Toggle the three gripper buttons' active state to match an angle, WITHOUT
// sending. The reported angle may be mid-slew, so snap to the nearest of the
// three presets (open 30 / narrow 10 / wide 15) rather than exact-matching.
function reflectGripper(angle) {
    const presets = [GRIPPER_OPEN, GRIPPER_CLOSE_NARROW, GRIPPER_CLOSE_WIDE];
    let nearest = presets[0];
    for (const p of presets) {
        if (Math.abs(angle - p) < Math.abs(angle - nearest)) nearest = p;
    }
    gripperAngle = nearest;
    document.getElementById('pose-grip-open')?.classList.toggle('active', nearest === GRIPPER_OPEN);
    document.getElementById('pose-grip-close-narrow')?.classList.toggle('active', nearest === GRIPPER_CLOSE_NARROW);
    document.getElementById('pose-grip-close-wide')?.classList.toggle('active', nearest === GRIPPER_CLOSE_WIDE);
}

function wsConnected() {
    return isConnected();
}

export async function initPoseTeaching() {
    // Connect button + reflect shared connection state in the status pill.
    document.getElementById('pose-connect-btn')?.addEventListener('click', connectRobot);
    onRobotMessage(handleConn);
    // Adopt the arm's broadcast position into the sliders/gripper (bidirectional).
    onRobotMessage(handleState);

    // Initialize servo control sliders (base..wrist; gripper is buttons)
    SLIDER_SERVOS.forEach((servo, i) => {
        const slider = document.getElementById(`pose-${servo}`);
        if (!slider) return;  // mobile scaffold may omit it
        const display = slider.nextElementSibling;

        slider.addEventListener('input', (e) => {
            dragging[i] = true;  // guard: ignore incoming state for this channel
            const angle = parseInt(e.target.value);
            if (display) display.textContent = `${angle}°`;
            // Throttle live commands so a drag doesn't flood the robot.
            const now = Date.now();
            if (wsConnected() && now - lastSent[i] >= SEND_INTERVAL) {
                lastSent[i] = now;
                sendServo(i, angle);
            }
        });
        // Always send the final value when the drag ends, then release the guard.
        slider.addEventListener('change', (e) => {
            if (wsConnected()) sendServo(i, parseInt(e.target.value));
            dragging[i] = false;
        });
        // `change` only fires if the value actually changed, so a press-without-
        // move (a click, or a nudge back to origin) would leave dragging[i] stuck
        // true and freeze this channel's sync. Clear it on release/blur too.
        const releaseGuard = () => { dragging[i] = false; };
        slider.addEventListener('pointerup', releaseGuard);
        slider.addEventListener('blur', releaseGuard);
    });

    // Gripper buttons: Open, Close (narrow) and Close (wide). The jaws have a
    // narrow usable arc, so it's preset angles only — arbitrary angles jam the
    // linkage. Two close presets let you hand-test both grip widths: narrow
    // grips thin 1-stud pieces firmly; wide stops short so the servo doesn't
    // stall against a thick 2-stud piece (which would starve the shoulder).
    // reflectGripper() (module scope) does the active-class toggle; here we add
    // the send so a button press also drives the arm.
    function setGripper(angle) {
        reflectGripper(angle);
        if (wsConnected()) sendServo(GRIPPER_CH, angle);
    }
    document.getElementById('pose-grip-open')?.addEventListener('click', () => setGripper(GRIPPER_OPEN));
    document.getElementById('pose-grip-close-narrow')?.addEventListener('click', () => setGripper(GRIPPER_CLOSE_NARROW));
    document.getElementById('pose-grip-close-wide')?.addEventListener('click', () => setGripper(GRIPPER_CLOSE_WIDE));

    // Manual / Auto / Reset. Null-guarded so the mobile scaffold (which omits
    // these buttons) doesn't throw. The board broadcasts fresh state on each,
    // so handleState re-adopts positions and flips the enabled/active UI.
    document.getElementById('pose-mode-manual')?.addEventListener('click', () => setMode(false));
    document.getElementById('pose-mode-auto')?.addEventListener('click', () => setMode(true));
    document.getElementById('pose-reset-btn')?.addEventListener('click', () => sendReset());

    // Save pose button
    document.getElementById('save-pose-btn')?.addEventListener('click', async () => {
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

    // Load the saved joint move order, seed the shared link (so it's re-sent on
    // connect), and render the reorder list.
    await loadJointOrder();

    // Load and render existing poses
    await loadPoses();
}

// Load joint_order from settings, apply it to the shared link and the UI.
async function loadJointOrder() {
    try {
        currentSettings = await fetchSettings();
    } catch (e) {
        console.error('Failed to load settings:', e);
        currentSettings = {};
    }
    const saved = currentSettings.joint_order;
    if (Array.isArray(saved) && saved.length === 5) {
        jointOrder = saved.filter((ch) => ch !== GRIPPER_CH);
        // Seed the shared link so the saved order is re-sent to the arm on connect.
        setJointOrder(saved);
    }
    renderJointOrder();
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
                <span class="pose-card-actions">
                    <button class="pose-card-go btn-secondary" data-pose="${name}">▶ Go</button>
                    ${name !== 'HOME' ? `<button class="pose-card-delete" data-pose="${name}">🗑️</button>` : ''}
                </span>
            </div>
            <div class="pose-card-angles">
                [${angles.join(', ')}]
            </div>
        `;

        // Go button: drive the arm to this saved pose (all 5 joints incl.
        // gripper) and adopt its values into the sliders immediately — the arm
        // doesn't broadcast during slew, so we update the UI optimistically.
        const goBtn = card.querySelector('.pose-card-go');
        if (goBtn) {
            // Re-apply the current mode's disabled state — this card was just
            // rebuilt, so it wouldn't otherwise reflect an active auto mode.
            goBtn.disabled = !manualEnabled;
            goBtn.addEventListener('click', () => {
                if (!wsConnected()) {
                    alert('Connect to the robot first.');
                    return;
                }
                if (!manualEnabled) return;  // arm is in auto mode; ignore
                const target = currentPoses[name];
                if (!Array.isArray(target)) return;
                sendPose(target);
                // Adopt into sliders, but don't yank a channel being dragged.
                for (let i = 0; i < 4; i++) if (!dragging[i]) applySliderFromArm(i, target[i]);
                if (target.length > GRIPPER_CH) reflectGripper(target[GRIPPER_CH]);
            });
        }

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
