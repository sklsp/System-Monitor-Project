"""Background ping / latency monitoring."""

from __future__ import annotations

import re
import subprocess
import sys
import threading
import time

DEFAULT_HOSTS = (
    ("Google", "8.8.8.8"),
    ("Cloudflare", "1.1.1.1"),
)


def _parse_ping_ms(output: str) -> float | None:
    match = re.search(r"[=<]\s*(\d+)\s*ms", output, re.IGNORECASE)
    if match:
        return float(match.group(1))
    if re.search(r"<1\s*ms", output, re.IGNORECASE):
        return 0.5
    return None


def ping_host(host: str, timeout_ms: int = 2000) -> float | None:
    try:
        if sys.platform.startswith("win"):
            proc = subprocess.run(
                ["ping", "-n", "1", "-w", str(timeout_ms), host],
                capture_output=True,
                text=True,
                timeout=(timeout_ms / 1000) + 2,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        else:
            proc = subprocess.run(
                ["ping", "-c", "1", "-W", str(max(1, timeout_ms // 1000)), host],
                capture_output=True,
                text=True,
                timeout=(timeout_ms / 1000) + 2,
            )
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    return _parse_ping_ms(proc.stdout or "")


class PingMonitor:
    def __init__(self, hosts: tuple[tuple[str, str], ...] = DEFAULT_HOSTS, interval: float = 5.0):
        self.hosts = hosts
        self.interval = interval
        self._results: dict[str, float | None] = {label: None for label, _ in hosts}
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _worker(self) -> None:
        while not self._stop.is_set():
            for label, host in self.hosts:
                latency = ping_host(host)
                with self._lock:
                    self._results[label] = latency
            self._stop.wait(self.interval)

    def get_results(self) -> dict[str, float | None]:
        with self._lock:
            return dict(self._results)

    def average_ms(self) -> float | None:
        values = [v for v in self.get_results().values() if v is not None]
        if not values:
            return None
        return round(sum(values) / len(values), 1)
