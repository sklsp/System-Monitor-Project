from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel


def make_card(title: str, monitor, padding: int = 8):
    frame = QFrame()
    frame.setObjectName('card')
    frame.setStyleSheet(f"QFrame#card {{ background-color: {monitor.ui_panel}; border-radius: 10px; padding: {padding}px; }}")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(8, 6, 8, 6)
    layout.setSpacing(6)
    if title:
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-weight: 700; color: {monitor.ui_muted}; font-size: 12px;")
        layout.addWidget(title_label)
    return frame, layout
