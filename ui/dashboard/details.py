from PyQt5.QtWidgets import QWidget, QVBoxLayout

from ui.tabs.cpu_details import build_cpu_details
from ui.tabs.gpu_details import build_gpu_details
from ui.tabs.memory_details import build_memory_details
from ui.tabs.disk_details import build_disk_details
from ui.tabs.network_details import build_network_details


def build_details(self):
    widget = QWidget()
    layout = QVBoxLayout()
    layout.setSpacing(10)

    from PyQt5.QtWidgets import QTabWidget

    details_tabs = QTabWidget()
    self.details_tabs = details_tabs
    details_tabs.setStyleSheet("""
        QTabWidget::pane { border: 1px solid #555; }
        QTabBar::tab { background-color: #3b3b3b; color: #fff; padding: 8px 20px; }
        QTabBar::tab:selected { background-color: #555; }
    """)
    details_tabs.addTab(build_cpu_details(self), "CPU")
    details_tabs.addTab(build_gpu_details(self), "GPU")
    details_tabs.addTab(build_memory_details(self), "RAM")
    details_tabs.addTab(build_disk_details(self), "Disk")
    details_tabs.addTab(build_network_details(self), "Ethernet")

    layout.addWidget(details_tabs)
    widget.setLayout(layout)
    return widget
