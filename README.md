System Monitor

Run the Qt-based system monitor GUI.

Quick start (Windows, using the workspace virtualenv):

1. Activate your venv (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the app headless for a quick startup test (no display required):

```powershell
# make sure Qt can run offscreen
$env:QT_QPA_PLATFORM='offscreen'
.venv\Scripts\python.exe tests\run_headless.py
```

3. To run the full GUI (requires display):

```powershell
.venv\Scripts\python.exe main.py
```

Files of interest:
- `main.py` — launcher
- `ui/dashboard.py` — UI implementation
- `ui/graphs.py` — fallback graph widget
- `monitoring/net.py`, `monitoring/disk.py` — monitoring helpersA modern real-time system monitoring dashboard built with Python.