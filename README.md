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

### ⚙️ System
- Active processes list
- Real-time updates
- Basic performance graphs
- Dark mode UI

---

## 🚀 Planned Features

- CPU & GPU temperature monitoring
- Fan speed tracking
- Clock speed monitoring (CPU/GPU)
- FPS overlay for gaming
- In-game performance statistics
- Ping / latency monitoring
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

## ⚙️ Installation

### Step 1: Clone the repository
```bash
git clone <your-repo-url>
cd System-Monitor-Project
```

### Step 2: Create virtual environment
```bash
python -m venv .venv
```

### Step 3: Activate environment (Windows PowerShell)
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies
```bash
pip install -r requirements.txt
```

**If requirements file is missing:**
```bash
dir -Recurse requirements.txt
cd <folder-containing-file>
pip install -r requirements.txt
```

---

## 🚀 Running the Application

### Start GUI (Main Mode)
```bash
python main.py
```

### Headless Test Mode (No GUI)
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
