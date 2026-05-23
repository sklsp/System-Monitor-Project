from PyQt5.QtWidgets import QApplication

from ui.dashboard import SystemMonitor


def main():
    import sys
    app = QApplication(sys.argv)
    monitor = SystemMonitor()
    monitor.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
