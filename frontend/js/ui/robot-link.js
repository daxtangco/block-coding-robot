// Single live link to the robot arm.
//
// The IDE talks to the same WebSocket the phone app uses (ws://192.168.4.1/ws),
// so dragging a pose slider and running a block program both drive the real arm
// through one socket. Pose-teaching and the program-runner share this module so
// there is exactly one connection and one set of listeners.

const ROBOT_WS_URL = 'ws://192.168.4.1/ws';
const RECONNECT_DELAY = 2000;

// ── Gripper: single source of truth ─────────────────────────────────────────
// The gripper is servo channel 4. Lower angle = jaws more closed (OPEN=30 is
// jaws apart). Every gripper control — the Teach Poses buttons and the block
// program runner — imports these so they can't drift apart. Keep them in sync
// with GRIPPER_OPEN/GRIPPER_CLOSE in arm_controller_ap_mode.ino, which is what
// the robot's own remote page and closeClaw()/openClaw() use.
export const GRIPPER_CH = 4;
export const GRIPPER_OPEN = 30;

// One fixed close angle can't fit every piece: the servo has no feedback, so if
// the jaws hit a thick piece before reaching the commanded angle, the servo
// STALLS — drawing max current on the shared supply, which starves the shoulder
// and jams the next lift. So close angle is chosen by piece WIDTH:
//   - narrow (1-stud): jaws travel nearly shut, so a small angle grips firmly.
//   - wide  (2-stud):  jaws contact sooner, so a larger angle = the servo still
//                      reaches its target and never stalls.
// Tune these two on the real arm; they're the only gripper numbers to touch.
export const GRIPPER_CLOSE_NARROW = 10;
export const GRIPPER_CLOSE_WIDE = 13;
// Default close (manual Teach Poses button, when no piece is known): use the
// wider angle so a manual close can never stall on whatever is in the jaws.
export const GRIPPER_CLOSE = GRIPPER_CLOSE_WIDE;

// LEGO classes that are 2 studs wide. Everything else is treated as narrow.
const WIDE_CLASSES = new Set([
    'brick_2x2', 'brick_2x4', 'plate_2x2', 'plate_2x4',
]);

// Pick the close angle for a detected class name. Unknown/absent → narrow-safe
// default is the wide angle (never stall); a known narrow class grips tighter.
export function gripperCloseForClass(className) {
    if (!className) return GRIPPER_CLOSE;
    return WIDE_CLASSES.has(className) ? GRIPPER_CLOSE_WIDE : GRIPPER_CLOSE_NARROW;
}

let ws = null;
let connected = false;
let reconnectTimer = null;

// Desired joint move order (servo channels; see setJointOrder). Re-sent to the
// board on every (re)connect so a reboot/reflash restores the user's choice.
// Default matches the firmware default: wrist, elbow, shoulder, base, gripper.
let desiredJointOrder = [3, 2, 1, 0, 4];

// Subscribers get every parsed message from the board: {type:'state',...},
// {type:'done'}, etc. Connection-state changes are delivered as a synthetic
// {type:'__conn', connected:bool, reason:string}.
const listeners = new Set();

function emit(msg) {
    for (const fn of listeners) {
        try { fn(msg); } catch (e) { console.error('robot-link listener error', e); }
    }
}

export function onRobotMessage(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);  // unsubscribe
}

export function isConnected() {
    return connected;
}

export function connectRobot() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
        return;
    }
    emit({ type: '__conn', connected: false, reason: 'connecting' });
    try {
        ws = new WebSocket(ROBOT_WS_URL);
    } catch (e) {
        emit({ type: '__conn', connected: false, reason: 'error', message: e.message });
        return;
    }

    ws.onopen = () => {
        connected = true;
        clearTimeout(reconnectTimer);
        // Put the board in manual mode so it accepts our servo commands (auto mode
        // runs the compiled student program instead).
        ws.send(JSON.stringify({ type: 'mode', auto: false }));
        // Restore the saved joint move order (the board resets to its firmware
        // default on reboot/reflash).
        ws.send(JSON.stringify({ type: 'jointorder', order: desiredJointOrder }));
        emit({ type: '__conn', connected: true, reason: 'open' });
    };

    ws.onmessage = (evt) => {
        let msg;
        try { msg = JSON.parse(evt.data); } catch { return; }
        emit(msg);
    };

    ws.onclose = () => {
        connected = false;
        // The board restarts its AP on every reboot/flash, dropping this socket.
        // Auto-reconnect so manual control and running programs recover on their own.
        emit({ type: '__conn', connected: false, reason: 'closed' });
        clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(connectRobot, RECONNECT_DELAY);
    };

    ws.onerror = () => {
        connected = false;
        emit({ type: '__conn', connected: false, reason: 'unreachable' });
    };
}

export function setMode(auto) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'mode', auto }));
    }
}

// Reset the arm to its firmware default positions. The board applies the
// defaults and broadcasts a fresh {type:'state'} so listeners re-adopt.
export function sendReset() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'reset' }));
    }
}

// Set the order joints ease into a pose (array of servo channels, a permutation
// of 0..4). Remembered so it's re-applied on reconnect, and pushed live now if
// connected. The firmware validates it's a full permutation before accepting.
export function setJointOrder(order) {
    desiredJointOrder = order.slice();
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'jointorder', order: desiredJointOrder }));
    }
}

export function sendServo(channel, angle) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'servo', channel, angle }));
    }
}

// Send all five joints of a pose ([base, shoulder, elbow, wrist, gripper]).
// The board accumulates the targets and slews them one joint at a time, then
// fires a single {type:'done'} once every joint has settled.
export function sendPose(angles) {
    angles.forEach((angle, channel) => sendServo(channel, angle));
}
