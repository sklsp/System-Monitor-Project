# System Monitor Dashboard

A real-time system monitoring dashboard for Windows, built with Python and PyQt5. It shows live CPU, RAM, disk, GPU and network statistics in a desktop window, plus a dedicated gaming tab that tracks the game you are playing.

## What it does

Three tabs (see `ui/dashboard/main.py`):

- **Gaming** - detects the foreground game (`GetForegroundWindow`) and shows IN GAME / DESKTOP status, live CPU/GPU/RAM/VRAM/ping for that session, a bottleneck estimate (CPU, GPU or RAM bound), warnings on temperature/RAM/ping, session peaks since start, ping graphs to Google and Cloudflare, top processes by CPU, and an always-on-top overlay mode.
- **Overview** - compact cards with sparklines for CPU, GPU, memory, disk, network and the top process list; cards reflow as you resize the window.
- **Details** - per-subsystem tabs (CPU, Memory, Disk, GPU, Network) with deeper metrics such as per-core usage, clock speed, swap, read/write rates and link speed.

Sensors come from `psutil`, WMI (`win32com`) and `GPUtil`; CPU temperature falls back to OpenHardwareMonitor when available (`monitoring/cpu_temp.py`).

## Tech used

- Python 3.10+, PyQt5 + PyQtChart for the UI
- psutil (CPU/RAM/disk/network), GPUtil (GPU), pywin32 (WMI, Windows only)
- No persistence: everything is live sampling, nothing is stored to disk

## How to run (Windows)

Easiest: double-click `start.bat`. It finds Python, creates `.venv`, installs `requirements.txt` on first run, then starts the app. Use `start_admin.bat` if CPU temperature shows N/A (some machines need admin rights for WMI).

Manual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Tests

No pytest suite; two headless smoke scripts that run the real app offscreen:

```powershell
$env:QT_QPA_PLATFORM="offscreen"
python tests\run_headless.py          # boots the dashboard for 3 seconds, exits clean
python tests\overview_layout_test.py  # resizes the window and prints card dimensions
```

## Known limits

- Windows only (WMI and `ctypes.windll` calls throughout).
- CPU temperature needs admin rights or a running OpenHardwareMonitor; otherwise it shows N/A.
- GPU metrics depend on what your driver exposes through WMI/GPUtil; some fields may be blank on certain GPUs.
- No history, export or alerting yet: the dashboard is live-only by design for now.

## Author

Made by sklsp.
