from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QRect


class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []
        self.setMinimumHeight(160)

    def set_history(self, history):
        self.history = list(history)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()
        painter.fillRect(rect, QColor(43, 43, 43))

        if not self.history:
            return

        margin = 6
        w = rect.width() - margin * 2
        h = rect.height() - margin * 2
        points = []
        count = len(self.history)
        maxv = max(self.history) if self.history else 100
        maxv = max(maxv, 1)
        for i, v in enumerate(self.history):
            x = margin + (i / max(1, count - 1)) * w if count > 1 else margin + w
            y = margin + h - (v / maxv) * h
            points.append((x, y))

        pen = QPen(QColor(76, 175, 80))
        pen.setWidth(2)
        painter.setPen(pen)
        for i in range(1, len(points)):
            x1, y1 = points[i - 1]
            x2, y2 = points[i]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # draw latest value text
        latest = self.history[-1]
        painter.setPen(Qt.white)
        painter.drawText(QRect(8, 8, 200, 20), Qt.AlignLeft, f"{latest}%")
