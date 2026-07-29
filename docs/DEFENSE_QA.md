# DEFENSE Q&A — Complete Study Sheet (RIAL-3-2425-C7)

## SYSTEM OVERVIEW
**Walk me through the system end to end.**
Camera SEES → PC THINKS → Arm ACTS. ESP32-CAM captures a frame → laptop backend runs YOLOv8 to classify → browser block-program reads the class → triggers the taught pose for that class → arm replays those joint angles. Three devices on the arm's WiFi; FastAPI backend is the hub. Two modes: manual (Teach Poses), auto (Program tab — run live in IDE or flash to ESP32).

---
## VISION / AI
**Which device runs the network, why not the ESP32?**
The PC. ESP32 lacks compute/memory for a neural net. Camera = eye, laptop = brain. That's why detection is IDE-only.

**What model, what output per frame?**
YOLOv8. Per piece: **class + bounding box + confidence**.

**Where does the model run in code?**
`backend/services/detection.py` → `detect()` → line 103 `results = model(frame, conf=conf)`. (`routes/detect.py` = API endpoint/door; `services/detection.py` = engine.)

**Does it reload the model every frame?**
No — lazy loading with caching. `_load_model()` loads once (~3.5s first frame), caches in `_model`, reuses after. `reload()` clears cache so a newly-trained model goes live without restart.

**Why is this AI, not a hard-coded filter?**
It's a neural network that LEARNED from labeled data, not rules we wrote. It generalizes to unseen images. A filter can't.

**You didn't invent YOLOv8 — your contribution?**
The integration: trained it for our task, connected it into a real-time robotic pipeline, made it retrainable. "The novelty is the integration, not the parts."

**Define integration.**
Making independent parts (vision, arm, blocks) work as one pipeline: frame → class → decision → motion. We built every connection and made it reliable on cheap hardware, offline, for beginners.

**Terminology:** paper says "computer vision / YOLOv8 object detection," not "AI." Say computer vision; bridge to AI only if adviser uses that word.

---
## CAMERA
**Why can't the browser fetch the camera image directly?**
CORS — Cross-Origin Resource Sharing, a browser security rule: browser won't let its JS read a response from another origin (camera IP). We route through a backend CORS proxy (`backend/routes/camera.py`); Python isn't a browser, so it fetches freely. Also does server-side rotation.

**Why does the proxy bypass CORS?**
CORS is enforced by the browser on its own scripts — nothing else obeys it. Move the cross-origin request into the backend (no CORS there); browser only talks to its own same-origin backend, always allowed.

**Camera specs / frame rate?**
ESP32-CAM, OV2640 sensor, **2D (no depth)**, VGA 640×480 (matches YOLO 640), JPEG. Stream ~20 fps; detection loop ~16 fps target (60ms poll), really limited by YOLO inference speed.

**Is it 2D?** Yes — OV2640, flat RGB, no depth. Root of the brick-vs-plate limit.

---
## ARM MOTION — TAUGHT POSES (CORE)
**How does the arm know its angles? Do you use inverse kinematics?**
No IK. Taught poses: student drags sliders to position the arm, saves joint angles directly (`pose-teaching.js` L260 → `poses.py`); program replays them (`program-runner.js` move_to_pose); firmware drives servos to saved angles (`arm_controller_ap_mode.ino` targetPos[]). Lead-through teaching — same as industrial robots.

**Why not IK?**
(1) Grade 7–10 users, no trig; programming was their #1 barrier. (2) Open-loop servos, no feedback — a computed coordinate wouldn't be reliably reached; recorded angles are more accurate. (3) Fixed positions to sort — nothing to compute.

**Where is "class → drop pose" decided?**
In the block program, interpreted live in `program-runner.js`. `camera_sees` checks detection; if match, runs the student's inner move-to-pose blocks. AI says what, program decides, firmware executes — 3 clean layers.

---
## HARDWARE
**Why one joint at a time?**
All servos at once = current surge → rail sags → ESP32 brownout/reset. One-at-a-time flattens draw. `updateServos()`, order via `jointOrder[]`.

**But you isolated the servo supply — why still brown out?**
Isolation fixed steady-state load; a startup surge from all five still causes a transient sag/ground-bounce through the shared ground. Two complementary fixes.

**Brownout vs stall?**
Brownout = voltage sag (from surge) resets ESP32. Stall = servo jammed past its limit draws MAX (locked-rotor) current, starves others. Transient surge vs sustained overload.

**Gripper force without a sensor?**
Open-loop, can't feel. Two pre-tuned angles: narrow ~8° (1-stud), wide ~13° (2-stud). Camera already classified the piece → program picks the angle. Classification substitutes for a force sensor. Limit: only tuned pieces; future work = force/current sensing.

---
## OFFLINE
**How does it work with no internet?**
ESP32 = access point; laptop + camera join the arm's WiFi (arm 192.168.4.1, cam 192.168.4.50). All traffic local. Only internet need = one-time setup (deps, arduino-cli, base weights). After that fully offline; trained model is a local file.

---
## HONEST LIMITATIONS
**How do you know it works on your pieces?**
120 trials (20×6) → 92.5% sorting on our setup. 95.6% mAP = validation; 92.5% = real-world. Failures were vision (misclassification), not motion.

**Why misclassify / false positives?**
Depth limit: brick-vs-plate = height, 1x6-vs-2x4 = footprint; one 2D camera can't capture both — infers height from fragile 2D cues (side wall, shadow, proportions). No negatives: trained only on brick images, so empty scene forces a detection. Both documented future work; depth camera / retraining with negatives would fix — cost trade-off (₱3,116).

**"Did you use AI to build this?"**
"We used AI as a coding assistant, like libraries and documentation — but we designed the system, made the engineering decisions, and understand every part. Ask me anything."

---
## KEY FILES (point to these)
- Vision engine: `backend/services/detection.py` (L103 = model runs)
- Vision endpoint: `backend/routes/detect.py`
- CORS proxy: `backend/routes/camera.py`
- Camera firmware: `backend/templates/esp32cam_stream.ino`
- Arm firmware: `backend/templates/arm_controller_ap_mode.ino` (targetPos[], updateServos, NO kinematics)
- Teach poses: `frontend/js/ui/pose-teaching.js` (L260 save angles)
- Block interpreter / decision: `frontend/js/ui/program-runner.js`
- Stability vote: `frontend/js/ui/vision-state.js` (getStableClass)
- Class→bin: `sorting_logic.py`
- Backend hub: `backend/main.py`

## DEMO SETUP
~45–60° camera angle (keeps height cue + stud pattern) · bright diffused light · matte contrasting background · fill the frame · confidence 0.70 · test each piece first, feature the reliable ones.
