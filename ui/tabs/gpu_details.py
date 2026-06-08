from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame

def build_gpu_details(monitor):
    widget = QWidget()
    layout = QVBoxLayout()
    layout.setSpacing(10)

    gpu_card = QFrame()
    gpu_card.setStyleSheet(f"QFrame {{ background-color: {monitor.ui_panel}; border-radius: 10px; padding: 12px; }}")
    g_layout = QGridLayout(gpu_card)
    g_layout.setSpacing(10)
    g_layout.addWidget(QLabel("GPU Name:"), 0, 0)
    monitor.gpu_name_label = QLabel()
    g_layout.addWidget(monitor.gpu_name_label, 0, 1)

    g_layout.addWidget(QLabel("Driver Version:"), 1, 0)
    monitor.gpu_driver_label = QLabel()
    g_layout.addWidget(monitor.gpu_driver_label, 1, 1)

    g_layout.addWidget(QLabel("GPU Load:"), 2, 0)
    monitor.gpu_load_label = QLabel()
    g_layout.addWidget(monitor.gpu_load_label, 2, 1)

    g_layout.addWidget(QLabel("Core Clock (MHz):"), 3, 0)
    monitor.gpu_core_clock_label = QLabel()
    g_layout.addWidget(monitor.gpu_core_clock_label, 3, 1)

    g_layout.addWidget(QLabel("Memory Clock (MHz):"), 4, 0)
    monitor.gpu_mem_clock_label = QLabel()
    g_layout.addWidget(monitor.gpu_mem_clock_label, 4, 1)

    g_layout.addWidget(QLabel("Temperature:"), 5, 0)
    monitor.gpu_temp_label = QLabel()
    g_layout.addWidget(monitor.gpu_temp_label, 5, 1)

    g_layout.addWidget(QLabel("Fan Speed:"), 6, 0)
    monitor.gpu_fan_label = QLabel()
    g_layout.addWidget(monitor.gpu_fan_label, 6, 1)

    g_layout.addWidget(QLabel("Throttling:"), 7, 0)
    monitor.gpu_throttle_label = QLabel()
    g_layout.addWidget(monitor.gpu_throttle_label, 7, 1)

    g_layout.addWidget(QLabel("VRAM Usage:"), 8, 0)
    monitor.gpu_mem_label = QLabel()
    g_layout.addWidget(monitor.gpu_mem_label, 8, 1)

    g_layout.addWidget(QLabel("VRAM Percent:"), 9, 0)
    monitor.gpu_mem_percent_label = QLabel()
    g_layout.addWidget(monitor.gpu_mem_percent_label, 9, 1)

    g_layout.addWidget(QLabel("Power Draw (W):"), 10, 0)
    monitor.gpu_power_draw_label = QLabel()
    g_layout.addWidget(monitor.gpu_power_draw_label, 10, 1)

    g_layout.addWidget(QLabel("Power Limit / Headroom:"), 11, 0)
    monitor.gpu_power_limit_label = QLabel()
    g_layout.addWidget(monitor.gpu_power_limit_label, 11, 1)

    layout.addWidget(gpu_card)
    widget.setLayout(layout)
    return widget
