"""CPU temperature collection for Windows and other platforms."""

from __future__ import annotations

import subprocess
import sys
import threading
import time
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import psutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENDOR_DIR = PROJECT_ROOT / "vendor" / "LibreHardwareMonitor"
LHM_DLL = VENDOR_DIR / "LibreHardwareMonitorLib.dll"
LHM_EXE = VENDOR_DIR / "LibreHardwareMonitor.exe"
LHM_PS1 = Path(__file__).with_name("read_cpu_temp_lhm.ps1")
LHM_RELEASE_URL = (
    "https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/"
    "releases/download/v0.9.4/LibreHardwareMonitor-net472.zip"
)

CPU_SENSOR_KEYS = ("cpu", "core", "package", "tctl", "tdie", "ccd", "socket", "dies")
GPU_SENSOR_KEYS = ("gpu", "graphics", "geforce", "radeon", "video", "vram")

_lhm_process = None
_lhm_started_by_app = False
_lhm_elevated_attempted = False
_setup_lock = threading.Lock()


def _valid_celsius(value: float) -> bool:
    return 1.0 <= value <= 120.0


def _is_cpu_sensor_name(name: str) -> bool:
    label = (name or "").lower()
    if any(key in label for key in GPU_SENSOR_KEYS):
        return False
    return any(key in label for key in CPU_SENSOR_KEYS)


def _normalize_tenths_kelvin(raw: float) -> float:
    if raw > 1000:
        return (raw / 10.0) - 273.15
    if raw > 100:
        return raw / 10.0
    return raw


def _parse_text_values(output: str) -> list[float]:
    readings: list[float] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if "=" in line:
            _, _, line = line.partition("=")
            line = line.strip()
        try:
            value = float(line)
        except ValueError:
            continue
        temp_c = _normalize_tenths_kelvin(value)
        if _valid_celsius(temp_c):
            readings.append(round(temp_c, 1))
    return readings


def _unique(readings: list[float]) -> list[float]:
    seen = set()
    result: list[float] = []
    for value in readings:
        key = round(value, 1)
        if key in seen:
            continue
        seen.add(key)
        result.append(key)
    return result


def _from_psutil() -> list[float]:
    if not hasattr(psutil, "sensors_temperatures"):
        return []
    readings: list[float] = []
    try:
        temps = psutil.sensors_temperatures()
    except Exception:
        return []
    for sensor_name, entries in temps.items():
        for entry in entries:
            if entry.current is None:
                continue
            label = (entry.label or sensor_name).lower()
            if _is_cpu_sensor_name(label) and _valid_celsius(entry.current):
                readings.append(round(entry.current, 1))
    return readings


def _from_wmi_namespace(namespace: str) -> list[float]:
    try:
        import win32com.client
    except ImportError:
        return []

    readings: list[float] = []
    try:
        if namespace == r"root\wmi":
            wmi_obj = win32com.client.GetObject(r"winmgmts:\\.\root\wmi")
            sensors = wmi_obj.ExecQuery("SELECT * FROM MSAcpi_ThermalZoneTemperature")
            for sensor in sensors:
                temp_c = sensor.CurrentTemperature / 10.0 - 273.15
                if _valid_celsius(temp_c):
                    readings.append(round(temp_c, 1))
            return readings

        wmi_obj = win32com.client.GetObject(rf"winmgmts:\\.\{namespace}")
        query = "SELECT Name, Value FROM Sensor WHERE SensorType='Temperature'"
        for sensor in wmi_obj.ExecQuery(query):
            name = str(sensor.Name)
            if not _is_cpu_sensor_name(name):
                continue
            try:
                value = float(sensor.Value)
            except (TypeError, ValueError):
                continue
            if _valid_celsius(value):
                readings.append(round(value, 1))
    except Exception:
        return []
    return readings


def _from_powershell(command: str, timeout: int = 8) -> list[float]:
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        return []
    if proc.returncode != 0:
        return []
    return _parse_text_values(proc.stdout)


def _from_lhm_dll() -> list[float]:
    if not LHM_DLL.is_file() or not LHM_PS1.is_file():
        return []
    try:
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(LHM_PS1),
                "-DllDirectory",
                str(VENDOR_DIR),
            ],
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        return []
    if proc.returncode != 0:
        return []
    return _parse_text_values(proc.stdout)


def find_lhm_directory() -> Path | None:
    candidates = [
        VENDOR_DIR,
        Path(r"C:\Program Files\LibreHardwareMonitor"),
        Path(r"C:\Program Files (x86)\LibreHardwareMonitor"),
    ]
    for path in candidates:
        if (path / "LibreHardwareMonitorLib.dll").is_file():
            return path
    return None


def ensure_lhm_installed() -> bool:
    if LHM_DLL.is_file():
        return True
    with _setup_lock:
        if LHM_DLL.is_file():
            return True
        VENDOR_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = VENDOR_DIR.parent / "lhm.zip"
        try:
            urlretrieve(LHM_RELEASE_URL, zip_path)
            with zipfile.ZipFile(zip_path, "r") as archive:
                archive.extractall(VENDOR_DIR)
            zip_path.unlink(missing_ok=True)
        except Exception:
            return False
    return LHM_DLL.is_file()


def _start_lhm_process(exe: Path, lhm_dir: Path, elevated: bool = False) -> None:
    global _lhm_process, _lhm_started_by_app, _lhm_elevated_attempted

    if elevated:
        _lhm_elevated_attempted = True
        script = (
            f"Start-Process -FilePath '{exe}' -WorkingDirectory '{lhm_dir}' "
            "-Verb RunAs -WindowStyle Hidden"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=15,
        )
        time.sleep(4)
        return

    try:
        _lhm_process = subprocess.Popen(
            [str(exe)],
            cwd=str(lhm_dir),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        _lhm_started_by_app = True
        time.sleep(3)
    except Exception:
        _lhm_process = None


def _has_cpu_temp_data() -> bool:
    return bool(
        _from_wmi_namespace(r"root\LibreHardwareMonitor")
        or _from_wmi_namespace(r"root\OpenHardwareMonitor")
        or _from_lhm_dll()
    )


def ensure_lhm_running() -> None:
    global _lhm_elevated_attempted

    if _has_cpu_temp_data():
        return

    lhm_dir = find_lhm_directory()
    if lhm_dir is None and ensure_lhm_installed():
        lhm_dir = VENDOR_DIR
    if lhm_dir is None:
        return

    exe = lhm_dir / "LibreHardwareMonitor.exe"
    if not exe.is_file():
        return

    if _lhm_process is not None and _lhm_process.poll() is None and _has_cpu_temp_data():
        return

    _start_lhm_process(exe, lhm_dir, elevated=False)

    if not _has_cpu_temp_data() and not _lhm_elevated_attempted:
        _start_lhm_process(exe, lhm_dir, elevated=True)


def get_cpu_temperature_readings() -> list[float]:
    readings = _from_psutil()
    if readings:
        return _unique(readings)

    if sys.platform.startswith("win"):
        ensure_lhm_installed()
        ensure_lhm_running()

        for namespace in (r"root\LibreHardwareMonitor", r"root\OpenHardwareMonitor"):
            readings = _from_wmi_namespace(namespace)
            if readings:
                return _unique(readings)

        readings = _from_lhm_dll()
        if readings:
            return _unique(readings)

        readings = _from_wmi_namespace(r"root\wmi")
        if readings:
            return _unique(readings)

        ps_script = r"""
$sensors = Get-CimInstance -Namespace root/LibreHardwareMonitor -ClassName Sensor -ErrorAction SilentlyContinue |
  Where-Object { $_.SensorType -eq 'Temperature' }
foreach ($s in $sensors) {
  $n = $s.Name.ToLower()
  if ($n -match 'gpu|graphics|geforce|radeon|video|vram') { continue }
  if ($n -notmatch 'cpu|core|package|tctl|tdie|ccd|socket|dies') { continue }
  if ($s.Value -ge 1 -and $s.Value -le 120) { $s.Value }
}
"""
        readings = _from_powershell(ps_script)
        if readings:
            return _unique(readings)

        for command in (
            "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature | "
            "Select-Object -ExpandProperty CurrentTemperature",
            "Get-CimInstance -ClassName Win32_TemperatureProbe | "
            "Select-Object -ExpandProperty CurrentReading",
        ):
            readings = _from_powershell(command)
            if readings:
                return _unique(readings)

    return []


def temperature_status_hint() -> str | None:
    if get_cpu_temperature_readings():
        return None
    if sys.platform.startswith("win"):
        if find_lhm_directory() or LHM_DLL.is_file():
            return (
                "CPU-temperatuur vereist administratorrechten op dit systeem. "
                "Start de app als administrator, sta LibreHardwareMonitor toe in "
                "Windows Defender, of run vendor\\LibreHardwareMonitor\\LibreHardwareMonitor.exe als admin."
            )
        return (
            "CPU-temperatuur wordt automatisch ingesteld bij eerste start "
            "(LibreHardwareMonitor)."
        )
    return "CPU-temperatuursensoren niet beschikbaar op dit platform."
