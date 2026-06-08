from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame

def build_disk_details(monitor):
    widget = QWidget()
    layout = QVBoxLayout()
    layout.setSpacing(10)
    disk_card = QFrame()
    disk_card.setStyleSheet(f"QFrame {{ background-color: {monitor.ui_panel}; border-radius: 10px; padding: 12px; }}")
    d_layout = QGridLayout(disk_card)
    d_layout.setSpacing(10)
    d_layout.addWidget(QLabel("Disk Usage:"), 0, 0)
    monitor.disk_usage_detail_label = QLabel()
    d_layout.addWidget(monitor.disk_usage_detail_label, 0, 1)

    d_layout.addWidget(QLabel("Total:"), 1, 0)
    monitor.disk_total_label = QLabel()
    d_layout.addWidget(monitor.disk_total_label, 1, 1)

    d_layout.addWidget(QLabel("Used:"), 2, 0)
    monitor.disk_used_label = QLabel()
    d_layout.addWidget(monitor.disk_used_label, 2, 1)

    d_layout.addWidget(QLabel("Free:"), 3, 0)
    monitor.disk_free_label = QLabel()
    d_layout.addWidget(monitor.disk_free_label, 3, 1)

    d_layout.addWidget(QLabel("Disk Busy:"), 4, 0)
    monitor.disk_busy_detail_label = QLabel()
    d_layout.addWidget(monitor.disk_busy_detail_label, 4, 1)

    d_layout.addWidget(QLabel("Throughput:"), 5, 0)
    monitor.disk_io_detail_label = QLabel()
    d_layout.addWidget(monitor.disk_io_detail_label, 5, 1)

    layout.addWidget(disk_card)
    widget.setLayout(layout)
    return widget
