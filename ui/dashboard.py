import sys
import subprocess
import csv
import io
import threading
import psutil
from pathlib import Path

# Ensure the project root is on sys.path so local packages can be imported
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from monitoring.net import get_active_network_interface, get_interface_speed
    from monitoring.disk import get_disk_busy_percent
    from monitoring.cpu_temp import get_cpu_temperature_readings, temperature_status_hint
    from monitoring.ping import PingMonitor
    from monitoring.gaming import (
        get_foreground_app,
        analyze_bottleneck,
        update_session_peaks,
        collect_performance_alerts,
        get_top_processes,
    )
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from monitoring.net import get_active_network_interface, get_interface_speed
    from monitoring.disk import get_disk_busy_percent
    from monitoring.cpu_temp import get_cpu_temperature_readings, temperature_status_hint
    from monitoring.ping import PingMonitor
    from monitoring.gaming import (
        get_foreground_app,
        analyze_bottleneck,
        update_session_peaks,
        collect_performance_alerts,
        get_top_processes,
    )

try:
    import GPUtil
except Exception:
    # If GPUtil can't be imported for any reason (missing dependency like
    # distutils), treat it as unavailable and fall back to nvidia-smi.
    GPUtil = None

try:
    from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
    QT_CHARTS_AVAILABLE = True
except ImportError:
    QT_CHARTS_AVAILABLE = False

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QProgressBar, QTabWidget, QPushButton, QScrollArea
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPainter, QColor, QPen

from ui.graphs import GraphWidget
from ui.gaming_tab import GamingTab


class SystemMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Monitor — Gaming")
        self.setGeometry(100, 100, 1200, 780)

        # Theme and palette
        self.ui_accent = "#7DD3FC"  # subtle cyan accent
        self.ui_warning = "#FFB86B"
        self.ui_bg = "#141416"
        self.ui_panel = "#1f1f23"
        self.ui_muted = "#9AA3B2"
        self.ui_fg = "#E6EEF3"
        self.setStyleSheet(f"background-color: {self.ui_bg}; color: {self.ui_fg}; font-family: 'Segoe UI', Arial;")

        # Initialize data storage for charts
        self.cpu_history = []
        self.memory_history = []
        self.gpu_history = []
        self.disk_history = []
        self.eth_history = []
        core_count = psutil.cpu_count(logical=True) or 1
        self.cpu_core_histories = [[] for _ in range(core_count)]
        self.cpu_temp_history = []
        self.max_history = 30
        self.prev_disk_io = psutil.disk_io_counters()
        self.prev_net_io = psutil.net_io_counters(pernic=True)
        self.network_interface = get_active_network_interface()
        self.last_cpu_temp_readings = []
        self.last_cpu_temp_hint = None
        self.last_gpu_data = None
        self.cpu_temp_thread = None
        self.slow_update_counter = 0
        self.slow_update_frequency = 10
        self.session_peaks = {"cpu": 0, "gpu": 0, "ram": 0, "cpu_temp": 0, "gpu_temp": 0}
        self.last_top_processes = []
        self.ping_monitor = PingMonitor()
        psutil.cpu_percent(interval=None)

        self.init_ui()
        self.ping_monitor.start()
        self.start_cpu_temp_background_refresh()

        # Timer for updating info
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_system_info)
        self.timer.start(2500)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)

        title = QLabel("System Monitor")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_font.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet(f"color: {self.ui_fg}; padding: 8px 6px; margin-bottom: 6px;")

        header_row = QHBoxLayout()
        header_row.addWidget(title)
        header_row.addStretch()
        main_layout.addLayout(header_row)

        tabs = QTabWidget()
        self.main_tabs = tabs
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 0px; background: transparent; }}
            QTabBar::tab {{ background-color: {self.ui_panel}; color: {self.ui_muted}; padding: 8px 18px; margin: 4px; border-radius: 8px; }}
            QTabBar::tab:selected {{ background-color: {self.ui_panel}; color: {self.ui_fg}; border: 1px solid rgba(125,211,252,0.12); }}
        """)

        self.gaming_tab = GamingTab(on_top_toggle=self.set_always_on_top)
        tabs.addTab(self.gaming_tab, "Gaming")

        overview_widget = self.create_overview_tab()
        tabs.addTab(overview_widget, "Overview")

        details_widget = self.create_details_tab()
        tabs.addTab(details_widget, "Details")

        main_layout.addWidget(tabs)
        scroll_area.setWidget(content_widget)

        outer_layout = QVBoxLayout(central_widget)
        outer_layout.addWidget(scroll_area)

    def create_chart(self, title, color, fixed_max=None, compact=False):
        from PyQt5.QtWidgets import QFrame
        from ui.graphs import MiniSparklineWidget

        container = QFrame()
        container.setObjectName('card')
        container.setStyleSheet(f"QFrame#card {{ background-color: {self.ui_panel}; border-radius: 10px; padding: 8px; }}")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-weight: 700; color: {self.ui_muted}; font-size: 12px;")
        layout.addWidget(title_label)

        if compact:
            # compact mode: small sparkline widget for overview cards
            spark = MiniSparklineWidget(color)
            spark.setMinimumHeight(36)
            layout.addWidget(spark)
            # keep a placeholder GraphWidget return value None for compatibility
            return container, spark, None
        else:
            graph_widget = GraphWidget(color, fixed_max=fixed_max)
            graph_widget.setMinimumHeight(140)
            layout.addWidget(graph_widget)
            return container, graph_widget, None

    def update_series(self, chart_or_series, history):
        if chart_or_series is None:
            return
        if isinstance(chart_or_series, GraphWidget):
            chart_or_series.set_history(history)
            return
        try:
            series = chart_or_series
            series.clear()
            for i, value in enumerate(history):
                series.append(i, value)
            try:
                chart = series.chart()
                if chart is not None:
                    chart.update()
            except Exception:
                pass
        except Exception:
            return

    def start_cpu_temp_background_refresh(self):
        if self.cpu_temp_thread is not None and self.cpu_temp_thread.is_alive():
            return

        def worker():
            readings = get_cpu_temperature_readings()
            self.last_cpu_temp_readings = readings
            self.last_cpu_temp_hint = temperature_status_hint(bool(readings))

        self.cpu_temp_thread = threading.Thread(target=worker, daemon=True)
        self.cpu_temp_thread.start()

    def set_always_on_top(self, enabled: bool) -> None:
        flags = self.windowFlags()
        if enabled:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
        self.show()

    def create_metric_button(self, text, details_tab_name):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(
            "QPushButton { border: none; color: #ffffff; text-align: left; font-weight: bold; font-size: 14px; }"
            "QPushButton:hover { color: #9cf; }"
        )
        button.setFlat(True)
        button.clicked.connect(lambda: self.navigate_to_details_tab(details_tab_name))
        return button

    def navigate_to_details_tab(self, tab_name):
        if hasattr(self, 'main_tabs'):
            self.main_tabs.setCurrentIndex(1)
        if hasattr(self, 'details_tabs'):
            for index in range(self.details_tabs.count()):
                if self.details_tabs.tabText(index) == tab_name:
                    self.details_tabs.setCurrentIndex(index)
                    break

    def create_overview_tab(self):
        from PyQt5.QtWidgets import QFrame

        widget = QWidget()
        layout = QGridLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(6, 6, 6, 6)

        # Overview card grid: show compact cards with metric, value and mini graph
        cards = []

        # CPU
        from ui.graphs import MiniSparklineWidget

        self.cpu_label = QLabel("0%")
        self.cpu_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.cpu_trend = QLabel("")
        self.cpu_trend.setStyleSheet(f"color: {self.ui_accent}; font-weight: 700;")
        cpu_card, self.cpu_chart_view, self.cpu_series = self.create_chart("CPU", "#4CAF50", fixed_max=100, compact=True)
        cpu_top = QWidget()
        cpu_top_layout = QHBoxLayout(cpu_top)
        cpu_top_layout.setContentsMargins(0, 0, 0, 0)
        cpu_top_layout.addWidget(self.cpu_label)
        cpu_top_layout.addStretch()
        cpu_top_layout.addWidget(self.cpu_trend)
        cpu_card.layout().insertWidget(0, cpu_top)
        self.cpu_mini = MiniSparklineWidget("#4CAF50")
        cpu_card.layout().insertWidget(1, self.cpu_mini)
        cpu_card.setMaximumHeight(110)
        cpu_card.setMinimumWidth(260)
        layout.addWidget(cpu_card, 0, 0)

        # GPU
        self.gpu_label = QLabel("N/A")
        self.gpu_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.gpu_trend = QLabel("")
        self.gpu_trend.setStyleSheet(f"color: {self.ui_accent}; font-weight: 700;")
        gpu_card, self.gpu_chart_view, self.gpu_series = self.create_chart("GPU", "#9C27B0", fixed_max=100, compact=True)
        gpu_top = QWidget()
        gpu_top_layout = QHBoxLayout(gpu_top)
        gpu_top_layout.setContentsMargins(0, 0, 0, 0)
        gpu_top_layout.addWidget(self.gpu_label)
        gpu_top_layout.addStretch()
        gpu_top_layout.addWidget(self.gpu_trend)
        gpu_card.layout().insertWidget(0, gpu_top)
        self.gpu_mini = MiniSparklineWidget("#9C27B0")
        gpu_card.layout().insertWidget(1, self.gpu_mini)
        gpu_card.setMaximumHeight(110)
        gpu_card.setMinimumWidth(260)
        layout.addWidget(gpu_card, 0, 1)

        # RAM
        self.memory_label = QLabel("0%")
        self.memory_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.memory_trend = QLabel("")
        self.memory_trend.setStyleSheet(f"color: {self.ui_accent}; font-weight: 700;")
        ram_card, self.memory_chart_view, self.memory_series = self.create_chart("RAM", "#2196F3", fixed_max=100, compact=True)
        ram_top = QWidget()
        ram_top_layout = QHBoxLayout(ram_top)
        ram_top_layout.setContentsMargins(0, 0, 0, 0)
        ram_top_layout.addWidget(self.memory_label)
        ram_top_layout.addStretch()
        ram_top_layout.addWidget(self.memory_trend)
        ram_card.layout().insertWidget(0, ram_top)
        self.memory_mini = MiniSparklineWidget("#2196F3")
        ram_card.layout().insertWidget(1, self.memory_mini)
        ram_card.setMaximumHeight(110)
        ram_card.setMinimumWidth(260)
        layout.addWidget(ram_card, 0, 2)

        # Disk
        self.disk_label = QLabel("0%")
        self.disk_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.disk_trend = QLabel("")
        self.disk_trend.setStyleSheet(f"color: {self.ui_accent}; font-weight: 700;")
        disk_card, self.disk_chart_view, self.disk_series = self.create_chart("Disk", "#FF9800", fixed_max=100, compact=True)
        disk_top = QWidget()
        disk_top_layout = QHBoxLayout(disk_top)
        disk_top_layout.setContentsMargins(0, 0, 0, 0)
        disk_top_layout.addWidget(self.disk_label)
        disk_top_layout.addStretch()
        disk_top_layout.addWidget(self.disk_trend)
        disk_card.layout().insertWidget(0, disk_top)
        self.disk_mini = MiniSparklineWidget("#FF9800")
        disk_card.layout().insertWidget(1, self.disk_mini)
        disk_card.setMaximumHeight(110)
        disk_card.setMinimumWidth(260)
        layout.addWidget(disk_card, 1, 0)

        # Network
        self.eth_label = QLabel("0%")
        self.eth_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.eth_trend = QLabel("")
        self.eth_trend.setStyleSheet(f"color: {self.ui_accent}; font-weight: 700;")
        eth_card, self.eth_chart_view, self.eth_series = self.create_chart("Network", "#00BCD4", fixed_max=100, compact=True)
        eth_top = QWidget()
        eth_top_layout = QHBoxLayout(eth_top)
        eth_top_layout.setContentsMargins(0, 0, 0, 0)
        eth_top_layout.addWidget(self.eth_label)
        eth_top_layout.addStretch()
        eth_top_layout.addWidget(self.eth_trend)
        eth_card.layout().insertWidget(0, eth_top)
        self.eth_mini = MiniSparklineWidget("#00BCD4")
        eth_card.layout().insertWidget(1, self.eth_mini)
        eth_card.setMaximumHeight(110)
        eth_card.setMinimumWidth(260)
        layout.addWidget(eth_card, 1, 1)

        # Processes small info card
        proc_card = QFrame()
        proc_card.setStyleSheet(f"QFrame {{ background-color: {self.ui_panel}; border-radius: 10px; padding: 12px; }}")
        proc_layout = QVBoxLayout(proc_card)
        proc_title = QLabel("Processes")
        proc_title.setStyleSheet(f"color: {self.ui_muted}; font-weight: 700;")
        proc_layout.addWidget(proc_title)
        self.process_label = QLabel("0")
        self.process_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        proc_layout.addWidget(self.process_label)
        proc_card.setMaximumHeight(110)
        proc_card.setMinimumWidth(260)
        layout.addWidget(proc_card, 1, 2)

        widget.setLayout(layout)
        return widget
        
    def create_details_tab(self):
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
        
    def create_cpu_details_tab(self):
        widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)

        # Card wrapper for CPU info
        from PyQt5.QtWidgets import QFrame
        cpu_card = QFrame()
        cpu_card.setStyleSheet(f"QFrame {{ background-color: {self.ui_panel}; border-radius: 10px; padding: 12px; }}")
        cpu_layout = QVBoxLayout(cpu_card)

        info_layout = QGridLayout()
        info_layout.setSpacing(10)
        info_layout.addWidget(QLabel("CPU Load:"), 0, 0)
        self.cpu_load_detail_label = QLabel()
        info_layout.addWidget(self.cpu_load_detail_label, 0, 1)

        info_layout.addWidget(QLabel("Physical Cores:"), 1, 0)
        self.cpu_physical_label = QLabel()
        info_layout.addWidget(self.cpu_physical_label, 1, 1)

        info_layout.addWidget(QLabel("Logical Cores:"), 2, 0)
        self.cpu_logical_label = QLabel()
        info_layout.addWidget(self.cpu_logical_label, 2, 1)

        info_layout.addWidget(QLabel("Current Frequency:"), 3, 0)
        self.cpu_current_freq_label = QLabel()
        info_layout.addWidget(self.cpu_current_freq_label, 3, 1)

        info_layout.addWidget(QLabel("Boost Frequency:"), 4, 0)
        self.cpu_boost_freq_label = QLabel()
        info_layout.addWidget(self.cpu_boost_freq_label, 4, 1)

        info_layout.addWidget(QLabel("Throttling:"), 5, 0)
        self.cpu_throttling_label = QLabel()
        info_layout.addWidget(self.cpu_throttling_label, 5, 1)

        info_layout.addWidget(QLabel("CPU Temp Max:"), 6, 0)
        self.cpu_temp_max_label = QLabel()
        info_layout.addWidget(self.cpu_temp_max_label, 6, 1)

        info_layout.addWidget(QLabel("CPU Temp Avg:"), 7, 0)
        self.cpu_temp_avg_label = QLabel()
        info_layout.addWidget(self.cpu_temp_avg_label, 7, 1)

        self.cpu_temp_hint_label = QLabel()
        self.cpu_temp_hint_label.setWordWrap(True)
        self.cpu_temp_hint_label.setStyleSheet(f"color: {self.ui_warning}; font-size: 11px;")
        info_layout.addWidget(self.cpu_temp_hint_label, 8, 0, 1, 2)

        info_layout.addWidget(QLabel("Power Usage:"), 9, 0)
        self.cpu_power_watts_label = QLabel()
        info_layout.addWidget(self.cpu_power_watts_label, 9, 1)

        info_layout.addWidget(QLabel("Package Power:"), 10, 0)
        self.cpu_power_package_label = QLabel()
        info_layout.addWidget(self.cpu_power_package_label, 10, 1)

        cpu_layout.addLayout(info_layout)
        main_layout.addWidget(cpu_card)

        main_layout.addWidget(QLabel("Per-Core Usage:"))
        self.cpu_core_labels = []
        self.cpu_core_graphs = []
        core_count = len(self.cpu_core_histories)
        core_colors = ["#4CAF50", "#66BB6A", "#81C784", "#43A047", "#2E7D32", "#1B5E20"]
        for i in range(core_count):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(8)
            core_label = QLabel(f"Core {i + 1}: 0%")
            core_label.setFont(QFont("Arial", 11))
            core_label.setMinimumWidth(95)
            self.cpu_core_labels.append(core_label)
            core_graph = GraphWidget(core_colors[i % len(core_colors)], fixed_max=100)
            core_graph.setMinimumHeight(52)
            core_graph.setMaximumHeight(60)
            self.cpu_core_graphs.append(core_graph)
            row_layout.addWidget(core_label)
            row_layout.addWidget(core_graph, 1)
            main_layout.addWidget(row_widget)

        main_layout.addWidget(QLabel("CPU Temperature Graph:"))
        self.cpu_temp_graph = GraphWidget()
        self.cpu_temp_graph.setMinimumHeight(160)
        main_layout.addWidget(self.cpu_temp_graph)

        widget.setLayout(main_layout)
        return widget
        
    def create_gpu_details_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        from PyQt5.QtWidgets import QFrame
        gpu_card = QFrame()
        gpu_card.setStyleSheet(f"QFrame {{ background-color: {self.ui_panel}; border-radius: 10px; padding: 12px; }}")
        g_layout = QGridLayout(gpu_card)
        g_layout.setSpacing(10)
        g_layout.addWidget(QLabel("GPU Name:"), 0, 0)
        self.gpu_name_label = QLabel()
        g_layout.addWidget(self.gpu_name_label, 0, 1)

        g_layout.addWidget(QLabel("Driver Version:"), 1, 0)
        self.gpu_driver_label = QLabel()
        g_layout.addWidget(self.gpu_driver_label, 1, 1)

        g_layout.addWidget(QLabel("GPU Load:"), 2, 0)
        self.gpu_load_label = QLabel()
        g_layout.addWidget(self.gpu_load_label, 2, 1)

        g_layout.addWidget(QLabel("Core Clock (MHz):"), 3, 0)
        self.gpu_core_clock_label = QLabel()
        g_layout.addWidget(self.gpu_core_clock_label, 3, 1)

        g_layout.addWidget(QLabel("Memory Clock (MHz):"), 4, 0)
        self.gpu_mem_clock_label = QLabel()
        g_layout.addWidget(self.gpu_mem_clock_label, 4, 1)

        g_layout.addWidget(QLabel("Temperature:"), 5, 0)
        self.gpu_temp_label = QLabel()
        g_layout.addWidget(self.gpu_temp_label, 5, 1)

        g_layout.addWidget(QLabel("Fan Speed:"), 6, 0)
        self.gpu_fan_label = QLabel()
        g_layout.addWidget(self.gpu_fan_label, 6, 1)

        g_layout.addWidget(QLabel("Throttling:"), 7, 0)
        self.gpu_throttle_label = QLabel()
        g_layout.addWidget(self.gpu_throttle_label, 7, 1)

        g_layout.addWidget(QLabel("VRAM Usage:"), 8, 0)
        self.gpu_mem_label = QLabel()
        g_layout.addWidget(self.gpu_mem_label, 8, 1)

        g_layout.addWidget(QLabel("VRAM Percent:"), 9, 0)
        self.gpu_mem_percent_label = QLabel()
        g_layout.addWidget(self.gpu_mem_percent_label, 9, 1)

        g_layout.addWidget(QLabel("Power Draw (W):"), 10, 0)
        self.gpu_power_draw_label = QLabel()
        g_layout.addWidget(self.gpu_power_draw_label, 10, 1)

        g_layout.addWidget(QLabel("Power Limit / Headroom:"), 11, 0)
        self.gpu_power_limit_label = QLabel()
        g_layout.addWidget(self.gpu_power_limit_label, 11, 1)

        layout.addWidget(gpu_card)
        widget.setLayout(layout)
        return widget
        
    def create_ram_details_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        from PyQt5.QtWidgets import QFrame
        ram_card = QFrame()
        ram_card.setStyleSheet(f"QFrame {{ background-color: {self.ui_panel}; border-radius: 10px; padding: 12px; }}")
        r_layout = QGridLayout(ram_card)
        r_layout.setSpacing(10)
        r_layout.addWidget(QLabel("Memory Usage:"), 0, 0)
        self.memory_percent_detail_label = QLabel()
        r_layout.addWidget(self.memory_percent_detail_label, 0, 1)

        r_layout.addWidget(QLabel("Total:"), 1, 0)
        self.memory_total_label = QLabel()
        r_layout.addWidget(self.memory_total_label, 1, 1)

        r_layout.addWidget(QLabel("Used:"), 2, 0)
        self.memory_used_label = QLabel()
        r_layout.addWidget(self.memory_used_label, 2, 1)

        r_layout.addWidget(QLabel("Available:"), 3, 0)
        self.memory_available_label = QLabel()
        r_layout.addWidget(self.memory_available_label, 3, 1)

        r_layout.addWidget(QLabel("Swap Total:"), 4, 0)
        self.swap_total_label = QLabel()
        r_layout.addWidget(self.swap_total_label, 4, 1)

        r_layout.addWidget(QLabel("Swap Used:"), 5, 0)
        self.swap_used_label = QLabel()
        r_layout.addWidget(self.swap_used_label, 5, 1)

        layout.addWidget(ram_card)
        widget.setLayout(layout)
        return widget
        
    def create_disk_details_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        from PyQt5.QtWidgets import QFrame
        disk_card = QFrame()
        disk_card.setStyleSheet(f"QFrame {{ background-color: {self.ui_panel}; border-radius: 10px; padding: 12px; }}")
        d_layout = QGridLayout(disk_card)
        d_layout.setSpacing(10)
        d_layout.addWidget(QLabel("Disk Usage:"), 0, 0)
        self.disk_usage_detail_label = QLabel()
        d_layout.addWidget(self.disk_usage_detail_label, 0, 1)

        d_layout.addWidget(QLabel("Total:"), 1, 0)
        self.disk_total_label = QLabel()
        d_layout.addWidget(self.disk_total_label, 1, 1)

        d_layout.addWidget(QLabel("Used:"), 2, 0)
        self.disk_used_label = QLabel()
        d_layout.addWidget(self.disk_used_label, 2, 1)

        d_layout.addWidget(QLabel("Free:"), 3, 0)
        self.disk_free_label = QLabel()
        d_layout.addWidget(self.disk_free_label, 3, 1)

        d_layout.addWidget(QLabel("Disk Busy:"), 4, 0)
        self.disk_busy_detail_label = QLabel()
        d_layout.addWidget(self.disk_busy_detail_label, 4, 1)

        d_layout.addWidget(QLabel("Throughput:"), 5, 0)
        self.disk_io_detail_label = QLabel()
        d_layout.addWidget(self.disk_io_detail_label, 5, 1)

        layout.addWidget(disk_card)
        widget.setLayout(layout)
        return widget
        
    def create_ethernet_details_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        from PyQt5.QtWidgets import QFrame
        net_card = QFrame()
        net_card.setStyleSheet(f"QFrame {{ background-color: {self.ui_panel}; border-radius: 10px; padding: 12px; }}")
        n_layout = QGridLayout(net_card)
        n_layout.setSpacing(10)
        n_layout.addWidget(QLabel("Interface:"), 0, 0)
        self.network_interface_label = QLabel()
        n_layout.addWidget(self.network_interface_label, 0, 1)

        n_layout.addWidget(QLabel("Link Speed:"), 1, 0)
        self.network_speed_label = QLabel()
        n_layout.addWidget(self.network_speed_label, 1, 1)

        n_layout.addWidget(QLabel("Upload:"), 2, 0)
        self.network_upload_label = QLabel()
        n_layout.addWidget(self.network_upload_label, 2, 1)

        n_layout.addWidget(QLabel("Download:"), 3, 0)
        self.network_download_label = QLabel()
        n_layout.addWidget(self.network_download_label, 3, 1)

        n_layout.addWidget(QLabel("Usage:"), 4, 0)
        self.network_usage_label = QLabel()
        n_layout.addWidget(self.network_usage_label, 4, 1)

        layout.addWidget(net_card)
        widget.setLayout(layout)
        return widget
        
    def update_system_info(self):
        # CPU
        self.slow_update_counter += 1
        do_slow_update = (self.slow_update_counter % self.slow_update_frequency) == 0

        cpu_percents = psutil.cpu_percent(interval=None, percpu=True)
        cpu_percent = round(sum(cpu_percents) / len(cpu_percents), 1) if cpu_percents else 0
        self.cpu_label.setText(f"{cpu_percent}%")
        self.cpu_history.append(cpu_percent)
        self.cpu_history = self.cpu_history[-self.max_history:]
        self.update_series(self.cpu_series if self.cpu_series is not None else self.cpu_chart_view, self.cpu_history)
        # update mini sparkline and trend
        try:
            if hasattr(self, 'cpu_mini'):
                self.cpu_mini.set_history(self.cpu_history)
            if hasattr(self, 'cpu_trend'):
                if len(self.cpu_history) >= 2:
                    prev = self.cpu_history[-2]
                    curr = self.cpu_history[-1]
                    diff = curr - prev
                    if abs(diff) < 0.5:
                        self.cpu_trend.setText("→")
                        self.cpu_trend.setStyleSheet(f"color: {self.ui_muted}; font-weight: 700;")
                    elif diff > 0:
                        self.cpu_trend.setText(f"▲ {diff:.1f}%")
                        self.cpu_trend.setStyleSheet("color: #FF6B6B; font-weight: 700;")
                    else:
                        self.cpu_trend.setText(f"▼ {abs(diff):.1f}%")
                        self.cpu_trend.setStyleSheet(f"color: {self.ui_accent}; font-weight: 700;")
        except Exception:
            pass
        if hasattr(self, 'cpu_bar'):
            self.cpu_bar.setValue(int(cpu_percent))

        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_freq = psutil.cpu_freq()
        cpu_freq_current = cpu_freq.current if cpu_freq else 0
        cpu_freq_max = cpu_freq.max if cpu_freq else 0
        self.cpu_load_detail_label.setText(f"{cpu_percent}%")
        self.cpu_physical_label.setText(str(cpu_count_physical))
        self.cpu_logical_label.setText(str(cpu_count_logical))
        self.cpu_current_freq_label.setText(f"{cpu_freq_current:.0f} MHz / {cpu_freq_current / 1000:.2f} GHz")
        self.cpu_boost_freq_label.setText(f"{cpu_freq_max:.0f} MHz / {cpu_freq_max / 1000:.2f} GHz")
        throttling_status = "Unknown"
        if cpu_freq and cpu_freq_max > 0:
            throttling_status = "Yes" if cpu_freq_current + 100 < cpu_freq_max and cpu_percent > 95 else "No"
        self.cpu_throttling_label.setText(throttling_status)

        for idx, label in enumerate(self.cpu_core_labels):
            if idx < len(cpu_percents):
                pct = cpu_percents[idx]
                label.setText(f"Core {idx + 1}: {pct}%")
                if idx < len(self.cpu_core_histories):
                    self.cpu_core_histories[idx].append(pct)
                    self.cpu_core_histories[idx] = self.cpu_core_histories[idx][-self.max_history:]
                if idx < len(self.cpu_core_graphs):
                    self.cpu_core_graphs[idx].set_history(self.cpu_core_histories[idx])
            else:
                label.setText(f"Core {idx + 1}: N/A")

        cpu_temp_readings = self.last_cpu_temp_readings
        if cpu_temp_readings:
            cpu_temp_max = max(cpu_temp_readings)
            cpu_temp_avg = sum(cpu_temp_readings) / len(cpu_temp_readings)
        else:
            cpu_temp_max = None
            cpu_temp_avg = None
        self.cpu_temp_max_label.setText(f"{cpu_temp_max:.1f} °C" if cpu_temp_max is not None else "N/A")
        self.cpu_temp_avg_label.setText(f"{cpu_temp_avg:.1f} °C" if cpu_temp_avg is not None else "N/A")
        if hasattr(self, 'cpu_temp_hint_label'):
            self.cpu_temp_hint_label.setText(self.last_cpu_temp_hint or "")
        if cpu_temp_max is not None:
            self.cpu_temp_history.append(cpu_temp_max)
            self.cpu_temp_history = self.cpu_temp_history[-self.max_history:]
            self.cpu_temp_graph.set_history(self.cpu_temp_history)

        if self.cpu_temp_thread is None or not self.cpu_temp_thread.is_alive():
            self.start_cpu_temp_background_refresh()

        cpu_power_watts = "N/A"
        cpu_package_power = "N/A"
        if hasattr(psutil, 'sensors_power'):
            try:
                power_data = psutil.sensors_power()
                if isinstance(power_data, dict):
                    cpu_power_watts = power_data.get('power' if 'power' in power_data else next(iter(power_data), ''), 'N/A')
                elif hasattr(power_data, 'power'):
                    cpu_power_watts = getattr(power_data, 'power')
            except Exception:
                pass
        self.cpu_power_watts_label.setText(str(cpu_power_watts))
        self.cpu_power_package_label.setText(str(cpu_package_power))
        
        # Memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        self.memory_label.setText(f"{memory_percent}%")
        self.memory_history.append(memory_percent)
        self.memory_history = self.memory_history[-self.max_history:]
        self.update_series(self.memory_series if self.memory_series is not None else self.memory_chart_view, self.memory_history)
        try:
            if hasattr(self, 'memory_mini'):
                self.memory_mini.set_history(self.memory_history)
            if hasattr(self, 'memory_trend') and len(self.memory_history) >= 2:
                prev = self.memory_history[-2]
                curr = self.memory_history[-1]
                diff = curr - prev
                if abs(diff) < 0.5:
                    self.memory_trend.setText("→")
                    self.memory_trend.setStyleSheet(f"color: {self.ui_muted}; font-weight: 700;")
                elif diff > 0:
                    self.memory_trend.setText(f"▲ {diff:.1f}%")
                    self.memory_trend.setStyleSheet("color: #FF6B6B; font-weight: 700;")
                else:
                    self.memory_trend.setText(f"▼ {abs(diff):.1f}%")
                    self.memory_trend.setStyleSheet(f"color: {self.ui_accent}; font-weight: 700;")
        except Exception:
            pass
        if hasattr(self, 'memory_bar'):
            self.memory_bar.setValue(int(memory_percent))
        
        total_gb = memory.total / (1024**3)
        available_gb = memory.available / (1024**3)
        used_gb = memory.used / (1024**3)
        self.memory_percent_detail_label.setText(f"{memory_percent}%")
        self.memory_total_label.setText(f"Total: {total_gb:.2f} GB")
        self.memory_used_label.setText(f"{used_gb:.2f} GB")
        self.memory_available_label.setText(f"{available_gb:.2f} GB")
        swap = psutil.swap_memory()
        swap_total = swap.total / (1024**3)
        swap_used = swap.used / (1024**3)
        self.swap_total_label.setText(f"{swap_total:.2f} GB")
        self.swap_used_label.setText(f"{swap_used:.2f} GB")
        
        # Disk usage percent
        disk_io = psutil.disk_io_counters()
        write_bytes_delta = 0
        read_bytes_delta = 0
        if self.prev_disk_io:
            write_bytes_delta = disk_io.write_bytes - self.prev_disk_io.write_bytes
            read_bytes_delta = disk_io.read_bytes - self.prev_disk_io.read_bytes
        self.prev_disk_io = disk_io
        total_mbps = (read_bytes_delta + write_bytes_delta) / (1024 ** 2)
        disk_busy = get_disk_busy_percent()
        if disk_busy is None:
            max_io_mbps = 200.0
            disk_write_percent = int(min(max((total_mbps / max_io_mbps) * 100, 0), 100))
        else:
            disk_write_percent = int(min(max(disk_busy, 0), 100))
        self.disk_label.setText(f"{disk_write_percent}%")
        self.disk_history.append(disk_write_percent)
        self.disk_history = self.disk_history[-self.max_history:]
        self.update_series(self.disk_series if self.disk_series is not None else self.disk_chart_view, self.disk_history)
        try:
            if hasattr(self, 'disk_mini'):
                self.disk_mini.set_history(self.disk_history)
            if hasattr(self, 'disk_trend') and len(self.disk_history) >= 2:
                prev = self.disk_history[-2]
                curr = self.disk_history[-1]
                diff = curr - prev
                if abs(diff) < 0.5:
                    self.disk_trend.setText("→")
                    self.disk_trend.setStyleSheet(f"color: {self.ui_muted}; font-weight: 700;")
                elif diff > 0:
                    self.disk_trend.setText(f"▲ {diff:.1f}%")
                    self.disk_trend.setStyleSheet("color: #FF6B6B; font-weight: 700;")
                else:
                    self.disk_trend.setText(f"▼ {abs(diff):.1f}%")
                    self.disk_trend.setStyleSheet(f"color: {self.ui_accent}; font-weight: 700;")
        except Exception:
            pass
        if hasattr(self, 'disk_bar'):
            self.disk_bar.setValue(disk_write_percent)
            self.disk_bar.setFormat(f"{disk_write_percent}% ({total_mbps:.2f} MB/s)")
        self.disk_usage_detail_label.setText(f"{disk_write_percent}%")
        self.disk_busy_detail_label.setText(f"{disk_write_percent}%")
        self.disk_io_detail_label.setText(f"{total_mbps:.2f} MB/s")
        
        # Ethernet usage percent
        eth_send_percent = 0
        eth_recv_percent = 0
        eth_send_mbps = 0.0
        eth_recv_mbps = 0.0
        interface_name = self.network_interface or get_active_network_interface()
        interface_speed = get_interface_speed(interface_name) or 0
        if interface_name and interface_speed:
            net_io = psutil.net_io_counters(pernic=True)
            if interface_name in net_io and interface_name in self.prev_net_io:
                send_delta = net_io[interface_name].bytes_sent - self.prev_net_io[interface_name].bytes_sent
                recv_delta = net_io[interface_name].bytes_recv - self.prev_net_io[interface_name].bytes_recv
                eth_send_mbps = (send_delta * 8) / 1_000_000
                eth_recv_mbps = (recv_delta * 8) / 1_000_000
                if interface_speed > 0:
                    eth_send_percent = int(min(max(eth_send_mbps / interface_speed * 100, 0), 100))
                    eth_recv_percent = int(min(max(eth_recv_mbps / interface_speed * 100, 0), 100))
        self.prev_net_io = psutil.net_io_counters(pernic=True)
        eth_percent = max(eth_send_percent, eth_recv_percent)
        self.eth_label.setText(f"{eth_percent}%")
        self.eth_history.append(eth_percent)
        self.eth_history = self.eth_history[-self.max_history:]
        self.update_series(self.eth_series if self.eth_series is not None else self.eth_chart_view, self.eth_history)
        try:
            if hasattr(self, 'eth_mini'):
                self.eth_mini.set_history(self.eth_history)
            if hasattr(self, 'eth_trend') and len(self.eth_history) >= 2:
                prev = self.eth_history[-2]
                curr = self.eth_history[-1]
                diff = curr - prev
                if abs(diff) < 0.5:
                    self.eth_trend.setText("→")
                    self.eth_trend.setStyleSheet(f"color: {self.ui_muted}; font-weight: 700;")
                elif diff > 0:
                    self.eth_trend.setText(f"▲ {diff:.1f}%")
                    self.eth_trend.setStyleSheet("color: #FF6B6B; font-weight: 700;")
                else:
                    self.eth_trend.setText(f"▼ {abs(diff):.1f}%")
                    self.eth_trend.setStyleSheet(f"color: {self.ui_accent}; font-weight: 700;")
        except Exception:
            pass
        if hasattr(self, 'eth_bar'):
            self.eth_bar.setValue(eth_percent)
            self.eth_bar.setFormat(f"{eth_percent}% (↑{eth_send_mbps:.1f} Mb/s ↓{eth_recv_mbps:.1f} Mb/s)")
        self.network_interface_label.setText(interface_name or "Unknown")
        self.network_speed_label.setText(f"{interface_speed} Mbps" if interface_speed else "Unknown")
        self.network_upload_label.setText(f"↑{eth_send_mbps:.1f} Mb/s")
        self.network_download_label.setText(f"↓{eth_recv_mbps:.1f} Mb/s")
        self.network_usage_label.setText(f"{eth_percent}%")
        
        disk = psutil.disk_usage('/')
        total_gb = disk.total / (1024**3)
        used_gb = disk.used / (1024**3)
        free_gb = disk.free / (1024**3)
        self.disk_total_label.setText(f"Total: {total_gb:.2f} GB")
        self.disk_used_label.setText(f"{used_gb:.2f} GB")
        self.disk_free_label.setText(f"{free_gb:.2f} GB")
        
        # GPU
        gpu_shown = False
        gpu_temp = None
        gpu_load = 0.0
        gpu_mem = 0.0
        if GPUtil is not None:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_load = gpu.load * 100
                    gpu_mem = gpu.memoryUtil * 100
                    gpu_temp = getattr(gpu, "temperature", None)
                    self.gpu_label.setText(f"{gpu_load:.0f}%")
                    if hasattr(self, 'gpu_bar'):
                        self.gpu_bar.setValue(int(gpu_load))
                        self.gpu_bar.setFormat(f"{gpu_mem:.0f}% mem")
                    self.gpu_name_label.setText(f"{gpu.name}")
                    self.gpu_load_label.setText(f"Load: {gpu_load:.0f}%")
                    self.gpu_mem_label.setText(f"Memory: {gpu.memoryUsed:.0f} MiB / {gpu.memoryTotal:.0f} MiB")
                    self.gpu_mem_percent_label.setText(f"{gpu_mem:.0f}%")
                    self.gpu_temp_label.setText(f"{gpu_temp} °C" if gpu_temp is not None else "N/A")
                    gpu_shown = True
                    self.last_gpu_data = {
                        'gpu_load': gpu_load,
                        'gpu_mem': gpu_mem,
                        'gpu_temp': gpu_temp,
                        'gpu_name': gpu.name,
                        'gpu_used': gpu.memoryUsed,
                        'gpu_total': gpu.memoryTotal,
                        'gpu_label': self.gpu_label.text(),
                        'gpu_load_label': self.gpu_load_label.text(),
                        'gpu_mem_label': self.gpu_mem_label.text(),
                        'gpu_mem_percent_label': self.gpu_mem_percent_label.text(),
                        'gpu_temp_label': self.gpu_temp_label.text(),
                    }
                    # Supplement GPUtil info with nvidia-smi for more fields if available
                    try:
                        proc = subprocess.run(
                            [
                                "nvidia-smi",
                                "--query-gpu=driver_version,clocks.current.graphics,clocks.current.memory,fan.speed,power.draw,power.limit",
                                "--format=csv,noheader,nounits",
                            ],
                            capture_output=True,
                            text=True,
                            timeout=0.8,
                        )
                        if proc.returncode == 0 and proc.stdout.strip():
                            r = next(csv.reader(io.StringIO(proc.stdout)), None)
                            if r and len(r) >= 6:
                                drv = r[0].strip()
                                try:
                                    core_clk = float(r[1].strip())
                                except Exception:
                                    core_clk = None
                                try:
                                    mem_clk = float(r[2].strip())
                                except Exception:
                                    mem_clk = None
                                fan = r[3].strip()
                                try:
                                    p_draw = float(r[4].strip())
                                except Exception:
                                    p_draw = None
                                try:
                                    p_limit = float(r[5].strip())
                                except Exception:
                                    p_limit = None
                                self.gpu_driver_label.setText(drv)
                                self.gpu_core_clock_label.setText(f"{core_clk:.0f} MHz" if core_clk is not None else "N/A")
                                self.gpu_mem_clock_label.setText(f"{mem_clk:.0f} MHz" if mem_clk is not None else "N/A")
                                self.gpu_fan_label.setText(fan or "N/A")
                                self.gpu_power_draw_label.setText(f"{p_draw:.1f} W" if p_draw is not None else "N/A")
                                if p_limit is not None:
                                    try:
                                        headroom_pct = max(0.0, (p_limit - (p_draw or 0)) / p_limit * 100)
                                        self.gpu_power_limit_label.setText(f"{p_limit:.0f} W ({headroom_pct:.0f}% headroom)")
                                    except Exception:
                                        self.gpu_power_limit_label.setText(f"{p_limit:.0f} W")
                    except Exception:
                        pass
            except Exception:
                pass
        # If GPUtil didn't provide GPU info, try nvidia-smi as a fallback.
        # Run this whenever GPU isn't shown (keeps quick timeout to avoid blocking).
        if not gpu_shown:
            try:
                proc = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=name,driver_version,utilization.gpu,clocks.current.graphics,clocks.current.memory,temperature.gpu,fan.speed,power.draw,power.limit,memory.used,memory.total",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    reader = csv.reader(io.StringIO(proc.stdout))
                    # Use first GPU only for UI
                    row = next(reader, None)
                    if row and len(row) >= 11:
                        # Map fields from nvidia-smi
                        name = row[0].strip()
                        driver = row[1].strip()
                        try:
                            load = float(row[2].strip())
                        except Exception:
                            load = 0.0
                        try:
                            core_clk = float(row[3].strip())
                        except Exception:
                            core_clk = None
                        try:
                            mem_clk = float(row[4].strip())
                        except Exception:
                            mem_clk = None
                        try:
                            temp = float(row[5].strip())
                        except Exception:
                            temp = None
                        fan = row[6].strip()
                        try:
                            power_draw = float(row[7].strip())
                        except Exception:
                            power_draw = None
                        try:
                            power_limit = float(row[8].strip())
                        except Exception:
                            power_limit = None
                        mem_used = row[9].strip()
                        mem_total = row[10].strip()

                        gpu_load = load
                        gpu_mem = None
                        # parse memory values (may be integers)
                        try:
                            mem_used_val = float(mem_used)
                            mem_total_val = float(mem_total)
                            gpu_mem = (mem_used_val / mem_total_val) * 100 if mem_total_val > 0 else 0.0
                        except Exception:
                            mem_used_val = None
                            mem_total_val = None

                        # Determine throttling heuristics
                        throttle = "No"
                        if temp is not None and temp >= 90:
                            throttle = "Yes (thermal)"
                        elif power_limit is not None and power_draw is not None and power_draw >= power_limit * 0.98:
                            throttle = "Yes (power)"

                        # Update UI labels
                        self.gpu_label.setText(f"{gpu_load:.0f}%")
                        if hasattr(self, 'gpu_bar'):
                            self.gpu_bar.setValue(int(gpu_load))
                            if gpu_mem is not None:
                                self.gpu_bar.setFormat(f"{gpu_mem:.0f}% mem")
                        self.gpu_name_label.setText(name)
                        self.gpu_driver_label.setText(driver)
                        self.gpu_load_label.setText(f"Load: {gpu_load:.0f}%")
                        if mem_used_val is not None and mem_total_val is not None:
                            self.gpu_mem_label.setText(f"Memory: {mem_used_val:.0f} MiB / {mem_total_val:.0f} MiB")
                            self.gpu_mem_percent_label.setText(f"{(gpu_mem or 0):.0f}%")
                        else:
                            self.gpu_mem_label.setText(f"Memory: {mem_used} / {mem_total}")
                        self.gpu_core_clock_label.setText(f"{core_clk:.0f} MHz" if core_clk is not None else "N/A")
                        self.gpu_mem_clock_label.setText(f"{mem_clk:.0f} MHz" if mem_clk is not None else "N/A")
                        self.gpu_temp_label.setText(f"{temp:.0f} °C" if temp is not None else "N/A")
                        self.gpu_fan_label.setText(f"{fan}" if fan else "N/A")
                        self.gpu_power_draw_label.setText(f"{power_draw:.1f} W" if power_draw is not None else "N/A")
                        if power_limit is not None:
                            headroom = None
                            if power_draw is not None:
                                try:
                                    headroom_pct = max(0.0, (power_limit - power_draw) / power_limit * 100)
                                    headroom = f"{power_limit:.0f} W ({headroom_pct:.0f}% headroom)"
                                except Exception:
                                    headroom = f"{power_limit:.0f} W"
                            else:
                                headroom = f"{power_limit:.0f} W"
                            self.gpu_power_limit_label.setText(headroom)
                        else:
                            self.gpu_power_limit_label.setText("N/A")

                        self.gpu_throttle_label.setText(throttle)

                        gpu_shown = True
                        self.last_gpu_data = {
                            'gpu_load': gpu_load,
                            'gpu_mem': gpu_mem,
                            'gpu_temp': temp,
                            'gpu_name': name,
                            'gpu_used': mem_used_val,
                            'gpu_total': mem_total_val,
                            'gpu_label': self.gpu_label.text(),
                            'gpu_load_label': self.gpu_load_label.text(),
                            'gpu_mem_label': self.gpu_mem_label.text(),
                            'gpu_mem_percent_label': self.gpu_mem_percent_label.text(),
                            'gpu_temp_label': self.gpu_temp_label.text(),
                            'gpu_driver': driver,
                            'gpu_core_clock': core_clk,
                            'gpu_mem_clock': mem_clk,
                            'gpu_fan': fan,
                            'gpu_power_draw': power_draw,
                            'gpu_power_limit': power_limit,
                            'gpu_throttle': throttle,
                        }
            except Exception:
                pass
        if not gpu_shown and self.last_gpu_data:
            data = self.last_gpu_data
            gpu_load = data.get('gpu_load', 0.0)
            gpu_mem = data.get('gpu_mem', 0.0)
            gpu_temp = data.get('gpu_temp')
            self.gpu_label.setText(data.get('gpu_label', 'N/A'))
            if hasattr(self, 'gpu_bar'):
                self.gpu_bar.setValue(int(gpu_load))
                self.gpu_bar.setFormat(f"{gpu_mem:.0f}% mem")
            self.gpu_name_label.setText(data.get('gpu_name', 'GPU info unavailable'))
            self.gpu_load_label.setText(data.get('gpu_load_label', ''))
            self.gpu_mem_label.setText(data.get('gpu_mem_label', ''))
            self.gpu_mem_percent_label.setText(data.get('gpu_mem_percent_label', ''))
            self.gpu_temp_label.setText(data.get('gpu_temp_label', ''))
            gpu_shown = True
        if not gpu_shown:
            self.gpu_label.setText("N/A")
            if hasattr(self, 'gpu_bar'):
                self.gpu_bar.setValue(0)
                self.gpu_bar.setFormat("No GPU")
            self.gpu_name_label.setText("GPU info unavailable")
            self.gpu_load_label.setText("")
            self.gpu_mem_label.setText("")
            self.gpu_mem_percent_label.setText("")
            self.gpu_temp_label.setText("")

        self.gpu_history.append(gpu_load)
        self.gpu_history = self.gpu_history[-self.max_history:]
        self.update_series(self.gpu_series if self.gpu_series is not None else self.gpu_chart_view, self.gpu_history)
        try:
            if hasattr(self, 'gpu_mini'):
                self.gpu_mini.set_history(self.gpu_history)
            if hasattr(self, 'gpu_trend') and len(self.gpu_history) >= 2:
                prev = self.gpu_history[-2]
                curr = self.gpu_history[-1]
                diff = curr - prev
                if abs(diff) < 0.5:
                    self.gpu_trend.setText("→")
                    self.gpu_trend.setStyleSheet(f"color: {self.ui_muted}; font-weight: 700;")
                elif diff > 0:
                    self.gpu_trend.setText(f"▲ {diff:.1f}%")
                    self.gpu_trend.setStyleSheet("color: #FF6B6B; font-weight: 700;")
                else:
                    self.gpu_trend.setText(f"▼ {abs(diff):.1f}%")
                    self.gpu_trend.setStyleSheet(f"color: {self.ui_accent}; font-weight: 700;")
        except Exception:
            pass
        
        # Processes
        process_count = len(psutil.pids())
        self.process_label.setText(str(process_count))

        if do_slow_update:
            self.last_top_processes = get_top_processes(5)

        self.update_gaming_tab(
            cpu_percent=cpu_percent,
            gpu_load=gpu_load,
            memory_percent=memory_percent,
            gpu_mem=gpu_mem,
            cpu_temp_max=cpu_temp_max if cpu_temp_readings else None,
            gpu_temp=gpu_temp,
            # Additional GPU details for gaming tab
            gpu_model=(self.last_gpu_data.get('gpu_name') if self.last_gpu_data else None),
            vram_total=(self.last_gpu_data.get('gpu_total') if self.last_gpu_data else None),
            driver_version=(self.last_gpu_data.get('gpu_driver') if self.last_gpu_data else None),
            core_clock=(self.last_gpu_data.get('gpu_core_clock') if self.last_gpu_data else None),
            memory_clock=(self.last_gpu_data.get('gpu_mem_clock') if self.last_gpu_data else None),
            fan_speed=(self.last_gpu_data.get('gpu_fan') if self.last_gpu_data else None),
            throttling=(self.last_gpu_data.get('gpu_throttle') if self.last_gpu_data else None),
            power_draw=(self.last_gpu_data.get('gpu_power_draw') if self.last_gpu_data else None),
            power_limit=(self.last_gpu_data.get('gpu_power_limit') if self.last_gpu_data else None),
        )

    def update_gaming_tab(
        self,
        cpu_percent,
        gpu_load,
        memory_percent,
        gpu_mem,
        cpu_temp_max,
        gpu_temp,
        gpu_model=None,
        vram_total=None,
        driver_version=None,
        core_clock=None,
        memory_clock=None,
        fan_speed=None,
        throttling=None,
        power_draw=None,
        power_limit=None,
    ):
        if not hasattr(self, "gaming_tab"):
            return

        update_session_peaks(
            self.session_peaks,
            cpu_percent,
            gpu_load,
            memory_percent,
            cpu_temp_max,
            gpu_temp,
        )
        ping_results = self.ping_monitor.get_results()
        ping_avg = self.ping_monitor.average_ms()
        bottleneck = analyze_bottleneck(cpu_percent, gpu_load, memory_percent)
        alerts = collect_performance_alerts(
            cpu_percent,
            gpu_load,
            memory_percent,
            cpu_temp_max,
            gpu_temp,
            ping_avg,
        )
        self.gaming_tab.update_metrics(
            {
                "foreground": get_foreground_app(),
                "cpu_percent": cpu_percent,
                "gpu_percent": gpu_load,
                "ram_percent": memory_percent,
                "vram_percent": gpu_mem if gpu_mem else None,
                "gpu_model": gpu_model,
                "vram_total": vram_total,
                "driver_version": driver_version,
                "core_clock": core_clock,
                "memory_clock": memory_clock,
                "fan_speed": fan_speed,
                "throttling": throttling,
                "power_draw": power_draw,
                "power_limit": power_limit,
                "ping_avg": ping_avg,
                "ping_results": ping_results,
                "bottleneck": bottleneck,
                "alerts": alerts,
                "peaks": self.session_peaks,
                "top_processes": self.last_top_processes,
            }
        )

