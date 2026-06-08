from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame

def build_network_details(monitor):
    widget = QWidget()
    layout = QVBoxLayout()
    layout.setSpacing(10)
    net_card = QFrame()
    net_card.setStyleSheet(f"QFrame {{ background-color: {monitor.ui_panel}; border-radius: 10px; padding: 12px; }}")
    n_layout = QGridLayout(net_card)
    n_layout.setSpacing(10)
    n_layout.addWidget(QLabel("Interface:"), 0, 0)
    monitor.network_interface_label = QLabel()
    n_layout.addWidget(monitor.network_interface_label, 0, 1)

    n_layout.addWidget(QLabel("Link Speed:"), 1, 0)
    monitor.network_speed_label = QLabel()
    n_layout.addWidget(monitor.network_speed_label, 1, 1)

    n_layout.addWidget(QLabel("Upload:"), 2, 0)
    monitor.network_upload_label = QLabel()
    n_layout.addWidget(monitor.network_upload_label, 2, 1)

    n_layout.addWidget(QLabel("Download:"), 3, 0)
    monitor.network_download_label = QLabel()
    n_layout.addWidget(monitor.network_download_label, 3, 1)

    n_layout.addWidget(QLabel("Usage:"), 4, 0)
    monitor.network_usage_label = QLabel()
    n_layout.addWidget(monitor.network_usage_label, 4, 1)

    layout.addWidget(net_card)
    widget.setLayout(layout)
    return widget
