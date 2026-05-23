"""Gaming-focused helpers: active game, bottlenecks, alerts, top processes."""

from __future__ import annotations

import sys
from dataclasses import dataclass

import psutil

KNOWN_GAME_EXES = {
    "cs2.exe",
    "csgo.exe",
    "valorant.exe",
    "valorant-win64-shipping.exe",
    "fortniteclient-win64-shipping.exe",
    "r5apex.exe",
    "gta5.exe",
    "eldenring.exe",
    "rocketleague.exe",
    "overwatch.exe",
    "minecraft.exe",
    "javaw.exe",
    "league of legends.exe",
    "dota2.exe",
    "pubg.exe",
    "tslgame.exe",
    "cod.exe",
    "modernwarfare.exe",
    "helldivers2.exe",
    "bg3.exe",
    "witcher3.exe",
    "starfield.exe",
    "cyberpunk2077.exe",
    "destiny2.exe",
    "rainbowsix.exe",
    "rainbowsix_vulkan.exe",
    "ffxiv.exe",
    "ffxiv_dx11.exe",
    "wow.exe",
    "wowclassic.exe",
}

GAME_TITLE_KEYWORDS = (
    "counter-strike",
    "valorant",
    "fortnite",
    "apex legends",
    "call of duty",
    "league of legends",
    "dota 2",
    "overwatch",
    "minecraft",
    "elden ring",
    "grand theft auto",
    "rocket league",
    "helldivers",
    "baldur's gate",
    "cyberpunk",
    "destiny 2",
    "rainbow six",
    "world of warcraft",
)


@dataclass
class ForegroundApp:
    title: str
    process_name: str
    pid: int | None
    is_game: bool


@dataclass
class BottleneckInfo:
    label: str
    detail: str


def get_foreground_app() -> ForegroundApp:
    title = ""
    process_name = ""
    pid = None

    if sys.platform.startswith("win"):
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                length = user32.GetWindowTextLengthW(hwnd) + 1
                buffer = ctypes.create_unicode_buffer(length)
                user32.GetWindowTextW(hwnd, buffer, length)
                title = buffer.value or ""

                proc_id = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))
                pid = int(proc_id.value)
                if pid:
                    process_name = psutil.Process(pid).name()
        except Exception:
            pass

    is_game = is_likely_game(process_name, title)
    return ForegroundApp(
        title=title or "Onbekend venster",
        process_name=process_name or "—",
        pid=pid,
        is_game=is_game,
    )


def is_likely_game(process_name: str, window_title: str) -> bool:
    exe = (process_name or "").lower()
    if exe in KNOWN_GAME_EXES:
        return True
    title = (window_title or "").lower()
    return any(keyword in title for keyword in GAME_TITLE_KEYWORDS)


def analyze_bottleneck(cpu_percent: float, gpu_percent: float, ram_percent: float) -> BottleneckInfo:
    if gpu_percent >= 92 and cpu_percent < 70:
        return BottleneckInfo("GPU-bound", "GPU zit op het plafond — lagere grafische instellingen helpen.")
    if cpu_percent >= 88 and gpu_percent < 72:
        return BottleneckInfo("CPU-bound", "CPU is de bottleneck — sluit achtergrondapps of verlaag CPU-last.")
    if ram_percent >= 90:
        return BottleneckInfo("RAM-bound", "Weinig geheugen — sluit browsers of andere zware apps.")
    if gpu_percent >= 85 and cpu_percent >= 85:
        return BottleneckInfo("CPU + GPU", "Beide componenten zwaar belast — thermals/limits checken.")
    if gpu_percent < 50 and cpu_percent < 50 and ram_percent < 70:
        return BottleneckInfo("Ruimte over", "Systeem niet maximaal belast — ruimte voor hogere instellingen.")
    return BottleneckInfo("Gebalanceerd", "Geen duidelijke bottleneck op dit moment.")


def update_session_peaks(
    peaks: dict[str, float],
    cpu_percent: float,
    gpu_percent: float,
    ram_percent: float,
    cpu_temp: float | None,
    gpu_temp: float | None,
) -> dict[str, float]:
    peaks["cpu"] = max(peaks.get("cpu", 0), cpu_percent)
    peaks["gpu"] = max(peaks.get("gpu", 0), gpu_percent)
    peaks["ram"] = max(peaks.get("ram", 0), ram_percent)
    if cpu_temp is not None:
        peaks["cpu_temp"] = max(peaks.get("cpu_temp", 0), cpu_temp)
    if gpu_temp is not None:
        peaks["gpu_temp"] = max(peaks.get("gpu_temp", 0), gpu_temp)
    return peaks


def collect_performance_alerts(
    cpu_percent: float,
    gpu_percent: float,
    ram_percent: float,
    cpu_temp: float | None,
    gpu_temp: float | None,
    ping_ms: float | None,
) -> list[str]:
    alerts: list[str] = []
    if cpu_temp is not None and cpu_temp >= 90:
        alerts.append(f"Kritieke CPU-temp ({cpu_temp:.0f} °C)")
    elif cpu_temp is not None and cpu_temp >= 80:
        alerts.append(f"Hoge CPU-temp ({cpu_temp:.0f} °C)")
    if gpu_temp is not None and gpu_temp >= 90:
        alerts.append(f"Kritieke GPU-temp ({gpu_temp:.0f} °C)")
    elif gpu_temp is not None and gpu_temp >= 83:
        alerts.append(f"Hoge GPU-temp ({gpu_temp:.0f} °C)")
    if ram_percent >= 95:
        alerts.append(f"RAM bijna vol ({ram_percent:.0f}%)")
    elif ram_percent >= 85:
        alerts.append(f"Hoge RAM ({ram_percent:.0f}%)")
    if cpu_percent >= 98:
        alerts.append("CPU op 100%")
    if gpu_percent >= 98:
        alerts.append("GPU op 100%")
    if ping_ms is not None and ping_ms >= 120:
        alerts.append(f"Hoge ping ({ping_ms:.0f} ms)")
    elif ping_ms is not None and ping_ms >= 80:
        alerts.append(f"Verhoogde ping ({ping_ms:.0f} ms)")
    return alerts


def get_top_processes(limit: int = 5) -> list[tuple[str, float]]:
    psutil.cpu_percent(interval=0)
    ranked: list[tuple[str, float]] = []
    for proc in psutil.process_iter(["name"]):
        try:
            cpu = proc.cpu_percent(interval=0)
            if cpu > 0:
                ranked.append((proc.info.get("name") or "?", float(cpu)))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[:limit]
