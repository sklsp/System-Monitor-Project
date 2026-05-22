from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath, QFont
from PyQt5.QtCore import Qt, QRect


class GraphWidget(QWidget):
    def __init__(self, color="#4CAF50", fixed_max=None, parent=None):
        super().__init__(parent)
        self.history = []
        self.color = QColor(color)
        self.fixed_max = fixed_max
        self.setMinimumHeight(160)

    def set_history(self, history):
        self.history = list(history)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # Background
        painter.fillRect(rect, QColor(34, 34, 34))

        if not self.history:
            return

        margin = 8
        w = rect.width() - margin * 2
        h = rect.height() - margin * 2
        count = len(self.history)
        if self.fixed_max is not None and self.fixed_max > 0:
            maxv = self.fixed_max
            minv = 0
        else:
            maxv = max(self.history) if self.history else 100
            minv = min(self.history) if self.history else 0
            minv = min(minv, 0)
        maxv = max(maxv, 1)
        value_range = maxv - minv if maxv != minv else maxv or 1

        # Draw grid lines
        grid_pen = QPen(QColor(80, 80, 80, 120))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for i in range(1, 4):
            y = margin + i * (h / 4)
            painter.drawLine(margin, int(y), margin + w, int(y))
        for i in range(1, 4):
            x = margin + i * (w / 4)
            painter.drawLine(int(x), margin, int(x), margin + h)

        # Build points
        points = []
        for i, v in enumerate(self.history):
            x = margin + (i / max(1, count - 1)) * w if count > 1 else margin + w
            normalized = (v - minv) / value_range
            y = margin + h - normalized * h
            points.append((x, y))

        # Draw fill below line
        if len(points) > 1:
            fill_path = QPainterPath()
            fill_path.moveTo(points[0][0], rect.height() - margin)
            for x, y in points:
                fill_path.lineTo(x, y)
            fill_path.lineTo(points[-1][0], rect.height() - margin)
            fill_path.closeSubpath()
            fill_color = QColor(self.color)
            fill_color.setAlpha(80)
            painter.fillPath(fill_path, fill_color)

        # Draw line
        pen = QPen(self.color)
        pen.setWidth(2)
        painter.setPen(pen)
        for i in range(1, len(points)):
            x1, y1 = points[i - 1]
            x2, y2 = points[i]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Draw points
        point_pen = QPen(Qt.white)
        point_pen.setWidth(3)
        painter.setPen(point_pen)
        for x, y in points:
            painter.drawPoint(int(x), int(y))

        latest = self.history[-1]
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(QRect(margin + 4, margin + 2, 120, 18), Qt.AlignLeft, f"Now: {latest}%")

        painter.setPen(QColor(180, 180, 180))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(QRect(margin, rect.height() - margin - 18, 100, 16), Qt.AlignLeft, "History")
        painter.drawText(QRect(rect.width() - margin - 90, rect.height() - margin - 18, 90, 16), Qt.AlignRight, f"Max: {maxv}%")
