// Live block-program interpreter.
//
// Instead of compiling the Blockly workspace to C++ and flashing it, we walk the
// live blocks here in the browser and drive the arm over the shared WebSocket.
// This lets a program read the webcam detections (which run in the browser) and
// act on them — the camera's eyes and the arm's body live on different devices,
// so the program logic sits in the middle, here.
//
// The arm stays in manual mode; each move is sent as servo commands and we await
// the firmware's {type:'done'} ACK before advancing, so moves never overlap.

import { sendServo, isConnected, onRobotMessage,
         GRIPPER_CH, GRIPPER_OPEN, gripperCloseForClass } from './robot-link.js';
import { getLatestDetection } from './vision-state.js';
import { getPoses } from './pose-teaching.js';

// Gripper angles come from robot-link.js. close_claw picks its angle from the
// piece currently under the camera (see gripperCloseForClass): a wide 2-stud
// brick needs a larger close angle than a narrow 1-stud one, otherwise the jaws
// bottom out early and the servo stalls — drawing max current on the shared
// supply and starving the shoulder on the next lift.

const MOVE_TIMEOUT_MS = 13000;  // > firmware's 11s slewBlocking ceiling

let running = false;
let onLog = () => {};
let onStateChange = () => {};

export function isRunning() {
    return running;
}

// Register UI callbacks: log(message, isError) and stateChange(running).
export function setRunnerCallbacks({ log, stateChange }) {
    if (log) onLog = log;
    if (stateChange) onStateChange = stateChange;
}

// ---- move synchronization -------------------------------------------------

// Resolver for the in-flight move's {type:'done'} ACK, if any.
let pendingDone = null;

onRobotMessage((msg) => {
    if (msg.type === 'done' && pendingDone) {
        pendingDone();
    }
});

// Send something to the arm, then wait for the board to report the move settled.
function awaitMove(sendFn) {
    return new Promise((resolve, reject) => {
        let settled = false;
        const finish = (err) => {
            if (settled) return;
            settled = true;
            pendingDone = null;
            clearTimeout(timer);
            err ? reject(err) : resolve();
        };
        const timer = setTimeout(
            () => finish(new Error('Timed out waiting for the arm to finish moving')),
            MOVE_TIMEOUT_MS,
        );
        pendingDone = () => finish(null);
        sendFn();
    });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Class name of the highest-priority current detection, or null if none. Used
// to size the gripper close angle to the piece being picked up.
function topDetectionClass() {
    const result = getLatestDetection();
    const top = result && result.detections && result.detections[0];
    return top ? top.class_name : null;
}

// ---- control ---------------------------------------------------------------

export function stopProgram() {
    running = false;
    pendingDone = null;
    onStateChange(false);
    onLog('⏹ Stopped.', false);
}

// Run the current Blockly workspace. Throws if preconditions aren't met.
export async function runProgram(workspace) {
    if (running) return;
    if (!isConnected()) {
        throw new Error('Robot not connected. Open Teach Poses → Connect to Robot first.');
    }
    running = true;
    onStateChange(true);
    onLog('▶ Running program…', false);

    try {
        for (const block of workspace.getTopBlocks(true)) {
            await execSequence(block);
            if (!running) break;
        }
        if (running) onLog('✅ Program finished.', false);
    } catch (e) {
        onLog(`❌ ${e.message}`, true);
    } finally {
        running = false;
        pendingDone = null;
        onStateChange(false);
    }
}

// ---- interpreter ------------------------------------------------------------

// Execute a block and then its next-connected sibling (a statement sequence).
async function execSequence(block) {
    let b = block;
    while (b && running) {
        await execBlock(b);
        b = b.getNextBlock();
    }
}

async function execBlock(block) {
    if (!running) return;
    switch (block.type) {
        case 'move_to_pose': {
            const poseName = block.getFieldValue('POSE');
            const poses = getPoses();
            const angles = poses[poseName];
            if (!angles) throw new Error(`Pose "${poseName}" not found`);
            onLog(`move to ${poseName}`, false);
            // Position the 4 arm joints only; the gripper (channel 4) is driven
            // solely by open_claw/close_claw at the tuned 5/30 angles. Poses bake
            // in old 0/90 gripper values that jam the geared jaws, so we never
            // replay channel 4 from a pose.
            await awaitMove(() => angles.slice(0, 4).forEach((a, ch) => sendServo(ch, a)));
            break;
        }
        case 'open_claw':
            onLog('open claw', false);
            await awaitMove(() => sendServo(GRIPPER_CH, GRIPPER_OPEN));
            break;
        case 'close_claw': {
            // Choose the close angle from the piece under the camera so a wide
            // brick doesn't stall the servo (see gripperCloseForClass).
            const seen = topDetectionClass();
            const angle = gripperCloseForClass(seen);
            onLog(`close claw${seen ? ` (${seen} → ${angle}°)` : ''}`, false);
            await awaitMove(() => sendServo(GRIPPER_CH, angle));
            break;
        }
        case 'wait_for_arm':
            await sleep(200);
            break;
        case 'wait_seconds':
            await sleep(parseFloat(block.getFieldValue('SECONDS')) * 1000);
            break;
        case 'forever_loop': {
            const body = block.getInputTargetBlock('DO');
            while (running) {
                await execSequence(body);
                await sleep(0);  // yield so Stop can interrupt
            }
            break;
        }
        case 'controls_repeat_ext': {
            const times = Math.floor(evalValue(block.getInputTargetBlock('TIMES')) || 0);
            const body = block.getInputTargetBlock('DO');
            for (let i = 0; i < times && running; i++) {
                await execSequence(body);
            }
            break;
        }
        case 'controls_if':
            await execIf(block);
            break;
        default:
            // Statement blocks we don't handle are skipped; value blocks are only
            // reached via evalValue, never here.
            break;
    }
}

async function execIf(block) {
    let n = 0;
    while (block.getInput('IF' + n)) {
        const cond = evalValue(block.getInputTargetBlock('IF' + n));
        if (cond) {
            await execSequence(block.getInputTargetBlock('DO' + n));
            return;
        }
        n++;
    }
    if (block.getInput('ELSE')) {
        await execSequence(block.getInputTargetBlock('ELSE'));
    }
}

// Evaluate a value/boolean block synchronously (no value block moves the arm).
function evalValue(block) {
    if (!block) return null;
    switch (block.type) {
        case 'camera_sees': {
            const className = block.getFieldValue('CLASS');
            const minConf = parseFloat(block.getFieldValue('CONFIDENCE'));  // percent
            const result = getLatestDetection();
            if (!result || !result.detections) return false;
            return result.detections.some(
                (d) => d.class_name === className && d.confidence * 100 >= minConf,
            );
        }
        case 'current_detection': {
            const result = getLatestDetection();
            const top = result && result.detections && result.detections[0];
            return top ? top.class_name : 'none';
        }
        case 'current_confidence': {
            const result = getLatestDetection();
            const top = result && result.detections && result.detections[0];
            return top ? Math.round(top.confidence * 100) : 0;
        }
        case 'logic_compare': {
            const a = evalValue(block.getInputTargetBlock('A'));
            const b = evalValue(block.getInputTargetBlock('B'));
            switch (block.getFieldValue('OP')) {
                case 'EQ': return a == b;
                case 'NEQ': return a != b;
                case 'LT': return a < b;
                case 'LTE': return a <= b;
                case 'GT': return a > b;
                case 'GTE': return a >= b;
            }
            return false;
        }
        case 'logic_operation': {
            const a = evalValue(block.getInputTargetBlock('A'));
            const b = evalValue(block.getInputTargetBlock('B'));
            return block.getFieldValue('OP') === 'AND' ? (a && b) : (a || b);
        }
        case 'logic_negate':
            return !evalValue(block.getInputTargetBlock('BOOL'));
        case 'logic_boolean':
            return block.getFieldValue('BOOL') === 'TRUE';
        case 'math_number':
            return parseFloat(block.getFieldValue('NUM'));
        case 'math_arithmetic': {
            const a = evalValue(block.getInputTargetBlock('A')) || 0;
            const b = evalValue(block.getInputTargetBlock('B')) || 0;
            switch (block.getFieldValue('OP')) {
                case 'ADD': return a + b;
                case 'MINUS': return a - b;
                case 'MULTIPLY': return a * b;
                case 'DIVIDE': return b !== 0 ? a / b : 0;
            }
            return 0;
        }
        case 'text':
            return block.getFieldValue('TEXT');
        default:
            return null;
    }
}
