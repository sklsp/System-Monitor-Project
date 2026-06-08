from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from ui.graphs import MiniSparklineWidget, GraphWidget

def create_chart(monitor, title, color, fixed_max=None, compact=False):
    container = QFrame()
    container.setObjectName('card')
    container.setStyleSheet(f"QFrame#card {{ background-color: {monitor.ui_panel}; border-radius: 10px; padding: 8px; }}")
    layout = QVBoxLayout(container)
    layout.setContentsMargins(8, 6, 8, 6)
    layout.setSpacing(6)
    title_label = QLabel(title)
    title_label.setStyleSheet(f"font-weight: 700; color: {monitor.ui_muted}; font-size: 12px;")
    layout.addWidget(title_label)

    if compact:
        spark = MiniSparklineWidget(color)
        spark.setMinimumHeight(36)
        layout.addWidget(spark)
        return container, spark, None
    else:
        graph_widget = GraphWidget(color, fixed_max=fixed_max)
        graph_widget.setMinimumHeight(140)
        layout.addWidget(graph_widget)
        return container, graph_widget, None


def update_series(chart_or_series, history):
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
