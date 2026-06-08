from PyQt5.QtCore import QTimer


def start_timers(monitor, interval_ms: int = 2500):
    """Start the recurring UI update timer for the monitor.

    This keeps the timer lifecycle owned by a dedicated controller module so
    the main window remains focused on composition.
    """
    if hasattr(monitor, 'update_timer') and monitor.update_timer is not None:
        return monitor.update_timer

    monitor.update_timer = QTimer()
    monitor.update_timer.timeout.connect(monitor.update_system_info)
    monitor.update_timer.start(interval_ms)
    return monitor.update_timer
