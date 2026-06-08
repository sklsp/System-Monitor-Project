from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

def build_details(self):
    widget = QWidget()
    layout = QVBoxLayout()
    layout.setSpacing(10)

    details_tabs = QTabWidget()
    self.details_tabs = details_tabs
    details_tabs.setStyleSheet("""
        QTabWidget::pane { border: 1px solid #555; }
        QTabBar::tab { background-color: #3b3b3b; color: #fff; padding: 8px 20px; }
        QTabBar::tab:selected { background-color: #555; }
    """)
    details_tabs.addTab(self.create_cpu_details_tab(), "CPU")
    details_tabs.addTab(self.create_gpu_details_tab(), "GPU")
    details_tabs.addTab(self.create_ram_details_tab(), "RAM")
    details_tabs.addTab(self.create_disk_details_tab(), "Disk")
    details_tabs.addTab(self.create_ethernet_details_tab(), "Ethernet")

    layout.addWidget(details_tabs)
    widget.setLayout(layout)
    return widget
