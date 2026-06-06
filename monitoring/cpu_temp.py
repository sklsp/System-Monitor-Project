"""CPU temperature collection (LibreHardwareMonitor removed)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import psutil

CPU_SENSOR_KEYS = ("cpu", "core", "package", "tctl", "tdie", "ccd", "socket", "dies")
GPU_SENSOR_KEYS = ("gpu", "graphics", "geforce", "radeon", "video", "vram")

_elevated_dll_attempted = False


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


def _is_process_elevated() -> bool:
    if not sys.platform.startswith("win"):
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _run_powershell(command: str, timeout: int = 25) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        return None


def _run_powershell_encoded(script: str, timeout: int = 25) -> subprocess.CompletedProcess | None:
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    try:
        return subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-EncodedCommand",
                encoded,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        return None


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


def _from_wmi_acpi() -> list[float]:
    try:
        import win32com.client
    except ImportError:
        return []

    readings: list[float] = []
    try:
        wmi_obj = win32com.client.GetObject(r"winmgmts:\\.\root\wmi")
        sensors = wmi_obj.ExecQuery("SELECT * FROM MSAcpi_ThermalZoneTemperature")
        for sensor in sensors:
            temp_c = sensor.CurrentTemperature / 10.0 - 273.15
            if _valid_celsius(temp_c):
                readings.append(round(temp_c, 1))
    except Exception:
        return []
    return readings


def _from_external_monitor_wmi() -> list[float]:
    """Use WMI only if another tool already exposed sensors (no app is started)."""
    try:
        import win32com.client
    except ImportError:
        return []

    readings: list[float] = []
    # Only check OpenHardwareMonitor namespace; LibreHardwareMonitor has been removed.
    for namespace in (r"root\\OpenHardwareMonitor",):
        try:
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
            continue
    return readings


def _from_wmi_probes() -> list[float]:
    try:
        import win32com.client
    except ImportError:
        return []

    readings: list[float] = []
    try:
        wmi_obj = win32com.client.GetObject(r"winmgmts:\\.\root\cimv2")
        probes = wmi_obj.ExecQuery("SELECT CurrentReading FROM Win32_TemperatureProbe")
        for probe in probes:
            if probe.CurrentReading is None:
                continue
            temp_c = _normalize_tenths_kelvin(float(probe.CurrentReading))
            if _valid_celsius(temp_c):
                readings.append(round(temp_c, 1))
    except Exception:
        return []
    return readings


def _from_powershell_cim(command: str, timeout: int = 8) -> list[float]:
    proc = _run_powershell(command, timeout=timeout)
    if proc is None or proc.returncode != 0:
        return []
    return _parse_text_values(proc.stdout)


def _from_windows_native() -> list[float]:
    """Built-in Windows sources (no third-party apps)."""
    readings = _from_wmi_acpi()
    if readings:
        return readings

    readings = _from_wmi_probes()
    if readings:
        return readings

    ps_commands = (
        "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature "
        "-ErrorAction SilentlyContinue | Select-Object -ExpandProperty CurrentTemperature",
        "Get-CimInstance -ClassName Win32_TemperatureProbe -ErrorAction SilentlyContinue "
        "| Select-Object -ExpandProperty CurrentReading",
        "Get-CimInstance -ClassName Win32_PerfFormattedData_Counters_ThermalZoneInformation "
        "-ErrorAction SilentlyContinue | Select-Object -ExpandProperty Temperature",
    )
    for command in ps_commands:
        readings = _from_powershell_cim(command)
        if readings:
            return readings
    return []


def _hardware_lib_dir() -> Path | None:
    if HW_DLL.is_file():
        return HW_LIB_DIR
    return None


def _read_temp_output_file() -> list[float]:
    if not TEMP_OUTPUT.is_file():
        return []
    try:
        text = TEMP_OUTPUT.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    return _parse_text_values(text)


def _from_bundled_hardware_lib() -> list[float]:
    """Run sensor DLL in the current process privilege level."""
    lib_dir = _hardware_lib_dir()
    if lib_dir is None or not HW_PS1.is_file():
        return []

    proc = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(HW_PS1),
            "-LibDirectory",
            str(lib_dir),
        ],
        capture_output=True,
        text=True,
        timeout=20,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if proc.returncode != 0:
        return []
    return _parse_text_values(proc.stdout)


def _from_bundled_hardware_lib_elevated() -> list[float]:
    """
    Elevated child processes cannot pipe stdout back to a non-admin parent.
    Write readings to a temp file and read them here.
    """
    lib_dir = _hardware_lib_dir()
    if lib_dir is None or not HW_PS1.is_file():
        return []

    try:
        TEMP_OUTPUT.unlink(missing_ok=True)
    except OSError:
        pass

    ps1 = str(HW_PS1).replace("'", "''")
    lib = str(lib_dir).replace("'", "''")
    out = str(TEMP_OUTPUT).replace("'", "''")

    inner_script = (
        f"& '{ps1}' -LibDirectory '{lib}' | "
        f"ForEach-Object {{ $_.ToString() }} | "
        f"Set-Content -LiteralPath '{out}' -Encoding UTF8"
    )
    inner_b64 = base64.b64encode(inner_script.encode("utf-16-le")).decode("ascii")

    wrapper_script = (
        f"$p = Start-Process powershell -ArgumentList @("
        f"'-NoProfile','-ExecutionPolicy','Bypass','-EncodedCommand','{inner_b64}'"
        f") -Verb RunAs -Wait -PassThru -WindowStyle Hidden; "
        f"if ($p.ExitCode -ne 0) {{ exit $p.ExitCode }}"
    )

    proc = _run_powershell(wrapper_script, timeout=35)
    if proc is None or proc.returncode != 0:
        return _read_temp_output_file()

    readings = _read_temp_output_file()
    if readings:
        return readings
    return _parse_text_values(proc.stdout)


def get_cpu_temperature_readings() -> list[float]:
    global _elevated_dll_attempted

    readings = _from_psutil()
    if readings:
        return _unique(readings)

    if sys.platform.startswith("win"):
        readings = _from_windows_native()
        if readings:
            return _unique(readings)

        readings = _from_external_monitor_wmi()
        if readings:
            return _unique(readings)
    return []


def temperature_status_hint(has_readings: bool = False) -> str | None:
    if has_readings:
        return None
    if sys.platform.startswith("win"):
        return (
            "CPU-temperatuur niet beschikbaar op dit systeem via standaard Windows-sensoren."
        )
    return "CPU-temperatuursensoren niet beschikbaar op dit platform."
