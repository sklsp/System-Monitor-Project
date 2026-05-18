import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Ensure project root is on sys.path so 'ui' and 'monitoring' packages import correctly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ui.dashboard import SystemMonitor

def run_for_seconds(seconds=3):
    app = QApplication(sys.argv)
    monitor = SystemMonitor()
    monitor.show()
    QTimer.singleShot(seconds * 1000, app.quit)
    try:
        app.exec_()
    except Exception as e:
        print('ERROR-RUN:', e)

if __name__ == '__main__':
    run_for_seconds(3)
