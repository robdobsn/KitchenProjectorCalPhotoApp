from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (QTimer, QCoreApplication, Qt, qsrand, QTime, QRectF, QPointF, pyqtSignal, QSize)
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPixmap, QFont, QPalette)
from PyQt5.QtWidgets import (QWidget, QApplication, QGraphicsScene, QGraphicsView, QPushButton, QVBoxLayout, QTextEdit, QGridLayout, QGraphicsRectItem, QGraphicsTextItem, QSizePolicy)
import time

class AnimatedClock(QGraphicsView):
    def __init__(self, parent=None):
        QGraphicsView.__init__(self, parent)
        self.updateSecs = 0.5
        # Border
        self.setLineWidth(0)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        # Size
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)
        # No scrollbars
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setBackgroundBrush(QColor("black"))
        # Text of clock
        self.textItem = QGraphicsTextItem()
        self.textItem.color = QColor(QColor("black"))
        self.textItem.setFont(QFont("Segoe UI", 80))
        self.textItem.setDefaultTextColor(QColor("white"))
        self.textItem.setHtml("")
        self.textItem.setZValue(20)
        self.scene.addItem(self.textItem)
        # Start ticking
        self.start()

    def sizeHint(self):
        return QSize(300, 150)

    def start(self):
        self.updateTimer = QTimer()
        self.updateTimer.setInterval(self.updateSecs * 990)
        self.updateTimer.timeout.connect(self.updateClock)
        self.updateTimer.start()
        print("Animated clock - starting")

    def stop(self):
        if self.updateTimer != None:
            self.updateTimer.stop()
        print("Animated clock - stopping")

    def updateClock(self):
        localtime = time.localtime()
        timeString = time.strftime("%H:%M:%S", localtime)
        self.textItem.setHtml(timeString)
        width = self.frameGeometry().width()
        self.textItem.setFont(QFont("Segoe UI", width / 8))
        self.textItem.update()

    def heightForWidth(self, width):
        return width * .32

