# 🖥️ System Monitor Dashboard

A real-time system monitoring dashboard built with Python and PyQt5.

This application displays live hardware statistics such as CPU, RAM, disk usage, GPU, and network activity through a clean desktop interface.

> **Note:** The project is still under active development, so features and structure may change over time.

---

## ✨ Features

### 🖥️ CPU
- CPU load
- Core usage
- Clock frequency

### 🧠 Memory (RAM)
- RAM usage
- Total / used / available memory
- Swap usage

### 💾 Disk
- Read / write activity
- Total / used / free storage

### 🎮 GPU
- GPU load
- VRAM usage
- GPU name

### 🌐 Network
- Upload / download activity
- Ethernet link speed

### 🎮 Gaming (tab)
- Actief venster / game-detectie (IN GAME / DESKTOP)
- Live CPU, GPU, RAM, VRAM en ping
- Bottleneck-analyse (CPU/GPU/RAM-bound)
- Prestatiewaarschuwingen (temp, RAM, ping)
- Session peaks sinds start
- Ping-grafiek (Google + Cloudflare)
- Top processen op CPU
- Altijd-bovenaan overlay-modus

### ⚙️ System
- Active processes list
- Real-time updates
- Basic performance graphs
- Dark mode UI

---

## 🚀 Planned Features

- Fan speed tracking
- FPS overlay for gaming (in-game hook)
- Frame time / 1% lows
- Bandwidth usage graphs
- System uptime tracking
- Advanced process manager
- Performance history graphs
- Export system logs
- Custom alerts (high usage / temperature)
- Gaming dashboard mode
- Lightweight overlay mode
- RGB-inspired UI themes
- Multi-monitor support
- Discord webhook integration
- Hardware benchmarking tools

---

## 🛠️ Built With

- Python 3.x
- PyQt5
- psutil
- GPUtil
- CustomTkinter (if used)
- Matplotlib
---

## ⚙️ Installation (beginner-friendly)

You do **not** need to be a programmer. If you can install a normal program and copy a few commands, you can run this app.

### Easiest way — double-click `start.bat` (Windows)

1. Install **Python** once (see below) with **Add to PATH** enabled.
2. Put the project folder on your PC (ZIP download or Git clone).
3. **Double-click `start.bat`** in the `System-Monitor-Project` folder.

The batch file will automatically:

- find Python on your PC  
- create a virtual environment (first time only)  
- install required packages (first time only)  
- start the System Monitor window  

If something fails, the black window stays open with an error message you can read or copy for help.

> **Next times:** just double-click `start.bat` again — setup is skipped if everything is already installed.

---

### Manual install (if you prefer the terminal)

### What you need first

| Item | What it is | How to check |
|------|------------|--------------|
| **Windows 10 or 11** | Your PC operating system | Most gaming PCs use this |
| **Python 3.10+** | The language this app runs on | Open **Command Prompt** or **PowerShell**, type `python --version`, press Enter. You should see something like `Python 3.12.x` |
| **Internet** | Only for the first install | To download Python (if needed) and required packages |

**Don’t have Python yet?**

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/) and download the latest **Windows** installer.
2. Run the installer.
3. On the first screen, turn **on** the box that says **“Add python.exe to PATH”** (this is important).
4. Click **Install Now** and finish the wizard.
5. Close and reopen any terminal windows, then try `python --version` again.

> **Using Cursor or VS Code?** You can also press **F5** after opening this folder, if a run configuration is already set up. The steps below still help when something does not start.

---

### Step 1 — Get the project on your PC

Pick **one** method.

**Option A — Download as ZIP (easiest if you don’t use Git)**

1. On GitHub, click the green **Code** button → **Download ZIP**.
2. Extract the ZIP (right-click → **Extract All…**).
3. You should end up with a folder named something like `System-Monitor-Project`.
4. Remember where you saved it (e.g. `Desktop\System-Monitor-Project`).

**Option B — Git clone (if you already use Git)**

```bash
git clone <your-repo-url>
cd System-Monitor-Project
```

---

### Step 2 — Open a terminal in the project folder

The terminal is the black or blue window where you type commands.

**Windows 11 / 10 (simple way):**

1. Open File Explorer and go to your `System-Monitor-Project` folder.
2. Click the address bar at the top, type `powershell`, press **Enter**.  
   A PowerShell window opens already “inside” the right folder.

**Alternative:** Right-click inside the folder → **Open in Terminal** (wording may vary).

You should see a path ending in `System-Monitor-Project` in the window. If not, you’re in the wrong folder.

---

### Step 3 — Install what the app needs

Copy and paste these commands **one at a time**, press **Enter** after each, and wait until it finishes.

**Recommended (keeps this project separate from other Python apps):**

```powershell
python -m venv .venv
```

If Windows blocks the next command, run this once (only affects the current window):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the start of the line — that means it worked.

**Install packages:**

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

That may take a few minutes. Errors in red are what matter; yellow warnings are often fine.

**Quick path (skip virtual environment):**  
If the steps above confuse you, you can try only:

```powershell
python -m pip install -r requirements.txt
```

It often works, but installing into a `.venv` is cleaner if you use Python for other projects too.

---

### Step 4 — Start the app

With the same terminal open (and `(.venv)` visible if you used Step 3):

```powershell
python main.py
```

A window titled **System Monitor — Gaming** should open.

To close the app, close the window or press **Ctrl+C** in the terminal.

---

## 🚀 Running the app again later

**Easy:** double-click **`start.bat`** again.

**Manual:** open PowerShell in the project folder, run `.\.venv\Scripts\Activate.ps1`, then `python main.py`.

---

## 🩹 Something went wrong?

| Problem | What to try |
|---------|-------------|
| **`'python' is not recognized`** | Reinstall Python and enable **Add to PATH**, then restart the PC. Or try `py main.py` instead of `python main.py`. |
| **`pip` is not recognized** | Use `python -m pip install -r requirements.txt` instead. |
| **Red errors while installing** | Make sure you’re in the folder that contains `requirements.txt`. Run `dir` and check that `main.py` is listed. |
| **Window flashes and closes** | Run from PowerShell (Step 2) so you can read the error message. |
| **CPU temperature shows N/A** | Allow **LibreHardwareMonitor** in Windows Defender (first run may download it). Some PCs also need **Run as administrator**. |
| **Weird font messages in the terminal** | Safe to ignore on Windows. |

Still stuck? Copy the **full red error text** from PowerShell when asking for help — that makes fixes much faster.

---

## 🧪 Headless test (optional, for developers)

You can skip this unless someone asked you to test without a window:

```powershell
$env:QT_QPA_PLATFORM="offscreen"
python tests\run_headless.py
```
---

## 📁 Project Structure

```
System-Monitor-Project/
│
├── main.py                 # Application entry point
├── requirements.txt        # Dependencies
├── README.md               # Project description
│
├── ui/
│   ├── dashboard.py        # Main UI implementation
│   └── graphs.py           # Graph components
│
├── monitoring/
│   ├── cpu.py
│   ├── disk.py
│   ├── net.py
│   └── gpu.py
│
├── tests/
│   └── run_headless.py
│
└── __pycache__
```

---

## ⚠️ Notes

- This project is still under active development
- Some features are experimental or incomplete
- Qt font warnings on Windows can be safely ignored
- Structure may change as the project evolves

---

## 👨‍💻 Author

Made by **sklsp**

---

## 🎯 Future Vision

This project is being developed into a lightweight, gaming-focused system monitor similar to tools like MSI Afterburner, but with a modern Python-based GUI.
