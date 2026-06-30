// Single live link to the robot arm.
//
// The IDE talks to the same WebSocket the phone app uses (ws://192.168.4.1/ws),
// so dragging a pose slider and running a block program both drive the real arm
// through one socket. Pose-teaching and the program-runner share this module so
// there is exactly one connection and one set of listeners.

const ROBOT_WS_URL = 'ws://192.168.4.1/ws';
const RECONNECT_DELAY = 2000;

let ws = null;
let connected = false;
let reconnectTimer = null;

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
