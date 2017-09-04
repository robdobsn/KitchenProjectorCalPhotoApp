from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (QTimer, QCoreApplication, Qt, qsrand, QTime, QRectF, QPointF, pyqtSignal, QSize)
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPixmap, QFont, QPalette)
from PyQt5.QtWidgets import (QWidget, QApplication, QGraphicsScene, QGraphicsView, QPushButton, QVBoxLayout, QTextEdit,
                             QGridLayout, QGraphicsRectItem, QGraphicsTextItem, QSizePolicy)
from AnimatedClock import AnimatedClock
from AnimatedCalendar import AnimatedCalendar
from AnimatedPhotos import AnimatedPhotos

class ImageWidget(QGraphicsView):
    def __init__(self, parent=None):
        QGraphicsView.__init__(self, parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setLineWidth(0)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

class MainWindow(QWidget):
    def __init__(self, mongoDbServer, parent=None):
        QWidget.__init__(self, parent)
        # Border around all widgets
        self.setAutoFillBackground(True)
        palette = QPalette()
        palette.setColor(QPalette.Background, Qt.white)
        self.setPalette(palette)
        # Clock
        self.clock = AnimatedClock()
        # Calendar
        self.calendar = AnimatedCalendar(calUpdateSecs=600, mongoDbServer=mongoDbServer)
        # Image
        self.photos = AnimatedPhotos("//macallan/photos/PhotosMain/", ["jpg"], maxCols=3, maxRows=4, borders=[0,0,0,0], xBetweenPics=5, yBetweenPics=5, animationSpeed=1.0, picChangeMs=5000)
        # Grid layout
        layout = QGridLayout()
        # layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        layout.addWidget(self.clock, 0, 0)
        layout.addWidget(self.calendar, 1, 0)
        layout.addWidget(self.photos, 0, 1, 2, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2.5)
        self.setLayout(layout)
        # Start photo animation
        self.photos.start()

    def closeEvent(self, event):
        print("Main window close event")
        self.calendar.stop()
        self.clock.stop()
        self.photos.stop()
        event.accept()
