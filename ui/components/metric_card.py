from PyQt5.QtWidgets import QLabel, QVBoxLayout
from ui.dashboard.layout import make_card


def create_metric_card(monitor, title: str, value_text: str = "N/A"):
    card, layout = make_card(title, monitor)
    value = QLabel(value_text)
    value.setStyleSheet(f"color: {monitor.ui_fg}; font-weight: 700; font-size: 16px;")
    layout.addWidget(value)
    return card, value
