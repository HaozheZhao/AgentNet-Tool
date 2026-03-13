# CCAgent Annotator

A desktop annotation tool for recording and labeling GUI interactions across Windows, Ubuntu, and macOS. Captures full video, keyboard/mouse inputs, accessibility trees, and HTML/DOM data during task execution. Built with Electron (frontend) + Flask (backend) + OBS Studio (screen recording).

## Features

- **Screen recording** via OBS Studio with automatic resolution/FPS configuration
- **Keyboard & mouse tracking** with action reduction (raw events → meaningful steps)
- **Smart text input handling**: merges character-level keystrokes into sentences, resolves backspace/arrow corrections into final intended text, stores both processed and raw keystroke sequences
- **Hotkey & shift+key recording**: properly captures ctrl+a, shift+1→! etc.
- **Pre-recording validation**: checks screen resolution (1920×1080) and OBS connection, auto-corrects output resolution if needed
- **Accessibility tree capture**: auto-detects UI elements under clicks on all platforms (Windows UI Automation, macOS Accessibility Framework, Linux AT-SPI)
- **Action review UI**: step-by-step replay with video clips, editable descriptions, justification fields, and knowledge points
- **Cloud upload** to Aliyun OSS with annotator metadata
- **HTML/DOM capture** via Chrome extension (optional)

## Architecture

```
CCAgent-Tool/
├── ccagent-annotator/           # Main application
│   ├── src/                     # Electron frontend (React + TypeScript)
│   │   ├── components/          # UI components
│   │   │   ├── Homepage/        # Recording start/stop interface
│   │   │   ├── Local/           # Local review & annotation page
│   │   │   ├── Verify/          # Verification/review page
│   │   │   ├── Dashboard/       # Task management dashboard
│   │   │   └── prerequisite/    # Pre-recording checks
│   │   ├── context/             # React context (state management)
│   │   └── index.ts             # Electron main process
│   ├── api/                     # Flask backend (Python)
│   │   ├── backend.py           # Flask app entry point (port 5328)
│   │   ├── core/                # Recording, reduction, OBS, utilities
│   │   │   ├── recorder.py      # pynput event capture
│   │   │   ├── obs_client.py    # OBS WebSocket integration
│   │   │   ├── a11y/            # Accessibility tree (per-platform)
│   │   │   └── action_reduction/# Event → action reduction pipeline
│   │   ├── services/            # Business logic (recording, upload, OBS)
│   │   └── controllers/         # HTTP + WebSocket handlers
├── setup.sh / setup.bat         # Platform setup scripts
├── start.sh / start.bat         # Platform launch scripts
├── requirements_ubuntu.txt      # Python deps (Ubuntu)
├── requirements_windows.txt     # Python deps (Windows)
├── .env.example                 # Environment config template
└── OBS_SETUP.md                 # OBS configuration guide
```

### Recording Pipeline

```
pynput events → events.jsonl → Reducer.compress() → event_buffer
  → Reducer.reduce_all() → reduced_actions (Type, Press, Click, Scroll, Drag)
  → Reducer.transform() → merge types, resolve text, fix hotkeys
  → match_element() → pair clicks with accessibility tree data
  → Reducer.finish() → video clips + reduced_events_vis.jsonl
```

### Data Captured Per Recording

```
recordings/<recording_id>/
├── events.jsonl              # Raw keyboard/mouse events
├── reduced_events_vis.jsonl  # Reduced actions with element info
├── element.jsonl             # Per-click accessibility tree snapshots
├── top_window.jsonl          # Active window name tracking
├── html.jsonl                # DOM snapshots (if Chrome plugin used)
├── metadata.json             # System info, timestamps, screen size
├── task_name.json            # Task name and description
├── annotator_info.json       # Annotator metadata (created on upload)
├── knowledge_points.json     # Knowledge points (if any)
├── *.mp4 / *.mov             # Full screen recording
└── videos/                   # Per-action video clips
```

---

## Quick Start (Ubuntu)

### Prerequisites

- **Ubuntu 22.04+** with desktop environment (GUI required)
- **OBS Studio**: `sudo apt install obs-studio`

### Installation

```bash
git clone https://github.com/HaozheZhao/CCAgent-Tool.git
cd CCAgent-Tool
chmod +x setup.sh
./setup.sh
```

This installs Miniconda (if needed), Node.js 18 (if needed), AT-SPI system packages for accessibility support, creates a conda environment with Python 3.11, and installs all dependencies including OpenCV with GStreamer support.

### Configuration

```bash
cp .env.example .env
nano .env  # Fill in Aliyun OSS credentials (only needed for cloud upload)
```

Configure OBS Studio following [OBS_SETUP.md](OBS_SETUP.md).

### Run

```bash
./start.sh
```

---

## Quick Start (Windows)

### Prerequisites

- **Git** from [git-scm.com](https://git-scm.com/download/win) (only manual install needed)
- **OBS Studio** from [obsproject.com](https://obsproject.com/)

### Installation

```cmd
git clone https://github.com/HaozheZhao/CCAgent-Tool.git
cd CCAgent-Tool
setup.bat
```

This automatically downloads and installs Miniconda (Python 3.11) and Node.js 18 if not found, creates a conda environment, and installs all dependencies.

### Configuration

```cmd
copy .env.example .env
notepad .env
```

Configure OBS Studio following [OBS_SETUP.md](OBS_SETUP.md).

### Run

```cmd
start.bat
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OSS_ENDPOINT` | Aliyun OSS endpoint (e.g., `oss-cn-shanghai.aliyuncs.com`) | For upload only |
| `OSS_ACCESS_KEY_ID` | Aliyun access key ID | For upload only |
| `OSS_ACCESS_KEY_SECRET` | Aliyun access key secret | For upload only |
| `OSS_BUCKET_NAME` | OSS bucket name | For upload only |
| `CONDA_PATH` | (Ubuntu only) Custom conda install path | No |

Cloud upload is optional. Local recording and review work without any `.env` configuration.

---

## OBS Studio Setup

OBS must be running with WebSocket enabled before recording. Key requirements:

1. **Display Capture source** recording your full main screen
2. **Desktop audio enabled**, microphone muted
3. **WebSocket server enabled** (Tools → WebSocket Server Settings → Enable, no authentication)
4. **Output resolution**: 1920×1080 (the app auto-configures this, but the desktop resolution must match)

See [OBS_SETUP.md](OBS_SETUP.md) for detailed instructions.

---

## How to Use

### Step 1: Start Recording

1. Set your screen resolution to **1920×1080**
2. Launch OBS Studio (the app will connect automatically via WebSocket)
3. Open the app and go to the **Home** page
4. Click **Start Recording**
5. Perform the task you want to annotate (browse the web, use desktop apps, etc.)
6. Click **End Recording** when done
7. Wait for processing to complete (the terminal shows progress)

### Step 2: Fill in Annotator Info

After recording, open the recording from the sidebar to enter the **Local Review** page. Before reviewing steps, fill in the **Annotator Info** block at the top:

| Field | Description | Example |
|-------|-------------|---------|
| **Username** | Your annotator name | `alice` |
| **Task ID** | Identifier for the task you performed | `search_001` |
| **Query** | The instruction or goal of the task | `Search for the nearest coffee shop on Google Maps` |
| **Upload Folder** | (Must) Custom OSS upload folder | `batch_march2026` |
| **Step by Step Instruction** | (optional) the Step by Step Instruction of the task  | `......` |

Click **Save** to lock the info. The task name is auto-generated as `username_taskID_NNN` (e.g., `alice_search_001_000`), with the number auto-incrementing if you have multiple recordings with the same base name.

### Step 3: Review & Annotate Each Step

The app breaks your recording into individual actions (clicks, typing, scrolling, etc.). For each step:

1. **Watch the video clip** — verify the action is correct
2. **Delete redundant steps** — remove accidental clicks or unnecessary actions by clicking the **x** button
3. **Check the steps and add justification** — add justification for the step
4. **Add knowledge points** (optional) — add any relevant notes in the Knowledge Points section, like "Create a folder in File Explorer", "Filter files by type in File Explorer", "Move files via drag-and-drop or cut/paste

### Step 4: Upload

1. Verify all steps look correct
2. Click **Upload** to send the recording to the cloud (requires OSS credentials in `.env`)
3. The recording is packaged with all metadata and uploaded to Aliyun OSS

### What Gets Uploaded

Each uploaded recording contains:
- **Video** — full screen recording + per-action clips
- **Events** — reduced action sequence with descriptions and element info
- **Accessibility data** — UI element trees captured at each click
- **Metadata** — system info, timestamps, screen resolution
- **Annotator info** — username, task ID, query, upload timestamp

---

## HTML/DOM Capture (Optional)

To capture HTML snapshots during recording (useful for web-based tasks), install the [CCAgent Chrome Plugin](https://github.com/fyq5166/AgentNet-Chrome-Plugin) in Google Chrome. The plugin automatically sends DOM data to the backend during recording.

---

## Platform Support

| Platform | Screen Recording | Input Tracking | Accessibility Tree | Status |
|----------|-----------------|----------------|-------------------|--------|
| Ubuntu 22.04+ | OBS Studio | pynput | AT-SPI (PyGObject) | Full support |
| Windows 10/11 | OBS Studio | pynput | UI Automation (pywinauto) | Full support |
| macOS 10.14+ | OBS Studio | pynput | Accessibility Framework (AppKit) | Full support |

---

## Build from Source

Requires Python >= 3.11 and Node.js >= 18.

```bash
pip install -r requirements_ubuntu.txt  # or requirements_windows.txt
cd ccagent-annotator
npm install
npm run build-flask   # Build backend
npm run make          # Build Electron app
```

The built application will be in `ccagent-annotator/out/`.

---

## License

[MIT License](LICENSE)
