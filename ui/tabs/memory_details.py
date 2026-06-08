from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame

def build_memory_details(monitor):
    widget = QWidget()
    layout = QVBoxLayout()
    layout.setSpacing(10)
    ram_card = QFrame()
    ram_card.setStyleSheet(f"QFrame {{ background-color: {monitor.ui_panel}; border-radius: 10px; padding: 12px; }}")
    r_layout = QGridLayout(ram_card)
    r_layout.setSpacing(10)
    r_layout.addWidget(QLabel("Memory Usage:"), 0, 0)
    monitor.memory_percent_detail_label = QLabel()
    r_layout.addWidget(monitor.memory_percent_detail_label, 0, 1)

    r_layout.addWidget(QLabel("Total:"), 1, 0)
    monitor.memory_total_label = QLabel()
    r_layout.addWidget(monitor.memory_total_label, 1, 1)

    r_layout.addWidget(QLabel("Used:"), 2, 0)
    monitor.memory_used_label = QLabel()
    r_layout.addWidget(monitor.memory_used_label, 2, 1)

    r_layout.addWidget(QLabel("Available:"), 3, 0)
    monitor.memory_available_label = QLabel()
    r_layout.addWidget(monitor.memory_available_label, 3, 1)

    r_layout.addWidget(QLabel("Swap Total:"), 4, 0)
    monitor.swap_total_label = QLabel()
    r_layout.addWidget(monitor.swap_total_label, 4, 1)

    r_layout.addWidget(QLabel("Swap Used:"), 5, 0)
    monitor.swap_used_label = QLabel()
    r_layout.addWidget(monitor.swap_used_label, 5, 1)

    layout.addWidget(ram_card)
    widget.setLayout(layout)
    return widget
