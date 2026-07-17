# Defense Presentation Script — Block Robot (RIAL-3-2425-C7)

**Target: ~20 minutes.** Word-for-word spoken script, one section per slide. Read naturally —
these are talking lines, not paragraphs to recite verbatim. `[timing]` is cumulative target.
Optional speaker handoffs are marked **[Speaker: …]** — reassign to Adriano / Cabral / Lin / Tangco
as you like, or run it solo.

> Tip: keep the deck's built-in speaker notes (press **S**) open on your presenter screen — this
> doc is the fuller rehearsal script; the notes are the on-stage reminders.

---

## Slide 1 — Title  ·  [0:00–0:45]
**[Speaker 1]**

"Good [morning/afternoon], panel. We're group RIAL-3-2425-C7, and our project is **Block Robot** —
the *Development of a Cost-Effective 3D-Printed Pick-and-Place Robotic Arm for Object Sorting and
Educational Applications*.

I'm [name], with me are [names]. In the next twenty minutes we'll show how we built a five-degree-
of-freedom robotic arm that a secondary-school student can program by **snapping blocks together**,
teach to **see objects with a camera**, and run **completely offline** — for under three-and-a-half
thousand pesos."

---

## Slide 2 — In one sentence  ·  [0:45–1:45]
**[Speaker 1]**

"If you remember one thing from this defense, let it be this line: **the camera sees, the PC thinks,
and the arm acts.**

The camera — an ESP32-CAM or just a laptop webcam — captures a frame. The laptop runs the neural
network that detects and classifies the piece. And the ESP32-based arm carries out the motion over
WebSocket to sort it.

Why split it three ways? Because each job lives on the device best suited to it. The ESP32 is far
too weak to run a neural network; the laptop can't ride on a moving arm. So vision runs on the PC,
motion on the microcontroller, and they talk over the arm's own WiFi. That deliberate split is the
backbone of the whole system."

---

## Slide 3 — The problem  ·  [1:45–3:00]
**[Speaker 2]**

"So why build this at all? Four problems.

First, **cost and access** — commercial educational arms run from around eight-and-a-half to over
seventeen thousand pesos. That's out of reach for most Philippine schools.

Second, the **programming barrier** — most platforms need real text coding, so a beginner can't
even start.

Third, **rigid perception** — they recognize a fixed set of objects; students can't teach them
*their own* objects.

And fourth, **infrastructure** — many depend on home WiFi or cloud accounts, which is awkward in a
classroom.

Our answer ties all four together: a 3D-printed 5-DOF arm, a block-coding IDE, YOLOv8 vision, and a
Grade 7-to-10 curriculum — all running fully offline on the robot's own WiFi, built for a target of
three-and-a-half thousand pesos or less."

---

## Slide 4 — Objectives  ·  [3:00–4:15]
**[Speaker 2]**

"That gives us our general objective: a low-cost, modular, 3D-printed 5-DOF pick-and-place arm for
object sorting in secondary education — with manual control, automated detection, and a grade-level
curriculum.

We broke that into five specific objectives, each with a measurable target:
- **SO1** — build it for **PHP 3,500 or less**.
- **SO2** — manual control plus detection, with a mean average precision of **at least 70**.
- **SO3** — an optimized sorting routine with **at least 90% pick-and-place success**.
- **SO4** — a structured **Grade 7–10 lesson manual**.
- **SO5** — assess **educational impact** with real students.

The next slide is the spine of this defense: we met all five."

---

## Slide 5 — Results dashboard  ·  [4:15–5:30]
**[Speaker 2]**

"Here are the headline numbers, and every single target was met or exceeded.

- **SO1, cost:** PHP **3,116** — about 89% of the ceiling, so we came in *under* budget.
- **SO2, detection:** **95.6%** mAP at 0.5 — against a target of 70. We beat it by ~25 points.
- **SO3, sorting:** **92.5%** pick-and-place success — above the 90% target.
- **SO4:** a complete **four-module** Grade 7–10 manual.
- **SO5:** a **System Usability Scale score of 71.3** — rated 'Good', above the ~68 industry
  benchmark.

Every number on this slide is defended by the slides that follow. If we're short on time, the cost,
detection, and sorting results are the core."

---

## Slide 6 — From the literature to our results  ·  [5:30–7:15]
**[Speaker 3]**

"Before the technical details, let me place our work against the literature — because our results
aren't just numbers, they answer gaps that prior studies left open. We reviewed 25 works through a
PRISMA process; here's how four themes map to what we achieved.

**Educational robotics** — Benyeogor, Vandevelde, and Zeng's *iArm* all showed robotics engages
students, but left a gap in *accessible, grade-leveled* systems. We answered that with a Grade 7–10
curriculum and a block IDE, and our usability score was 71.3.

**Vision-based pick-and-place** — this is the strongest comparison. A prior DLSU project, **Aldea et
al. in 2022**, built a joystick-controlled 4-DOF arm with a YOLOv5 model and reached an **88%**
grasp-and-dispose rate. Our block-coded 5-DOF arm with YOLOv8n reached **92.5% real sorting and
95.6% detection** — a direct improvement over that predecessor.

**Low-cost and 3D-printed arms** — Mick's Reachy, Ali, and Adediran showed 3D printing cuts cost,
but few pair low cost *with* vision. Ours is **PHP 3,116 and the only vision-capable arm** in our
comparison table.

And the recurring infrastructure gap — cloud and WiFi dependence — we removed entirely with offline
AP mode. So every documented gap maps to an objective we met."

---

## Slide 7 — References  ·  [7:15–7:30]
**[Speaker 3]**

"These are the works I just cited, with full references; the complete 25-study list is in Chapter 2
of the manuscript. I'll move on — but we can return here if you'd like the source on any specific
claim."

*(Move through quickly — this slide is for the panel's reference, not narration.)*

---

## Slide 8 — System architecture  ·  [7:30–8:45]
**[Speaker 3]**

"Architecturally, the system is three tiers.

**Tier 1** is the laptop — the browser runs the Blockly IDE, and a FastAPI server on localhost runs
YOLOv8 inference, model training, and firmware building and flashing.

**Tier 2** is the ESP32 arm controller. Critically, **the arm itself is the WiFi access point** — it
broadcasts a network called RobotArm-XXXX. It serves its own control page and drives five servos
through a PCA9685 driver over WebSocket.

**Tier 3** is the optional ESP32-CAM, which streams JPEG frames and **auto-joins the arm's network**.

The key design point: the laptop *and* the camera both join the *arm's* network. The arm sits at
192.168.4.1, the camera auto-takes .50. No home WiFi, no cloud — and that's exactly what makes it
classroom-deployable."

---

## Slide 9 — The hardware  ·  [8:45–10:00]
**[Speaker 4]**

"The hardware. Five degrees of freedom — base, shoulder, elbow, wrist, and gripper — built from an
open-source Thingiverse design, twelve printed parts in Esun **PLA+** at 20% infill.

For servos: the three heavy joints — base, shoulder, elbow — use **MG996R** metal-gear servos; the
wrist and gripper use **MG90S** micro servos. All five are driven through a **PCA9685** 16-channel
PWM driver over I²C.

Two deliberate design choices matter here. First, offloading PWM to the PCA9685 frees up the ESP32.
Second — and this one we learned the hard way — the servos run on a **dedicated, isolated 5-volt,
3-amp supply**, separate from the ESP32. Early on, servo current surges were resetting the board;
isolating the power rail fixed it. And per-joint travel caps keep every servo inside its safe
mechanical range."

---

## Slide 10 — Bill of materials  ·  [10:00–11:15]
**[Speaker 4]**

"So did we hit the cost target? Yes — the full bill of materials comes to **PHP 3,116**, which is
about 89% of the 3,500 ceiling, so we're comfortably under budget. The biggest line items are the
filament, the three MG996R servos, the ESP32-CAM, and the PCA9685 — all cheap, all widely available.

The comparison on the right is our strongest cost argument. Against the LEWANSOUL xArm 1S at around
8,500 and the Dobot Magician Lite at around 17,000, we're **63 to 82% cheaper** — and we're the
**only one of the three with built-in vision.** Those are their real product photos next to ours.
Cheaper *and* more capable on the dimension that matters for a sorting task."

---

## Slide 11 — The 5-tab IDE  ·  [11:15–12:15]
**[Speaker 1]**

"Everything the student touches lives in one browser page with five tabs.

**Setup** — name the robot's WiFi, then build and flash the firmware. **Teach Poses** — move the
real arm with sliders and save named positions. **Program** — snap blocks together and watch the
generated code appear live. **Vision** — point a camera and see detections and which bin each object
goes to. And **Train Model** — teach the computer to recognize your own objects.

The whole frontend is Blockly plus vanilla JavaScript — no framework, no build step. It just loads
in a browser."

---

## Slide 12 — Block-coding & manual control  ·  [12:15–13:45]
**[Speaker 1]**

"Let's look closer at programming and control — this is SO2.

Blocks snap together like LEGO and are type-checked by their shape, so you physically can't build a
nonsensical program. There are motion blocks, vision blocks, and logic blocks.

On manual control: the ESP32 hosts an embedded page at 192.168.4.1 with joint sliders, a
Manual/Auto toggle, and Reset, all over a persistent WebSocket — no per-request HTTP, no cloud hop,
so latency is bounded only by the local link.

Two things I want to highlight as genuine contributions. First, the **gripper uses three tuned
presets** — open, close-narrow, and close-wide — and when running live, the system **automatically
sizes the grip to the detected piece**: a one-stud piece grips narrow, a two-stud piece grips wide,
so the servo never stalls.

Second, we support **two run modes**: you can compile the blocks to C++ and flash them, *or* run
them live in the browser, where a JavaScript interpreter walks the blocks and streams servo commands
over the same WebSocket. Normally changing a block means recompile-and-reflash, which is slow — our
live runner makes iteration instant. The example on the right is a complete sorting loop in seven
blocks."

---

## Slide 13 — Object detection  ·  [13:45–15:00]
**[Speaker 3]**

"Now the detection results — the first half of SO2.

We used the *spiled-lego-bricks* dataset from Kaggle — about 3,000 images, 9,600 annotations, split
70/15/15. The model is **YOLOv8n**, trained in two stages — a frozen-backbone stage then fine-tuning
— on a Tesla T4 in Colab.

The result: **95.6% mAP at 0.5** overall, and 91.1% on the stricter 0.5-to-0.95 metric. Precision
0.897, recall 0.909, F1 0.903 — every class lands in the high-80s to mid-90s AP. That beats the
target of 70 by about 25 points.

One honest note: that 95.6% is on the clean, held-out validation set. Real-world sorting under
classroom lighting is harder — which is exactly what the next slide addresses."

---

## Slide 14 — Pick-and-place  ·  [15:00–16:15]
**[Speaker 4]**

"This is SO3 — does it actually pick and place reliably?

We ran **120 automated trials**, 20 for each of the six categories. A success meant the piece was
detected, lifted cleanly, and released within a 10-millimeter target zone.

Final result: **92.5% — 111 of 120** — above the 90% target, with every individual category at 90%
or better. The bricks hit 95%, the plates 90%.

But here's the story I want the panel to hear: we didn't start there. Before optimization we were at
**41.7%**. We climbed to 92.5% — a 50-point jump — purely through engineering fixes, which is the
next slide. And notably, **all nine remaining failures were detection errors — zero mechanical
failures** across the successful trials. The motion side was fully solved; the only gap left is
vision under lighting."

---

## Slide 15 — The optimization log  ·  [16:15–17:30]
**[Speaker 4]**

"So how did we get from 41% to 92%? Five documented fixes.

Servos were buzzing and jamming into their end-stops — we narrowed the PWM range and that stopped it.
All five servos starting at once caused a ground bounce that reset the board — so we **move one joint
at a time**, in a configurable order, which eliminated the resets. The gripper was stalling on
objects and starving the shoulder — we set a **safe close angle tuned per piece width** and capped
travel. Servo spikes were coupling into the ESP32 — we gave the servos their **own isolated 5V/3A
supply**. And the browser couldn't fetch camera frames directly because of CORS — so we added a
backend proxy.

One point of honesty the panel may probe: when I say we solved the gripper 'stall', we do **not**
sense current — there's no ADC on the servo line. Instead we *avoid commanding an angle that would
stall*. And in fact the paper credits that gripper-angle tuning, along with pose calibration, as the
direct driver of the 92.5% result."

---

## Slide 16 — Train your own model  ·  [17:30–18:15]
**[Speaker 3]**

"Beyond the fixed six LEGO classes, a class isn't locked to *our* objects — the **Train Model** tab
lets them retrain the detector on their own.

The workflow is simple: upload a dataset in YOLOv8 format — the kind you get from a free Roboflow or
Kaggle export, with a data.yaml — pick the number of epochs, and hit Start. YOLOv8n fine-tunes in
the background with a live progress bar. And here's the nice part: the moment it finishes, the new
weights are copied into the live model path and the detector **hot-reloads automatically** — no
server restart, no config change. Their model is immediately what the Vision tab and the 'camera
sees' block use.

It's the exact same pipeline we used to train our own six-class model. The honest note is that this
is dataset-based retraining — it needs an annotated dataset, not a 'show it to the camera once'
gesture — but that's precisely what makes it a real, localizing detector rather than a toy
classifier."

---

## Slide 17 — Educational impact  ·  [18:15–19:00]
**[Speaker 2]**

"SO4 and SO5 — the educational side.

For **SO4**, we built a four-module manual with a Grade 7-to-10 progression, moving from hardware
familiarization and manual control, through block-based programming, up to fully automated detection
and sorting — aligned with constructivist, experiential learning.

For **SO5**, we evaluated with students. The System Usability Scale came back at **71.3** — rated
'Good', above the ~68 benchmark — and **90% of the 40 participating students reported increased
interest in STEM.**"

---

## Slide 18 — Deployment  ·  [19:00–19:30]
**[Speaker 1]**

"A quick note on deployment, because usability for a non-technical teacher was a real goal. It's a
**single download** for Windows, macOS, or Linux, with the app and detection model bundled inside. A
built-in **doctor** checks Python, dependencies, the model, the arm, and the camera live. One click
builds the environment and starts the IDE, and another installs the robot-flashing tools. One file,
zero terminal commands on the happy path."

---

## Slide 19 — Technology stack  ·  [skip or 15s]
**[Speaker 1]**

*(Usually skip in a 20-minute talk unless asked.)* "The stack, briefly: Blockly and vanilla JS on
the frontend, FastAPI on the backend, Ultralytics YOLOv8 and OpenCV for vision, ESP32 Arduino with
an async web server for firmware, and arduino-cli plus PyInstaller to build and ship."

---

## Slide 20 — Contributions  ·  [19:30–20:00]
**[Speaker 4]**

"To summarize our contributions: a **vision-capable 5-DOF arm at PHP 3,116**, cheaper than
commercial arms that don't even have vision; a **block-coding IDE tied to real hardware** with a
browser interpreter for instant iteration; **95.6% detection and 92.5% real sorting** through a
documented optimization pipeline; **retrainable detection** — upload a YOLOv8 dataset in the IDE
and the fine-tuned model auto-deploys as the live detector with no restart; a **fully offline
architecture** with a one-click launcher; and a **validated Grade 7–10 curriculum**."

---

## Slide 21 — Limitations  ·  [only if time / on question]
**[any speaker]**

"We're candid about the trade-offs: the remaining failures are vision under lighting, not mechanical;
custom detection needs an annotated YOLOv8 dataset, not a one-shot demo; control is local-only by
design; and the servos are open-loop — we avoid stalls by capping travel and sizing the grip, not by
sensing current."

---

## Slide 22 — Future work  ·  [only if time / on question]
**[any speaker]**

"Future work follows the data: better detection robustness under classroom lighting, OTA firmware
updates to drop the USB re-flash, running the camera as the default vision source, few-shot 'show it
once' teaching so a custom class needs no annotated dataset, and a larger longitudinal classroom
study."

---

## Slide 23 — Conclusion  ·  [20:00–20:30]
**[Speaker 1]**

"To conclude: we built a **PHP 3,116**, 3D-printed, 5-DOF arm that a beginner can **program with
blocks, teach to see, and run entirely offline** — hitting **95.6% detection** and **92.5% sorting**,
and validated with students. **All five objectives met.**

Camera sees, PC thinks, arm acts. Thank you — we welcome your questions."

---

## Slide 24 — Appendix (Q&A)  ·  [as needed]

*Not presented — jump here on questions. Quick-reference answers:*
- **Cost?** PHP 3,116, 89% of the 3,500 target; vs ~8,500 / ~17,000 commercial.
- **Is 95.6% real-world?** It's the held-out validation set; real sorting was 92.5%; the 9 misses were
  vision under lighting.
- **How do you detect a stall?** We don't sense current — we cap travel and size the grip so it
  can't jam.
- **Why YOLOv8n?** Real-time on CPU, matches the low-cost/edge goal.
- **Why AP mode over cloud?** Works offline, no accounts, one room per robot.
- **Can students use their own objects?** Yes — the Train Model tab takes a YOLOv8-format dataset
  (e.g. a Roboflow export), fine-tunes YOLOv8n, then copies best.pt → models/lego_detector.pt and
  calls detection.reload(), so it becomes the live detector with no restart.
- **Is the Train Model tab how you got the 95.57% model? / Same model?** No — two different
  training paths, same YOLOv8n *architecture*. (1) Our **deployed 95.57% model** came from the
  **Colab notebook (LEGO_Detection_Training_v3)**: a **two-stage GPU** run — Stage 1 100 epochs
  (freeze-10) → Stage 2 50 epochs fine-tune, on a Tesla T4. (2) The in-app **Train Model tab** is
  the *classroom feature* — a **single-stage CPU** retrain from plain yolov8n.pt COCO weights, so
  students can add their own objects. It proves the retrain→deploy pipeline works, but it is NOT
  how we produced the headline model and wouldn't reach 95.57% on CPU single-stage.
- **How does a trained model go live?** Automatically — trainer.py copies the new best.pt to the
  canonical path and hot-reloads the detection service; the next /detect frame uses it.
- **Dataset?** spiled-lego-bricks (Kaggle), ~3,000 images / 9,600 annotations, 70/15/15.
- **Biggest engineering win?** 41.7% → 92.5% sorting via the optimization log.
- **What if a school has no 3D printer?** Printing is a *one-time* fabrication step, not a
  per-school requirement — and the whole arm is only **142.56 g** of PLA+ (~7 h 38 min, Table 6.2).
  Three ways to get the parts without owning a printer: (1) send the open-source STLs
  (Thingiverse thing:3039476) to a **local print shop / makerspace**; (2) **one printer** at a
  university or DepEd division office prints for many schools; (3) reprint just a broken part for a
  few pesos. **Cost stays low:** a published PH service rate is **₱2.50/g** (FDM services run
  ~₱2.50–₱10/g), so the parts cost ~**₱356** (worst case ~₱1,426). The arm total goes from ₱3,116
  (in-house filament, ~₱98) to only ~**₱3,375–₱4,444** outsourced — **still under half** the
  cheapest commercial arm (₱8,500 / ₱17,000), and still the only vision-capable one. It's also
  *why* the system is repairable: reprint one part instead of buying a proprietary replacement.

---

### Timing cheat-sheet
| Segment | Slides | Target |
|---|---|---|
| Setup & framing | 1–5 | ~5.5 min |
| Literature | 6–7 | ~2 min |
| System & hardware | 8–10 | ~3.5 min |
| IDE, control, detection, sorting | 11–15 | ~5.75 min |
| Train Model, education, deployment | 16–18 | ~2 min |
| Wrap-up | 20, 23 | ~1 min |
| **Total** | | **~20 min** |

Slides 19, 21, 22 are held in reserve — present only if ahead of pace or asked.
