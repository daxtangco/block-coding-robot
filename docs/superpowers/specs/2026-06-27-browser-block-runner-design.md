# Browser Block Runner — Vision-Driven Arm Sorting

**Date:** 2026-06-27
**Status:** Design approved, pending spec review

## Problem

The webcam detection runs in the **browser** (webcam → `/api/detect` → YOLO),
but block programs currently compile to **C++ flashed on the ESP32**, which has
no camera (the ESP32-CAM was shelved). So `camera_sees()` on the chip is a dead
stub (`return false`). We need the camera's eyes and the arm's body — which live
on two different devices — to drive a sort together.

## Decision

**The browser runs the block program live.** It interprets the Blockly workspace
directly in JS, reads live webcam detections, and streams servo commands to the
arm over the existing WebSocket (`ws://192.168.4.1/ws`) — the same link the pose
sliders use. The arm stays a dumb executor in **manual mode**; no compile/flash
to run or iterate.

Rejected alternative: keep compiling to C++ and push detections to the chip. More
moving parts, requires reflashing to change the program, and still depends on the
laptop being connected — no real benefit over running in the browser.

## Architecture

### Components

1. **`robot-link.js`** (new) — extracted from `pose-teaching.js`. Owns the single
   WebSocket: `connect()`, `sendServo(channel, angle)`, `sendPose(angles[5])`,
   `isConnected()`, and an event subscription for incoming `state`/`done` messages.
   Both pose-teaching and the runner import this one module — one socket, no dupes.

2. **`vision-state.js`** (new) — a tiny shared store. `vision-panel.js` writes its
   latest detection result here each loop; `getLatestDetection()` returns the most
   recent `{detections, count, ...}` for the interpreter to read.

3. **`program-runner.js`** (new) — the interpreter. Walks the live Blockly blocks
   recursively and async-executes them:
   - `move_to_pose` → look up pose `[base,shoulder,elbow,wrist,gripper]` → send all
     5 channels → **await the `done` ACK**.
   - `open_claw` / `close_claw` → send gripper channel at OPEN/CLOSE → await `done`.
   - `camera_sees(class, conf)` → read `getLatestDetection()`, return true if any
     detection matches `class` with `confidence ≥ conf/100`.
   - `current_detection` / `current_confidence` → top detection's class / confidence.
   - `controls_if`, `controls_repeat_ext`, `forever_loop`, `wait_seconds`,
     `logic_compare`, `math_*`, `variables_*` → standard interpretation.
   - `forever_loop` checks a `running` flag each iteration so Stop breaks out.

4. **Program toolbar UI** (`index.html` + wiring) — a **▶ Run** / **⏹ Stop** button.
   Run is disabled unless: (a) robot connected, and (b) the Vision webcam loop is
   active (camera required, per decision). Stop halts the loop; also auto-stops on
   tab switch away from Program.

### Firmware ACK (one additive change to `arm_controller_ap_mode.ino`)

In **manual mode**, `loop()` already eases servos via `updateServos()` (returns
`true` when all at target). Add:

- `bool movePending = false;` (file scope)
- In `handleWebSocketMessage`, on a `servo` command: `movePending = true;`
- In the manual-mode branch of `loop()`, after `updateServos()`:
  ```cpp
  bool done = updateServos();
  if (movePending && done) {
    movePending = false;
    broadcastDone();   // ws.textAll({"type":"done"})
  }
  ```
- New `broadcastDone()` sends `{"type":"done"}`.

No-op moves (commanded angle == current) settle on the next tick, so `done` still
fires — the browser never hangs. The compiled `runStudentProgram()` path (uses
`slewBlocking`) is untouched.

### Data flow (one sort cycle)

```
webcam frame ─▶ /api/detect ─▶ vision-state  (continuous, Vision tab)
                                    │
program-runner reads camera_sees ◀──┘
   │  evaluates blocks
   ▼
robot-link.sendPose() ─▶ WS {servo×5} ─▶ ESP32 eases joints
                                              │ all at target
browser awaits {type:'done'} ◀── broadcastDone() ◀──┘
   │
   ▼ next block
```

## Error Handling

- **Robot not connected / socket drops mid-run:** runner aborts, surfaces a status
  message, re-enables Run. (robot-link already auto-reconnects for pose-teaching.)
- **`done` never arrives (e.g. board reboot):** per-move timeout (~7s, > firmware's
  6s slewBlocking ceiling) rejects the await and stops the run with an error.
- **No detection data:** `camera_sees` returns false (safe default); the program
  simply doesn't trigger that branch.
- **Stop pressed mid-move:** `running=false`, runner stops scheduling new blocks;
  the in-flight move finishes on the arm (can't un-send), then loop exits.

## Testing

- Unit-ish: interpret a tiny workspace (if camera_sees → move_to_pose) against a
  faked `vision-state` + a fake robot-link, assert the command sequence.
- Manual: flash the one firmware change, connect, start camera, build a
  detect→sort program, press Run, confirm the arm sequences moves and waits for
  each `done`.

## Out of Scope

- ESP32-CAM (shelved).
- On-chip inference.
- Changing the compiled-firmware path (still available via Build & Flash).
