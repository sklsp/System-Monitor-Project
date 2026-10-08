"""The real dashboard, offscreen: it boots, runs its timers for 3 seconds and builds every overview card."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from PyQt5.QtCore import QTimer  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402

from ui.dashboard.main import SystemMonitor  # noqa: E402

CARDS = ["cpu_label", "gpu_label", "memory_label", "disk_label", "eth_label", "process_label"]


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_dashboard_runs_three_seconds_without_errors(app):
    errors = []
    previous = sys.excepthook
    sys.excepthook = lambda kind, value, tb: errors.append(value)  # PyQt reports slot exceptions here
    try:
        window = SystemMonitor()
        window.show()
        QTimer.singleShot(3000, app.quit)
        app.exec_()
        window.close()
    finally:
        sys.excepthook = previous
    assert errors == []


def test_overview_builds_every_card(app):
    window = SystemMonitor()
    window.resize(1200, 780)
    window.show()
    app.processEvents()
    for name in CARDS:
        label = getattr(window, name)
        assert label.parent() is not None and label.parent().width() > 0, name
    window.close()
