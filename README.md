# Block Robot IDE

Program a real robot arm by **snapping blocks together** — no typing code required.

This is a web app where you build a program out of colorful blocks (like Scratch),
and the robot arm does what your blocks say: move to a position, open or close its
gripper, look at an object with a camera, and sort it into the right bin.

---

## What this project is

**DLSU Thesis Project — RIAL-3-2425-C7**
*Development of a Cost-Effective 3D-Printed Pick-and-Place Robotic Arm for Object
Sorting and Educational Applications*

The robot is a 5-joint (5-DOF) arm built from 3D-printed parts and hobby servos.
You control it from a web page that has five tabs:

| Tab | What you do there |
|-----|-------------------|
| ⚙️ **Setup** | Name your robot's WiFi and set its password |
| 🎯 **Teach Poses** | Move the real arm with sliders, then save a position (a "pose") |
| 📦 **Program** | Drag blocks together to make the robot do things |
| 📷 **Vision** | Point a camera at objects; the computer recognizes them |
| 🎓 **Train Model** | Teach the computer to recognize *your own* objects |

The arm runs on an **ESP32** microcontroller. The camera and the "thinking" part
(recognizing objects) run on your **computer** — the camera takes the picture, the
computer figures out what's in it, and the arm acts on the result.

> **In one sentence:** the camera *sees*, the PC *thinks*, and the arm *acts*.

---

## Easiest install (no terminal)

> **One thing to install first: Python 3.8+.** The launcher sets everything
> else up for you, but it needs Python already on your computer to do it. Get
> it from [python.org/downloads](https://www.python.org/downloads/) (on the
> installer, tick **"Add Python to PATH"**). If you skip this, the launcher's
> first check shows ❌ Python and tells you the same thing.

1. Go to the [latest release](https://github.com/daxtangco/block-coding-robot/releases/latest)
   and download the file for your computer:
   - Windows: `Block-Robot.exe`
   - macOS: `Block-Robot` (right-click → Open the first time)
2. Double-click it. The launcher window opens. (The app and the detection
   model are bundled inside — no separate download needed.)
3. Click **⚙️ Set up / update** once and wait — it builds a Python environment
   and installs the packages the IDE needs.
4. Click **▶ Start IDE**. Your browser opens the IDE.

If a row shows ❌, the launcher tells you exactly what to do (for example,
install Python or join the robot's WiFi), then click **🩺 Check my system**
again.

---

## Part 1 — Run the IDE on your computer

You can do this part with **no robot and no camera** — it's how you build and preview
programs.

### What you need first

- A computer with **Python 3.8 or newer** ([download Python](https://www.python.org/downloads/))
  - On the installer, tick **"Add Python to PATH"**.
- That's it for the basics. (Extra steps for the camera and the robot come later.)

### Step 1 — Get the code

Open a terminal (Command Prompt, PowerShell, or Terminal) and run:

```bash
git clone https://github.com/daxtangco/block-coding-robot.git
cd block-coding-robot
```

### Step 2 — Install the basic parts

```bash
pip install -r requirements.txt
```

This installs the web server that runs the IDE. It's small and quick.

### Step 3 — Start the IDE

```bash
python -m uvicorn backend.main:app --reload
```

Leave this window open — it's the server. You'll see a message saying it's running.

### Step 4 — Open it in your browser

Go to **http://localhost:8000**

You should see the Block Robot IDE with the five tabs at the top. 🎉

> **To stop the server later:** click the terminal window and press `Ctrl + C`.

---

## Part 2 — Turn on the camera & object detection (optional)

Do this if you want the **Vision** tab and **Train Model** tab to work. It needs a few
bigger packages (they include the AI model that recognizes objects).

### Step 1 — Install the vision packages

```bash
pip install -r requirements-vision.txt
```

This may take a few minutes the first time — it's downloading the object-detection
software.

### Step 2 — Get a detection model

The Vision tab needs a trained "model" — the file that knows how to recognize objects.
You have two choices:

- **Use the included LEGO model** — if a file named `lego_detector.pt` is in the
  `models/` folder, the robot can already recognize six LEGO piece types
  (`brick_1x6`, `brick_2x2`, `brick_2x4`, `plate_1x2`, `plate_2x2`, `plate_2x4`).
- **Train your own** — see Part 4 below to teach it your own objects.

### Step 3 — Use the Vision tab

1. Restart the server (`Ctrl + C`, then run the `uvicorn` command again).
2. Open http://localhost:8000 and click the **📷 Vision** tab.
3. Click **Start Camera** and allow the browser to use your webcam.
4. Hold an object up — boxes appear around things the model recognizes, and it shows
   which bin each one goes to.

> The camera here is your **computer's webcam**. Later, an **ESP32-CAM** can send the
> picture instead — the rest works the same way.

---

## Part 3 — Connect the real robot arm (optional)

Do this when you have the physical robot built and want your blocks to move it.

### How it works

The robot makes its **own WiFi network**. You connect your phone or laptop to that
network, and a control page opens automatically. No home WiFi or internet needed.

### One-time setup (flashing the robot)

1. Plug the ESP32 into your computer with a USB cable.
2. Install **arduino-cli** — follow [docs/ARDUINO_CLI_SETUP.md](docs/ARDUINO_CLI_SETUP.md).
3. In the IDE, go to the **⚙️ Setup** tab and click **🔨 Build & Flash**. Wait about 2
   minutes while it builds the robot's program and loads it on.
4. Upload the robot's web page files (one time only):
   ```bash
   python scripts/upload_spiffs.py --port COM3
   ```
   Replace `COM3` with your ESP32's port (it might be `COM4`, or on Mac/Linux something
   like `/dev/ttyUSB0`).

Full details and pictures are in [docs/AP_MODE_SETUP.md](docs/AP_MODE_SETUP.md).

### Every-day use

1. Power on the robot (USB power bank or adapter).
2. On your phone or laptop, open WiFi settings and connect to:
   - **Network:** `RobotArm-XXXX`
   - **Password:** `robot1234`
3. A control page opens at **http://192.168.4.1** automatically.
4. Use the **🎯 Teach Poses** tab to move the arm with sliders and save positions, then
   use those positions in your block program.

Wiring the servos is explained in [docs/PCA9685_WIRING_GUIDE.md](docs/PCA9685_WIRING_GUIDE.md).

---

## Part 4 — Train the robot to see your own objects

The **🎓 Train Model** tab lets you teach the computer to recognize objects *you* pick
— not just LEGO.

1. **Get a dataset.** A dataset is a folder of labeled pictures. Download a free one and
   **export it in "YOLOv8" format** (you get a `.zip` with a `data.yaml` inside). Good
   places to find one:
   - **Roboflow Universe** — https://universe.roboflow.com (thousands of ready datasets)
   - **Kaggle Datasets** — https://www.kaggle.com/datasets
   - **Google Open Images** — https://storage.googleapis.com/openimages/web/index.html
2. In the **Train Model** tab, click **Upload & Validate** and choose your `.zip`. It
   tells you how many classes and images it found.
3. Pick the number of **epochs** (how many times it studies the pictures — more = slower
   but usually better; **20** is a good start).
4. Click **Start Training** and watch the progress bar.
5. When it finishes, **your** model becomes the live one — the Vision tab and the
   "camera sees" block now recognize your objects automatically.

> **Tip:** training is much faster on a computer with a graphics card (GPU). There's a
> free Google Colab notebook for that: `LEGO_Detection_Training_v2.ipynb`.

---

## Make your first block program

1. Click the **📦 Program** tab.
2. Drag blocks from the left toolbox into the workspace. They snap together like LEGO:
   - **Arm Control** (blue): *move to pose*, *open/close gripper*, *wait*
   - **Vision** (purple): *camera sees …*, *confidence*
   - **Logic** (green): *forever*, *if / else*, *repeat*
3. Watch the right side — it shows the real robot code your blocks make, live.
4. A simple sorting program reads like this:

   ```
   forever
     if camera sees "brick_2x4" with confidence > 50%
       move arm to pose PICKUP
       close gripper
       wait 1 second
       move arm to pose DROP_ZONE
       open gripper
   ```

---

## Folder map

```
block-coding-robot/
├── backend/              The server (Python). Runs the IDE and the AI detection.
│   ├── main.py           Starts everything.
│   ├── routes/           The web addresses the page talks to (build, poses, detect, train…).
│   ├── services/         The real work: builder, detection, trainer, storage.
│   └── templates/        The robot's firmware (the .ino files flashed to the ESP32).
├── frontend/             The web page you see in the browser.
│   ├── index.html        The five-tab layout.
│   ├── css/              How it looks.
│   └── js/               How it behaves (blocks, code generator, each tab).
├── docs/                 Step-by-step guides (flashing, wiring, AP mode, troubleshooting).
├── models/               Trained detection model(s) live here.
├── scripts/              Helper scripts (e.g. uploading the robot's web files).
├── config.py             Central settings: object classes, file paths, training options.
├── requirements.txt          Basic packages (just the IDE).
└── requirements-vision.txt   Extra packages for the camera & training.
```

---

## If something goes wrong

**The page won't open at localhost:8000**
- Make sure the server window is still running and didn't show an error.
- Check it's alive: open http://localhost:8000/health — it should say it's okay.
- Try a hard refresh in the browser: `Ctrl + F5`.

**"Build & Flash" fails**
- arduino-cli probably isn't installed yet — see [docs/ARDUINO_CLI_SETUP.md](docs/ARDUINO_CLI_SETUP.md).
- Make sure the ESP32 is plugged in and you picked the right port.

**The Vision or Train Model tab shows an error about a missing module**
- You likely skipped Part 2. Run `pip install -r requirements-vision.txt`.

**The camera won't start**
- Your browser must have permission to use the webcam — allow it when asked.
- Chrome or Edge work best.

**Can't connect to the robot's WiFi**
- Make sure the robot is powered on and you flashed it (Part 3).
- The network is `RobotArm-XXXX`, password `robot1234`. See
  [docs/TROUBLESHOOTING_AP_MODE.md](docs/TROUBLESHOOTING_AP_MODE.md).

---

## Guides for each part

- [Arduino CLI Setup](docs/ARDUINO_CLI_SETUP.md) — install the tool that flashes the robot
- [Access Point Mode Setup](docs/AP_MODE_SETUP.md) — flash the robot and connect to its WiFi
- [PCA9685 Wiring Guide](docs/PCA9685_WIRING_GUIDE.md) — how to wire the servos
- [Flash Instructions](docs/FLASH_INSTRUCTIONS.md) — loading firmware onto the ESP32
- [Hardware Pinout](docs/HARDWARE_PINOUT.md) — which pin connects to what
- [AP Mode Troubleshooting](docs/TROUBLESHOOTING_AP_MODE.md) — fixing connection problems
- [Testing Guide](TESTING.md) — checklists for trying every feature

---

## License & contact

Academic use — DLSU Thesis Project RIAL-3-2425-C7. For questions, contact the project
team.
