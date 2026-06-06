from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath, QFont
from PyQt5.QtCore import Qt, QRect


class GraphWidget(QWidget):
    def __init__(self, color="#4CAF50", fixed_max=None, value_suffix="%", parent=None):
        super().__init__(parent)
        self.history = []
        self.color = QColor(color)
        self.fixed_max = fixed_max
        self.value_suffix = value_suffix
        self.setMinimumHeight(160)

    def set_history(self, history):
        self.history = list(history)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # Background with rounded panel
        painter.setBrush(QColor(20, 20, 20))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 8, 8)

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

        # Draw subtle grid lines
        grid_pen = QPen(QColor(255, 255, 255, 18))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for i in range(1, 4):
            y = margin + i * (h / 4)
            painter.drawLine(margin, int(y), margin + w, int(y))

        # Build points
        points = []
        for i, v in enumerate(self.history):
            x = margin + (i / max(1, count - 1)) * w if count > 1 else margin + w
            normalized = (v - minv) / value_range
            y = margin + h - normalized * h
            points.append((x, y))

        # Draw smooth curve using QPainterPath
        if len(points) > 1:
            path = QPainterPath()
            path.moveTo(points[0][0], points[0][1])
            for i in range(1, len(points)):
                x0, y0 = points[i - 1]
                x1, y1 = points[i]
                mx = (x0 + x1) / 2
                path.quadTo(x0, y0, mx, (y0 + y1) / 2)
            path.lineTo(points[-1][0], points[-1][1])

            grad_color = QColor(self.color)
            grad_color.setAlpha(90)
            painter.fillPath(path, grad_color)

            pen = QPen(self.color)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawPath(path)

        # Draw a subtle marker for the latest point
        point_pen = QPen(self.color)
        point_pen.setWidth(3)
        painter.setPen(point_pen)
        x, y = points[-1]
        painter.drawEllipse(int(x) - 3, int(y) - 3, 6, 6)

        latest = self.history[-1]
        painter.setPen(QColor(230, 238, 243))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(
            QRect(margin + 6, margin + 2, 180, 18), Qt.AlignLeft, f"Now: {latest}{self.value_suffix}"
        )

        painter.setPen(QColor(160, 170, 180))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(QRect(margin, rect.height() - margin - 18, 100, 16), Qt.AlignLeft, "History")
        painter.drawText(
            QRect(rect.width() - margin - 140, rect.height() - margin - 18, 140, 16), Qt.AlignRight, f"Max: {maxv}{self.value_suffix}"
        )
