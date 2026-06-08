from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt


def create_metric_button(monitor, text, details_tab_name):
    button = QPushButton(text)
    button.setCursor(Qt.PointingHandCursor)
    button.setStyleSheet(
        "QPushButton { border: none; color: #ffffff; text-align: left; font-weight: bold; font-size: 14px; }"
        "QPushButton:hover { color: #9cf; }"
    )
    button.setFlat(True)
    button.clicked.connect(lambda: navigate_to_details_tab(monitor, details_tab_name))
    return button


def navigate_to_details_tab(monitor, tab_name):
    if hasattr(monitor, 'main_tabs'):
        # Assume details tab index is 1 (Overview=0, Details=1) as before
        try:
            monitor.main_tabs.setCurrentIndex(1)
        except Exception:
            pass
    if hasattr(monitor, 'details_tabs'):
        for index in range(monitor.details_tabs.count()):
            try:
                if monitor.details_tabs.tabText(index) == tab_name:
                    monitor.details_tabs.setCurrentIndex(index)
                    break
            except Exception:
                continue
