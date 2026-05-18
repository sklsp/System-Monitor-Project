import psutil
import subprocess
import sys

def get_active_network_interface():
    try:
        stats = psutil.net_if_stats()
        for name, s in stats.items():
            if s.isup and not name.lower().startswith("lo"):
                return name
    except Exception:
        pass
    return None


def get_interface_speed(name):
    try:
        stats = psutil.net_if_stats()
        if name in stats and stats[name].speed:
            return stats[name].speed
    except Exception:
        pass
    if sys.platform.startswith("win") and name:
        try:
            proc = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"Get-NetAdapter -Name '{name}' | Select-Object -ExpandProperty LinkSpeed",
                ],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                text = proc.stdout.strip()
                parts = text.split()
                if len(parts) >= 2:
                    speed_value = float(parts[0])
                    speed_unit = parts[1].lower()
                    if speed_unit.startswith("gb"):
                        return speed_value * 1000
                    if speed_unit.startswith("mb"):
                        return speed_value
        except Exception:
            pass
    return None


def get_net_io_counters(pernic=True):
    return psutil.net_io_counters(pernic=pernic)
