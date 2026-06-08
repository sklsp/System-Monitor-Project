"""Gaming dashboard tab."""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QCheckBox,
    QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.graphs import GraphWidget


class GamingTab(QWidget):
    def __init__(self, on_top_toggle=None):
        super().__init__()
        self._on_top_toggle = on_top_toggle
        self.ping_history: list[float] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QHBoxLayout()
        self.status_badge = QLabel("DESKTOP")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setStyleSheet(
            "background-color: #555; color: #fff; font-weight: bold; "
            "padding: 6px 14px; border-radius: 6px;"
        )
        header.addWidget(self.status_badge)
        header.addStretch()
        self.always_on_top_cb = QCheckBox("Altijd bovenaan (overlay)")
        self.always_on_top_cb.setStyleSheet("color: #ddd;")
        if self._on_top_toggle:
            self.always_on_top_cb.toggled.connect(self._on_top_toggle)
        header.addWidget(self.always_on_top_cb)
        layout.addLayout(header)

        self.active_game_label = QLabel("Actief venster: —")
        self.active_game_label.setWordWrap(True)
        self.active_game_label.setStyleSheet("font-size: 13px; color: #ccc;")
        layout.addWidget(self.active_game_label)

        self.process_label = QLabel("")
        self.process_label.setStyleSheet("font-size: 11px; color: #999;")
        layout.addWidget(self.process_label)

        self.gpu_summary_label = QLabel("")
        self.gpu_summary_label.setStyleSheet("font-size: 12px; color: #ccc;")
        layout.addWidget(self.gpu_summary_label)

        layout.addLayout(self._create_stat_row())

        info = QGridLayout()
        info.addWidget(QLabel("Bottleneck:"), 0, 0)
        self.bottleneck_label = QLabel("—")
        self.bottleneck_label.setStyleSheet("color: #ffeb3b; font-weight: bold;")
        info.addWidget(self.bottleneck_label, 0, 1)
        info.addWidget(QLabel("Detail:"), 1, 0)
        self.bottleneck_detail_label = QLabel("—")
        self.bottleneck_detail_label.setWordWrap(True)
        info.addWidget(self.bottleneck_detail_label, 1, 1)
        layout.addLayout(info)

        self.alerts_label = QLabel("")
        self.alerts_label.setWordWrap(True)
        self.alerts_label.setStyleSheet(
            "background-color: #3a2a2a; color: #ff8a80; padding: 8px; border-radius: 6px;"
        )
        layout.addWidget(self.alerts_label)

        peaks_title = QLabel("Session peaks (sinds start)")
        peaks_title.setStyleSheet("font-weight: bold; margin-top: 4px;")
        layout.addWidget(peaks_title)
        self.peaks_label = QLabel("—")
        self.peaks_label.setStyleSheet("color: #bbb; font-size: 12px;")
        layout.addWidget(self.peaks_label)

        ping_row = QHBoxLayout()
        self.ping_detail_label = QLabel("Ping: —")
        ping_row.addWidget(self.ping_detail_label)
        ping_row.addStretch()
        layout.addLayout(ping_row)

        self.ping_graph = GraphWidget("#00BCD4", fixed_max=150, value_suffix=" ms")
        self.ping_graph.setMinimumHeight(120)
        layout.addWidget(self.ping_graph)

        top_title = QLabel("Top processen (CPU)")
        top_title.setStyleSheet("font-weight: bold;")
        layout.addWidget(top_title)
        self.top_processes_label = QLabel("—")
        self.top_processes_label.setStyleSheet("color: #ccc; font-size: 12px;")
        self.top_processes_label.setWordWrap(True)
        layout.addWidget(self.top_processes_label)
        layout.addStretch()

    def _create_stat_row(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(10)
        specs = [
            ("CPU", "#4CAF50", "cpu_card"),
            ("GPU", "#9C27B0", "gpu_card"),
            ("RAM", "#2196F3", "ram_card"),
            ("VRAM", "#E91E63", "vram_card"),
            ("Ping", "#00BCD4", "ping_card"),
        ]
        for index, (title, color, attr) in enumerate(specs):
            frame = QFrame()
            frame.setStyleSheet(
                "QFrame { background-color: #333; border: 1px solid #555; border-radius: 8px; }"
            )
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(12, 10, 12, 10)
            heading = QLabel(title)
            heading.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
            value = QLabel("—")
            value.setFont(QFont("Arial", 18, QFont.Bold))
            value.setAlignment(Qt.AlignCenter)
            fl.addWidget(heading)
            fl.addWidget(value)
            setattr(self, attr, value)
            grid.addWidget(frame, 0, index)
        return grid

    def update_metrics(self, metrics: dict) -> None:
        fg = metrics.get("foreground")
        if fg and fg.is_game:
            self.status_badge.setText("IN GAME")
            self.status_badge.setStyleSheet(
                "background-color: #1b5e20; color: #fff; font-weight: bold; "
                "padding: 6px 14px; border-radius: 6px;"
            )
        else:
            self.status_badge.setText("DESKTOP")
            self.status_badge.setStyleSheet(
                "background-color: #555; color: #fff; font-weight: bold; "
                "padding: 6px 14px; border-radius: 6px;"
            )

        title = fg.title if fg else "—"
        self.active_game_label.setText(f"Actief venster: {title}")
        if fg:
            self.process_label.setText(f"Proces: {fg.process_name}")

        # GPU short summary for gaming overlay
        gpu_model = metrics.get('gpu_model')
        core_clock = metrics.get('core_clock')
        gpu_temp = metrics.get('gpu_temp')
        power_draw = metrics.get('power_draw')
        if gpu_model:
            parts = [gpu_model]
            if core_clock:
                parts.append(f"{core_clock:.0f} MHz")
            if gpu_temp is not None:
                parts.append(f"{gpu_temp:.0f}°C")
            if power_draw is not None:
                parts.append(f"{power_draw:.1f} W")
            self.gpu_summary_label.setText(" · ".join(parts))
        else:
            self.gpu_summary_label.setText("")

        self.cpu_card.setText(f"{metrics.get('cpu_percent', 0):.0f}%")
        self.gpu_card.setText(f"{metrics.get('gpu_percent', 0):.0f}%")
        self.ram_card.setText(f"{metrics.get('ram_percent', 0):.0f}%")
        vram = metrics.get("vram_percent")
        self.vram_card.setText(f"{vram:.0f}%" if vram is not None else "N/A")

        ping_avg = metrics.get("ping_avg")
        self.ping_card.setText(f"{ping_avg:.0f} ms" if ping_avg is not None else "—")

        bottleneck = metrics.get("bottleneck")
        if bottleneck:
            self.bottleneck_label.setText(bottleneck.label)
            self.bottleneck_detail_label.setText(bottleneck.detail)

        alerts = metrics.get("alerts") or []
        if alerts:
            self.alerts_label.setText("⚠ " + " · ".join(alerts))
            self.alerts_label.setStyleSheet(
                "background-color: #3a2a2a; color: #ff8a80; padding: 8px; border-radius: 6px;"
            )
        else:
            self.alerts_label.setText("Geen waarschuwingen — prestaties zien er goed uit.")
            self.alerts_label.setStyleSheet(
                "background-color: #2a3a2a; color: #a5d6a7; padding: 8px; border-radius: 6px;"
            )

        peaks = metrics.get("peaks") or {}
        cpu_temp_peak = peaks.get("cpu_temp", 0)
        gpu_temp_peak = peaks.get("gpu_temp", 0)
        self.peaks_label.setText(
            f"CPU {peaks.get('cpu', 0):.0f}% · GPU {peaks.get('gpu', 0):.0f}% · "
            f"RAM {peaks.get('ram', 0):.0f}% · "
            f"CPU temp {cpu_temp_peak:.0f}°C · GPU temp {gpu_temp_peak:.0f}°C"
        )

        ping_results = metrics.get("ping_results") or {}
        parts = [
            f"{name}: {lat:.0f} ms" if lat is not None else f"{name}: —"
            for name, lat in ping_results.items()
        ]
        self.ping_detail_label.setText("Ping · " + " · ".join(parts) if parts else "Ping: —")

        if ping_avg is not None:
            self.ping_history.append(ping_avg)
            self.ping_history = self.ping_history[-30:]
            self.ping_graph.set_history(self.ping_history)

        top_procs = metrics.get("top_processes") or []
        if top_procs:
            lines = [f"{name} — {cpu:.1f}%" for name, cpu in top_procs]
            self.top_processes_label.setText("\n".join(lines))
        else:
            self.top_processes_label.setText("Geen data")
