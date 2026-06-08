from ui.graphs import MiniSparklineWidget


def create_sparkline(monitor, color: str):
    s = MiniSparklineWidget(color)
    s.setMinimumHeight(36)
    return s
