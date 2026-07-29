# CODE MAP — Defense Cheat Sheet (RIAL-3-2425-C7)

The whole system in one line:
**Camera SEES → PC THINKS (YOLOv8) → Arm ACTS (taught poses).**
Three devices on the arm's own WiFi. The FastAPI backend on the laptop is the hub.

The 3 clean layers (memorize):
| Layer | Job | File |
|---|---|---|
| Vision / AI | says WHAT the piece is | `backend/services/detection.py` |
| Block program | decides WHAT TO DO | `frontend/js/ui/program-runner.js` |
| Firmware | EXECUTES the motion | `backend/templates/arm_controller_ap_mode.ino` |
> "Vision says what, the program decides what to do, the firmware does it."

---

## VISION / AI — "which device runs the model + where"
- **Runs on the PC/laptop, not the ESP32** (ESP32 lacks the compute). That's why detection is IDE-only.
- **The model runs here:** `backend/services/detection.py`
  - `detect()` — line 85. The AI actually runs at **line 103: `results = model(frame, conf=conf)`**.
  - Pipeline inside detect(): decode JPEG (cv2) → run model (L103) → loop boxes, pull **class + confidence + bounding box** → map class→bin (`_sorter.get_target_bin`) → return JSON.
- **Model caching (why it's real-time):** `_load_model()` line 52. `_model` (line 17) starts None; first frame loads YOLO from disk (~3.5s, line 65), every frame after reuses the cached model. "Lazy loading with caching."
- **Hot-swap after training:** `reload()` line 27 empties `_model` so the next detection loads new weights — no restart.
- **API endpoint (the door):** `backend/routes/detect.py` → `POST /api/detect`. (Different from services/detection.py = the engine.)
- **Model file:** `models/lego_detector.pt` (6 classes: brick_1x6/2x2/2x4, plate_1x2/2x2/2x4).
- Say: "YOLOv8 convolutional neural net — machine vision object detection. Outputs class, bounding box, confidence per piece."

## CAMERA — "the SEES"
- **Firmware:** `backend/templates/esp32cam_stream.ino` — serves `/capture` (JPEG) + `/stream`, static IP 192.168.4.50, VGA 640×480 (matches YOLO's 640 input).
- **CORS proxy (engineering fix #5):** `backend/routes/camera.py` — browser can't fetch cross-origin from the camera, so the backend fetches the frame for it and rotates it (`_rotate_jpeg` L17, `proxy_frame` L42). Rotate = handle a sideways-mounted camera.

## ARM MOTION — TAUGHT POSES (NOT inverse kinematics)
Two moments:
- **A. Teach & save** — `frontend/js/ui/pose-teaching.js`
  - Student drags sliders → live angle sent to arm (`sendServo`). Click Save → **line 260** reads slider values into `[base, shoulder, elbow, wrist, gripper]` → `savePose()` (L269) stores by name via `backend/routes/poses.py`.
- **B. Replay** — `frontend/js/ui/program-runner.js`, `case 'move_to_pose'` **line 132**: look up saved angle array → `sendServo(ch, a)` for the 4 joints.
- **Firmware executes** — `arm_controller_ap_mode.ino`: WebSocket msg (`handleWebSocketMessage` L447) → `targetPos[]` (L324) → `updateServos()` (L394) eases servos ONE joint at a time (prevents current surge/brownout).
- **NO trigonometry, NO coordinate solving anywhere.** Search the .ino for "kinematic" → nothing.

### THE IK ANSWER (adviser's core question) — say this cold:
"We do NOT compute joint angles from a target coordinate — that would be inverse kinematics. We use **taught poses**: the student physically positions the arm and we record the joint angles directly, then replay them. It's **lead-through teaching — the same method industrial robots use**."
Why not IK? 3 reasons:
1. **Users** are Grade 7–10 with no math background — IK needs trig beyond their curriculum; our study found programming was already their #1 barrier.
2. **Hardware** — open-loop hobby servos (MG996R/MG90S) have no position feedback, so a computed coordinate wouldn't be reliably reached anyway. Recording the angle that physically works is more accurate.
3. **Task** — we sort between a fixed feed position and fixed drop poses: a small set of known locations. Nothing to compute — you record it once.

## THE DECISION — "class → which pose"
- Lives in the **block program**, interpreted live in `frontend/js/ui/program-runner.js`.
- `camera_sees` block: `evalValue()` **L218 / case L221** — reads latest detection, checks class match (+ confidence, + stable vote).
- If true → runs the student's inner blocks → `move_to_pose DROP_x` → sends that pose's angles.
- **The student's block logic connects a detected class to a drop pose.** AI only reports the class; the program decides; firmware moves.
- Class→bin data helper: `sorting_logic.py` `get_target_bin()` L62 (SORTING_RULES L22).

## BLOCK CODING
- Block definitions: `frontend/js/blocks/` (arm.js, vision.js, logic.js), registered in index.js.
- Two run modes: generate C++ + flash (`frontend/js/generators/arduino_cpp.js`) OR run live in browser (`program-runner.js`, `runProgram()` L94) — no reflash.

## DETECTION STABILITY (why drops are consistent)
- `frontend/js/ui/vision-state.js` — every frame's top class is stored; `getStableClass()` returns the **majority vote over the last 7 frames**. Program routes on the voted class, not one flickery frame → consistent drops.

## BUILD / FLASH
- `backend/routes/build.py` → fills firmware template (`template_engine.py`, {{PLACEHOLDERS}}) → `builder.py` compiles via arduino-cli + flashes over USB.

## THE HUB
- `backend/main.py` — FastAPI server. Mounts routes under `/api` (L45–52), serves the browser IDE (L55), warms up the model on startup.

---

## Universal escape when stuck
"That's handled in `<file>` — I can open it and show you." Knowing the FILE is most of the battle.

## The "did you use AI?" answer
"We used AI as a coding assistant, like libraries and documentation — but we designed the system, made the engineering decisions, and understand every part. Ask me anything."

## Data flow (recite this = you've explained integration)
1. ESP32-CAM captures frame — esp32cam_stream.ino
2. Backend proxies it — routes/camera.py
3. Browser POSTs to /api/detect — routes/detect.py
4. YOLOv8 runs — services/detection.py L103   ← AI
5. Result stored — ui/vision-state.js
6. Block program reads class — ui/program-runner.js
7. Picks taught drop-pose for it
8. Angles sent over WebSocket — ui/robot-link.js
9. Firmware replays angles — arm_controller_ap_mode.ino   ← taught poses, NOT IK
