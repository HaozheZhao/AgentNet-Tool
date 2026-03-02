# AgentNet Annotator

A desktop annotation tool for recording and labeling GUI interactions on Ubuntu and Windows. Captures full video, keyboard/mouse inputs, accessibility trees, and HTML/DOM data during task execution. Built with Electron (frontend) + Flask (backend) + OBS Studio (screen recording).

## Features

- **Screen recording** via OBS Studio with automatic resolution/FPS configuration
- **Keyboard & mouse tracking** with action reduction (raw events → meaningful steps)
- **Smart text input handling**: merges character-level keystrokes into sentences, resolves backspace/arrow corrections into final intended text
- **Hotkey & shift+key recording**: properly captures ctrl+a, shift+1→! etc.
- **Pre-recording validation**: checks screen resolution (1920x1080) and OBS connection before recording starts
- **Action review UI**: step-by-step replay with video clips, editable descriptions, justification fields
- **Cloud upload** to Aliyun OSS
- **Accessibility tree capture** (Windows/macOS) and HTML/DOM capture (via Chrome plugin)

## Architecture

```
AgentNet-Tool/
├── agentnet-annotator/          # Main application
│   ├── src/                     # Electron frontend (React + TypeScript)
│   │   ├── components/          # UI components (recording, review, dashboard)
│   │   ├── context/             # React context (state management)
│   │   └── index.ts             # Electron main process
│   ├── api/                     # Flask backend (Python)
│   │   ├── backend.py           # Flask app entry point (port 5328)
│   │   ├── core/                # Recording, reduction, OBS, utilities
│   │   │   ├── recorder.py      # pynput event capture
│   │   │   ├── obs_client.py    # OBS WebSocket integration
│   │   │   └── action_reduction/# Event → action reduction pipeline
│   │   ├── services/            # Business logic (recording, upload, OBS)
│   │   └── controllers/         # HTTP + WebSocket handlers
│   └── scripts/                 # Utility scripts
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
  → Reducer.finish() → video clips + reduced_events_vis.jsonl
```

---

## Quick Start (Ubuntu)

### Prerequisites

- **Ubuntu 22.04+** with desktop environment (GUI required)
- **OBS Studio**: `sudo apt install obs-studio`

### Installation

```bash
git clone https://github.com/HaozheZhao/AgentNet-Tool.git
cd AgentNet-Tool
chmod +x setup.sh
./setup.sh
```

This installs Miniconda (if needed), Node.js 18 (if needed), creates a `agentnet` conda environment with Python 3.11, and installs all dependencies including OpenCV with GStreamer support.

### Configuration

```bash
cp .env.example .env
nano .env  # Fill in Aliyun OSS credentials for cloud upload
```

Configure OBS Studio following [OBS_SETUP.md](OBS_SETUP.md).

### Run

```bash
./start.sh
```

---

## Quick Start (Windows)

### Prerequisites

- **Python 3.11+** from [python.org](https://www.python.org/downloads/)
- **Node.js 18+** from [nodejs.org](https://nodejs.org/)
- **OBS Studio** from [obsproject.com](https://obsproject.com/)

### Installation

```cmd
git clone https://github.com/HaozheZhao/AgentNet-Tool.git
cd AgentNet-Tool
setup.bat
```

This creates a Python venv, installs pip and npm dependencies.

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

| Variable | Description |
|----------|-------------|
| `OSS_ENDPOINT` | Aliyun OSS endpoint (e.g., `oss-cn-shanghai.aliyuncs.com`) |
| `OSS_ACCESS_KEY_ID` | Aliyun access key ID |
| `OSS_ACCESS_KEY_SECRET` | Aliyun access key secret |
| `OSS_BUCKET_NAME` | OSS bucket name |
| `CONDA_PATH` | (Ubuntu only) Custom conda install path |

---

## OBS Studio Setup

OBS must be running with WebSocket enabled before recording. Key requirements:

1. **Display Capture source** recording your full main screen
2. **Desktop audio enabled**, microphone muted
3. **WebSocket server enabled** (Tools → WebSocket Server Settings → Enable, no authentication)
4. **Output resolution**: 1920x1080 (the app auto-configures this, but the desktop resolution must match)

See [OBS_SETUP.md](OBS_SETUP.md) for detailed instructions with screenshots.

---

## Usage

### Recording

1. Ensure screen resolution is **1920x1080** and OBS is running
2. Click **Start** in the app to begin recording
3. Perform the annotation task
4. Click **End Recording** to stop
5. Wait for data processing to complete (terminal shows "reduce time")

### Review & Annotate

1. Open the recorded session from the sidebar
2. Review each step — delete redundant steps (click **x** on each step)
3. Fill in **justification** for every step (why the action is necessary)
4. Set task name: `yourname_workerID/taskID` (e.g., `xiaoming_worker_1/0001`)
5. Click **Upload**

### HTML/DOM Capture (Optional)

To capture HTML during recording, use [Google Chrome Dev](https://developer.chrome.com/) with the [AgentNet Chrome Plugin](https://github.com/fyq5166/AgentNet-Chrome-Plugin).

---

## Build from Source

Requires Python >= 3.11 and Node.js >= 18.

```bash
pip install -r requirements_ubuntu.txt  # or requirements_windows.txt
cd agentnet-annotator
npm install
npm run build-flask   # Build backend
npm run make          # Build Electron app
```

The built application will be in `agentnet-annotator/out/`.

---

## License

[MIT License](LICENSE)
