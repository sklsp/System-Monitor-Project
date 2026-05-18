import sys
import subprocess
import psutil
try:
    import GPUtil
except ModuleNotFoundError:
    GPUtil = None

try:
    from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
    QT_CHARTS_AVAILABLE = True
except Exception:
    QT_CHARTS_AVAILABLE = False

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout, QLabel, QProgressBar, QTabWidget
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPainter, QColor

from monitoring.net import get_active_network_interface, get_interface_speed
from monitoring.disk import get_disk_busy_percent
from ui.graphs import GraphWidget


class SystemMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Monitor")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")

        # Initialize data storage for charts
        self.cpu_history = []
        self.memory_history = []
        self.gpu_history = []
        self.disk_history = []
        self.eth_history = []
        self.max_history = 60
        self.prev_disk_io = psutil.disk_io_counters()
        self.prev_net_io = psutil.net_io_counters(pernic=True)
        self.network_interface = get_active_network_interface()

        self.init_ui()

        # Timer for updating info
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_system_info)
        self.timer.start(1000)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        title = QLabel("System Monitor")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #555; }
            QTabBar::tab { background-color: #3b3b3b; color: #fff; padding: 8px 20px; }
            QTabBar::tab:selected { background-color: #555; }
        """)

        overview_widget = self.create_overview_tab()
        tabs.addTab(overview_widget, "Overview")

        details_widget = self.create_details_tab()
        tabs.addTab(details_widget, "Details")

        main_layout.addWidget(tabs)
        central_widget.setLayout(main_layout)

    def create_chart(self, title, color):
        if not QT_CHARTS_AVAILABLE:
            return GraphWidget(), None, None

        series = QLineSeries()
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(title)
        chart.legend().hide()

        axis_x = QValueAxis()
        axis_x.setLabelFormat("%d")
        axis_x.setRange(0, self.max_history)
        axis_x.setTickCount(6)
        axis_x.setTitleText("Seconds")

        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setTickCount(5)
        axis_y.setTitleText("%")

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(180)
        chart_view.setStyleSheet("background-color: #2b2b2b;")

        return chart_view, series, axis_x

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
        except Exception:
            return

    def create_overview_tab(self):
        widget = QWidget()
        layout = QGridLayout()
        layout.setSpacing(15)

        # CPU Info
        layout.addWidget(QLabel("CPU Usage"), 0, 0)
        self.cpu_label = QLabel("0%")
        self.cpu_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.cpu_label, 0, 1)
        self.cpu_chart_view, self.cpu_series, _ = self.create_chart("CPU Usage", "#4CAF50")
        if self.cpu_chart_view:
            layout.addWidget(self.cpu_chart_view, 1, 0, 1, 2)
        else:
            self.cpu_bar = QProgressBar()
            self.cpu_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #555;
                    border-radius: 5px;
                    background-color: #3b3b3b;
                    height: 25px;
                }
                QProgressBar::chunk { background-color: #4CAF50; }
            """)
            layout.addWidget(self.cpu_bar, 1, 0, 1, 2)

        # Memory Info
        layout.addWidget(QLabel("Memory Usage"), 2, 0)
        self.memory_label = QLabel("0%")
        self.memory_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.memory_label, 2, 1)
        self.memory_chart_view, self.memory_series, _ = self.create_chart("Memory Usage", "#2196F3")
        if self.memory_chart_view:
            layout.addWidget(self.memory_chart_view, 3, 0, 1, 2)
        else:
            self.memory_bar = QProgressBar()
            self.memory_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #555;
                    border-radius: 5px;
                    background-color: #3b3b3b;
                    height: 25px;
                }
                QProgressBar::chunk { background-color: #2196F3; }
            """)
            layout.addWidget(self.memory_bar, 3, 0, 1, 2)

        # GPU Info
        layout.addWidget(QLabel("GPU Usage"), 4, 0)
        self.gpu_label = QLabel("N/A")
        self.gpu_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.gpu_label, 4, 1)
        self.gpu_chart_view, self.gpu_series, _ = self.create_chart("GPU Usage", "#9C27B0")
        if self.gpu_chart_view:
            layout.addWidget(self.gpu_chart_view, 5, 0, 1, 2)
        else:
            self.gpu_bar = QProgressBar()
            self.gpu_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #555;
                    border-radius: 5px;
                    background-color: #3b3b3b;
                    height: 25px;
                }
                QProgressBar::chunk { background-color: #9C27B0; }
            """)
            layout.addWidget(self.gpu_bar, 5, 0, 1, 2)

        # Disk Usage Info
        layout.addWidget(QLabel("Disk Usage"), 6, 0)
        self.disk_label = QLabel("0%")
        self.disk_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.disk_label, 6, 1)
        self.disk_chart_view, self.disk_series, _ = self.create_chart("Disk Usage", "#FF9800")
        if self.disk_chart_view:
            layout.addWidget(self.disk_chart_view, 7, 0, 1, 2)
        else:
            self.disk_bar = QProgressBar()
            self.disk_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #555;
                    border-radius: 5px;
                    background-color: #3b3b3b;
                    height: 25px;
                }
                QProgressBar::chunk { background-color: #FF9800; }
            """)
            layout.addWidget(self.disk_bar, 7, 0, 1, 2)

        # Ethernet Info
        layout.addWidget(QLabel("Ethernet Usage"), 8, 0)
        self.eth_label = QLabel("0%")
        self.eth_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.eth_label, 8, 1)
        self.eth_chart_view, self.eth_series, _ = self.create_chart("Ethernet Usage", "#00BCD4")
        if self.eth_chart_view:
            layout.addWidget(self.eth_chart_view, 9, 0, 1, 2)
        else:
            self.eth_bar = QProgressBar()
            self.eth_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #555;
                    border-radius: 5px;
                    background-color: #3b3b3b;
                    height: 25px;
                }
                QProgressBar::chunk { background-color: #00BCD4; }
            """)
            layout.addWidget(self.eth_bar, 9, 0, 1, 2)

        # Process Info
        layout.addWidget(QLabel("Process Count"), 10, 0)
        self.process_label = QLabel("0")
        self.process_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.process_label, 10, 1)

        widget.setLayout(layout)
        return widget
        
    def create_details_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        details_tabs = QTabWidget()
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
        layout = QGridLayout()
        layout.setSpacing(10)
        layout.addWidget(QLabel("CPU Load:"), 0, 0)
        self.cpu_load_detail_label = QLabel()
        layout.addWidget(self.cpu_load_detail_label, 0, 1)
        
        layout.addWidget(QLabel("Physical Cores:"), 1, 0)
        self.cpu_physical_label = QLabel()
        layout.addWidget(self.cpu_physical_label, 1, 1)
        
        layout.addWidget(QLabel("Logical Cores:"), 2, 0)
        self.cpu_logical_label = QLabel()
        layout.addWidget(self.cpu_logical_label, 2, 1)
        
        layout.addWidget(QLabel("Frequency:"), 3, 0)
        self.cpu_freq_label = QLabel()
        layout.addWidget(self.cpu_freq_label, 3, 1)
        
        layout.addWidget(QLabel("Max Frequency:"), 4, 0)
        self.cpu_max_freq_label = QLabel()
        layout.addWidget(self.cpu_max_freq_label, 4, 1)
        
        widget.setLayout(layout)
        return widget
        
    def create_gpu_details_tab(self):
        widget = QWidget()
        layout = QGridLayout()
        layout.setSpacing(10)
        layout.addWidget(QLabel("GPU Name:"), 0, 0)
        self.gpu_name_label = QLabel()
        layout.addWidget(self.gpu_name_label, 0, 1)
        
        layout.addWidget(QLabel("GPU Load:"), 1, 0)
        self.gpu_load_label = QLabel()
        layout.addWidget(self.gpu_load_label, 1, 1)
        
        layout.addWidget(QLabel("Memory Usage:"), 2, 0)
        self.gpu_mem_label = QLabel()
        layout.addWidget(self.gpu_mem_label, 2, 1)
        
        layout.addWidget(QLabel("Memory Percent:"), 3, 0)
        self.gpu_mem_percent_label = QLabel()
        layout.addWidget(self.gpu_mem_percent_label, 3, 1)
        
        layout.addWidget(QLabel("Temperature:"), 4, 0)
        self.gpu_temp_label = QLabel()
        layout.addWidget(self.gpu_temp_label, 4, 1)
        
        widget.setLayout(layout)
        return widget
        
    def create_ram_details_tab(self):
        widget = QWidget()
        layout = QGridLayout()
        layout.setSpacing(10)
        layout.addWidget(QLabel("Memory Usage:"), 0, 0)
        self.memory_percent_detail_label = QLabel()
        layout.addWidget(self.memory_percent_detail_label, 0, 1)
        
        layout.addWidget(QLabel("Total:"), 1, 0)
        self.memory_total_label = QLabel()
        layout.addWidget(self.memory_total_label, 1, 1)
        
        layout.addWidget(QLabel("Used:"), 2, 0)
        self.memory_used_label = QLabel()
        layout.addWidget(self.memory_used_label, 2, 1)
        
        layout.addWidget(QLabel("Available:"), 3, 0)
        self.memory_available_label = QLabel()
        layout.addWidget(self.memory_available_label, 3, 1)
        
        layout.addWidget(QLabel("Swap Total:"), 4, 0)
        self.swap_total_label = QLabel()
        layout.addWidget(self.swap_total_label, 4, 1)
        
        layout.addWidget(QLabel("Swap Used:"), 5, 0)
        self.swap_used_label = QLabel()
        layout.addWidget(self.swap_used_label, 5, 1)
        
        widget.setLayout(layout)
        return widget
        
    def create_disk_details_tab(self):
        widget = QWidget()
        layout = QGridLayout()
        layout.setSpacing(10)
        layout.addWidget(QLabel("Disk Usage:"), 0, 0)
        self.disk_usage_detail_label = QLabel()
        layout.addWidget(self.disk_usage_detail_label, 0, 1)
        
        layout.addWidget(QLabel("Total:"), 1, 0)
        self.disk_total_label = QLabel()
        layout.addWidget(self.disk_total_label, 1, 1)
        
        layout.addWidget(QLabel("Used:"), 2, 0)
        self.disk_used_label = QLabel()
        layout.addWidget(self.disk_used_label, 2, 1)
        
        layout.addWidget(QLabel("Free:"), 3, 0)
        self.disk_free_label = QLabel()
        layout.addWidget(self.disk_free_label, 3, 1)
        
        layout.addWidget(QLabel("Disk Busy:"), 4, 0)
        self.disk_busy_detail_label = QLabel()
        layout.addWidget(self.disk_busy_detail_label, 4, 1)
        
        layout.addWidget(QLabel("Throughput:"), 5, 0)
        self.disk_io_detail_label = QLabel()
        layout.addWidget(self.disk_io_detail_label, 5, 1)
        
        widget.setLayout(layout)
        return widget
        
    def create_ethernet_details_tab(self):
        widget = QWidget()
        layout = QGridLayout()
        layout.setSpacing(10)
        layout.addWidget(QLabel("Interface:"), 0, 0)
        self.network_interface_label = QLabel()
        layout.addWidget(self.network_interface_label, 0, 1)
        
        layout.addWidget(QLabel("Link Speed:"), 1, 0)
        self.network_speed_label = QLabel()
        layout.addWidget(self.network_speed_label, 1, 1)
        
        layout.addWidget(QLabel("Upload:"), 2, 0)
        self.network_upload_label = QLabel()
        layout.addWidget(self.network_upload_label, 2, 1)
        
        layout.addWidget(QLabel("Download:"), 3, 0)
        self.network_download_label = QLabel()
        layout.addWidget(self.network_download_label, 3, 1)
        
        layout.addWidget(QLabel("Usage:"), 4, 0)
        self.network_usage_label = QLabel()
        layout.addWidget(self.network_usage_label, 4, 1)
        
        widget.setLayout(layout)
        return widget
        
    def update_system_info(self):
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_label.setText(f"{cpu_percent}%")
        self.cpu_history.append(cpu_percent)
        self.cpu_history = self.cpu_history[-self.max_history:]
        self.update_series(self.cpu_chart_view, self.cpu_history)
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
        self.cpu_freq_label.setText(f"{cpu_freq_current:.0f} MHz")
        self.cpu_max_freq_label.setText(f"{cpu_freq_max:.0f} MHz")
        
        # Memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        self.memory_label.setText(f"{memory_percent}%")
        self.memory_history.append(memory_percent)
        self.memory_history = self.memory_history[-self.max_history:]
        self.update_series(self.memory_chart_view, self.memory_history)
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
        self.update_series(self.disk_chart_view, self.disk_history)
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
        self.update_series(self.eth_chart_view, self.eth_history)
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
            except Exception:
                pass
        if not gpu_shown:
            try:
                proc = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,utilization.gpu,utilization.memory,memory.used,memory.total", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    fields = [f.strip() for f in proc.stdout.split(',')]
                    if len(fields) >= 5:
                        name, load, mem_util, mem_used, mem_total = fields[:5]
                        gpu_load = float(load)
                        gpu_mem = float(mem_util)
                        self.gpu_label.setText(f"{gpu_load:.0f}%")
                        if hasattr(self, 'gpu_bar'):
                            self.gpu_bar.setValue(int(gpu_load))
                            self.gpu_bar.setFormat(f"{gpu_mem:.0f}% mem")
                        self.gpu_name_label.setText(name)
                        self.gpu_load_label.setText(f"Load: {gpu_load:.0f}%")
                        self.gpu_mem_label.setText(f"Memory: {mem_used} MiB / {mem_total} MiB")
                        self.gpu_mem_percent_label.setText(f"{gpu_mem:.0f}%")
                        self.gpu_temp_label.setText("N/A")
                        gpu_shown = True
            except Exception:
                pass
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
        self.update_series(self.gpu_chart_view, self.gpu_history)
        
        # Processes
        process_count = len(psutil.pids())
        self.process_label.setText(str(process_count))

