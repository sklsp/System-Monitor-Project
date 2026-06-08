from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame, QHBoxLayout
from PyQt5.QtGui import QFont
from ui.graphs import GraphWidget

def build_cpu_details(monitor):
    widget = QWidget()
    main_layout = QVBoxLayout()
    main_layout.setSpacing(12)

    cpu_card = QFrame()
    cpu_card.setStyleSheet(f"QFrame {{ background-color: {monitor.ui_panel}; border-radius: 10px; padding: 12px; }}")
    cpu_layout = QVBoxLayout(cpu_card)

    info_layout = QGridLayout()
    info_layout.setSpacing(10)
    info_layout.addWidget(QLabel("CPU Load:"), 0, 0)
    monitor.cpu_load_detail_label = QLabel()
    info_layout.addWidget(monitor.cpu_load_detail_label, 0, 1)

    info_layout.addWidget(QLabel("Physical Cores:"), 1, 0)
    monitor.cpu_physical_label = QLabel()
    info_layout.addWidget(monitor.cpu_physical_label, 1, 1)

    info_layout.addWidget(QLabel("Logical Cores:"), 2, 0)
    monitor.cpu_logical_label = QLabel()
    info_layout.addWidget(monitor.cpu_logical_label, 2, 1)

    info_layout.addWidget(QLabel("Current Frequency:"), 3, 0)
    monitor.cpu_current_freq_label = QLabel()
    info_layout.addWidget(monitor.cpu_current_freq_label, 3, 1)

    info_layout.addWidget(QLabel("Boost Frequency:"), 4, 0)
    monitor.cpu_boost_freq_label = QLabel()
    info_layout.addWidget(monitor.cpu_boost_freq_label, 4, 1)

    info_layout.addWidget(QLabel("Throttling:"), 5, 0)
    monitor.cpu_throttling_label = QLabel()
    info_layout.addWidget(monitor.cpu_throttling_label, 5, 1)

    info_layout.addWidget(QLabel("CPU Temp Max:"), 6, 0)
    monitor.cpu_temp_max_label = QLabel()
    info_layout.addWidget(monitor.cpu_temp_max_label, 6, 1)

    info_layout.addWidget(QLabel("CPU Temp Avg:"), 7, 0)
    monitor.cpu_temp_avg_label = QLabel()
    info_layout.addWidget(monitor.cpu_temp_avg_label, 7, 1)

    monitor.cpu_temp_hint_label = QLabel()
    monitor.cpu_temp_hint_label.setWordWrap(True)
    monitor.cpu_temp_hint_label.setStyleSheet(f"color: {monitor.ui_warning}; font-size: 11px;")
    info_layout.addWidget(monitor.cpu_temp_hint_label, 8, 0, 1, 2)

    info_layout.addWidget(QLabel("Power Usage:"), 9, 0)
    monitor.cpu_power_watts_label = QLabel()
    info_layout.addWidget(monitor.cpu_power_watts_label, 9, 1)

    info_layout.addWidget(QLabel("Package Power:"), 10, 0)
    monitor.cpu_power_package_label = QLabel()
    info_layout.addWidget(monitor.cpu_power_package_label, 10, 1)

    cpu_layout.addLayout(info_layout)
    main_layout.addWidget(cpu_card)

    main_layout.addWidget(QLabel("Per-Core Usage:"))
    monitor.cpu_core_labels = []
    monitor.cpu_core_graphs = []
    core_count = len(monitor.cpu_core_histories)
    core_colors = ["#4CAF50", "#66BB6A", "#81C784", "#43A047", "#2E7D32", "#1B5E20"]
    for i in range(core_count):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 2, 0, 2)
        row_layout.setSpacing(8)
        core_label = QLabel(f"Core {i + 1}: 0%")
        core_label.setFont(QFont("Arial", 11))
        core_label.setMinimumWidth(95)
        monitor.cpu_core_labels.append(core_label)
        core_graph = GraphWidget(core_colors[i % len(core_colors)], fixed_max=100)
        core_graph.setMinimumHeight(52)
        core_graph.setMaximumHeight(60)
        monitor.cpu_core_graphs.append(core_graph)
        row_layout.addWidget(core_label)
        row_layout.addWidget(core_graph, 1)
        main_layout.addWidget(row_widget)

    main_layout.addWidget(QLabel("CPU Temperature Graph:"))
    monitor.cpu_temp_graph = GraphWidget()
    monitor.cpu_temp_graph.setMinimumHeight(160)
    main_layout.addWidget(monitor.cpu_temp_graph)

    widget.setLayout(main_layout)
    return widget
