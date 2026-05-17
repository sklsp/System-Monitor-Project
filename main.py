import sys
import subprocess
import psutil
try:
    import GPUtil
except ModuleNotFoundError:
    GPUtil = None
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QProgressBar, QTabWidget
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont


class SystemMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Monitor")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")
        
        # Initialize data storage for charts
        self.cpu_history = []
        self.memory_history = []
        self.max_history = 60
        self.prev_disk_io = psutil.disk_io_counters()
        
        self.init_ui()
        
        # Timer for updating info
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_system_info)
        self.timer.start(1000)  # Update every 1 second
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel("System Monitor")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Create tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #555; }
            QTabBar::tab { background-color: #3b3b3b; color: #fff; padding: 8px 20px; }
            QTabBar::tab:selected { background-color: #555; }
        """)
        
        # Overview Tab
        overview_widget = self.create_overview_tab()
        tabs.addTab(overview_widget, "Overview")
        
        # Details Tab
        details_widget = self.create_details_tab()
        tabs.addTab(details_widget, "Details")
        
        main_layout.addWidget(tabs)
        central_widget.setLayout(main_layout)
        
    def create_overview_tab(self):
        widget = QWidget()
        layout = QGridLayout()
        layout.setSpacing(15)
        
        # CPU Info
        layout.addWidget(QLabel("CPU Usage"), 0, 0)
        self.cpu_label = QLabel("0%")
        self.cpu_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.cpu_label, 0, 1)
        
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
        
        # Disk Write Info
        layout.addWidget(QLabel("Disk Writing"), 6, 0)
        self.disk_label = QLabel("0%")
        self.disk_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.disk_label, 6, 1)
        
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
        
        # Process Info
        layout.addWidget(QLabel("Process Count"), 8, 0)
        self.process_label = QLabel("0")
        self.process_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.process_label, 8, 1)
        
        widget.setLayout(layout)
        return widget
        
    def create_details_tab(self):
        widget = QWidget()
        layout = QGridLayout()
        layout.setSpacing(10)
        
        # CPU Details
        layout.addWidget(QLabel("CPU Info:"), 0, 0)
        self.cpu_count_label = QLabel()
        layout.addWidget(self.cpu_count_label, 0, 1)
        
        self.cpu_freq_label = QLabel()
        layout.addWidget(self.cpu_freq_label, 1, 1)
        
        # Memory Details
        layout.addWidget(QLabel("Memory Info:"), 2, 0)
        self.memory_total_label = QLabel()
        layout.addWidget(self.memory_total_label, 2, 1)
        
        self.memory_available_label = QLabel()
        layout.addWidget(self.memory_available_label, 3, 1)
        
        # Disk Details
        layout.addWidget(QLabel("Disk Info:"), 4, 0)
        self.disk_total_label = QLabel()
        layout.addWidget(self.disk_total_label, 4, 1)
        
        self.disk_free_label = QLabel()
        layout.addWidget(self.disk_free_label, 5, 1)
        
        # GPU Details
        layout.addWidget(QLabel("GPU Info:"), 6, 0)
        self.gpu_name_label = QLabel()
        layout.addWidget(self.gpu_name_label, 6, 1)
        
        self.gpu_load_label = QLabel()
        layout.addWidget(self.gpu_load_label, 7, 1)
        
        self.gpu_mem_label = QLabel()
        layout.addWidget(self.gpu_mem_label, 8, 1)
        
        # Network Details
        layout.addWidget(QLabel("Network Info:"), 9, 0)
        self.network_sent_label = QLabel()
        layout.addWidget(self.network_sent_label, 9, 1)
        
        self.network_recv_label = QLabel()
        layout.addWidget(self.network_recv_label, 10, 1)
        
        widget.setLayout(layout)
        return widget
        
    def update_system_info(self):
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_label.setText(f"{cpu_percent}%")
        self.cpu_bar.setValue(int(cpu_percent))
        
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0
        self.cpu_count_label.setText(f"Cores: {cpu_count}")
        self.cpu_freq_label.setText(f"Frequency: {cpu_freq:.0f} MHz")
        
        # Memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        self.memory_label.setText(f"{memory_percent}%")
        self.memory_bar.setValue(int(memory_percent))
        
        total_gb = memory.total / (1024**3)
        available_gb = memory.available / (1024**3)
        used_gb = memory.used / (1024**3)
        self.memory_total_label.setText(f"Total: {total_gb:.2f} GB")
        self.memory_available_label.setText(f"Used: {used_gb:.2f} GB / Available: {available_gb:.2f} GB")
        
        # Disk write percent
        disk_io = psutil.disk_io_counters()
        write_bytes_delta = 0
        if self.prev_disk_io:
            write_bytes_delta = disk_io.write_bytes - self.prev_disk_io.write_bytes
        self.prev_disk_io = disk_io
        write_mbps = write_bytes_delta / (1024 ** 2)
        max_write_mbps = 10.0  # 10 MB/s maps to 100%
        disk_write_percent = int(min(max((write_mbps / max_write_mbps) * 100, 0), 100))
        self.disk_label.setText(f"{disk_write_percent}%")
        self.disk_bar.setValue(disk_write_percent)
        self.disk_bar.setFormat(f"{write_mbps:.2f} MB/s")
        
        disk = psutil.disk_usage('/')
        total_gb = disk.total / (1024**3)
        used_gb = disk.used / (1024**3)
        free_gb = disk.free / (1024**3)
        self.disk_total_label.setText(f"Total: {total_gb:.2f} GB")
        self.disk_free_label.setText(f"Used: {used_gb:.2f} GB / Free: {free_gb:.2f} GB")
        
        # GPU
        gpu_shown = False
        if GPUtil is not None:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_load = gpu.load * 100
                    gpu_mem = gpu.memoryUtil * 100
                    self.gpu_label.setText(f"{gpu_load:.0f}%")
                    self.gpu_bar.setValue(int(gpu_load))
                    self.gpu_bar.setFormat(f"{gpu_mem:.0f}% mem")
                    self.gpu_name_label.setText(f"{gpu.name}")
                    self.gpu_load_label.setText(f"Load: {gpu_load:.0f}%")
                    self.gpu_mem_label.setText(f"Memory: {gpu.memoryUsed:.0f} MiB / {gpu.memoryTotal:.0f} MiB")
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
                        self.gpu_bar.setValue(int(gpu_load))
                        self.gpu_bar.setFormat(f"{gpu_mem:.0f}% mem")
                        self.gpu_name_label.setText(name)
                        self.gpu_load_label.setText(f"Load: {gpu_load:.0f}%")
                        self.gpu_mem_label.setText(f"Memory: {mem_used} MiB / {mem_total} MiB")
                        gpu_shown = True
            except Exception:
                pass
        if not gpu_shown:
            self.gpu_label.setText("N/A")
            self.gpu_bar.setValue(0)
            self.gpu_bar.setFormat("No GPU")
            self.gpu_name_label.setText("GPU info unavailable")
            self.gpu_load_label.setText("")
            self.gpu_mem_label.setText("")
        
        # Processes
        process_count = len(psutil.pids())
        self.process_label.setText(str(process_count))
        
        # Network
        net_io = psutil.net_io_counters()
        sent_mb = net_io.bytes_sent / (1024**2)
        recv_mb = net_io.bytes_recv / (1024**2)
        self.network_sent_label.setText(f"Sent: {sent_mb:.2f} MB")
        self.network_recv_label.setText(f"Received: {recv_mb:.2f} MB")


def main():
    app = QApplication(sys.argv)
    monitor = SystemMonitor()
    monitor.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
