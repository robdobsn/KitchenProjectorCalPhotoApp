from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (QTimer, QCoreApplication, Qt, qsrand, QTime, QRectF, QPointF, pyqtSignal, QSize, QPoint, QSettings, QVariant)
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPixmap, QFont, QPalette)
from PyQt5.QtWidgets import (QWidget, QApplication, QGraphicsScene, QGraphicsView, QLabel, QSplitter, QPushButton, QHBoxLayout,
                             QVBoxLayout, QTextEdit, QGridLayout, QGraphicsRectItem, QGraphicsTextItem, QSizePolicy, QListWidget, QListWidgetItem)

from AnimatedClock import AnimatedClock
from AnimatedCalendar import AnimatedCalendar
from StaticPhotos import StaticPhotos
from CaptionedPhotos import CaptionedPhotos

# class ImageWidget(QGraphicsView):
#     def __init__(self, parent=None):
#         QGraphicsView.__init__(self, parent)
#         self.scene = QGraphicsScene()
#         self.setScene(self.scene)
#         self.setLineWidth(0)
#         self.setFrameShape(QtWidgets.QFrame.NoFrame)

class MainWindow(QWidget):
    def __init__(self, appConfig, parent=None):
        QWidget.__init__(self, parent)
        # Frameless window
        # self.setWindowFlags(Qt.FramelessWindowHint)
        # Background to black
        self.setAutoFillBackground(True)
        palette = QPalette()
        palette.setColor(QPalette.Background, Qt.black)
        self.setPalette(palette)
        # Clock
        self.clock = AnimatedClock()
        # Calendar
        self.calendar = AnimatedCalendar(calUpdateSecs=600, mongoDbServer=appConfig["calendarConfigSource"])
        # Image
        # self.photos = AnimatedPhotos("//macallan/photos/PhotosMain/", ["jpg"], maxCols=3, maxRows=4, borders=[0,0,0,0], xBetweenPics=5, yBetweenPics=5, animationSpeed=1.0, picChangeMs=5000)
        self.photos = StaticPhotos("//macallan/photos/PhotosMain/", ["jpg"], picChangeMs=5000)
        #self.photos = CaptionedPhotos("//macallan/photos/PhotosMain/", ["jpg"], picChangeMs=5000)

        self.vertSplitter = QSplitter(Qt.Vertical)
        self.vertSplitter.addWidget(self.clock)
        self.vertSplitter.addWidget(self.calendar)

        self.horzSplitter = QSplitter(Qt.Horizontal)
        self.horzSplitter.addWidget(self.vertSplitter)
        self.horzSplitter.addWidget(self.photos)

        hbox = QHBoxLayout(self)
        hbox.addWidget(self.horzSplitter)
        self.setLayout(hbox)

        settings = QSettings("PhotoCalendar")
        settings.beginGroup("MainWindow")
        size = settings.value("Size", QVariant(QSize(1920, 1200)))
        self.resize(size)
        # settings.setValue("Position", QVariant(QPoint(299,200)))
        # settings.sync()
        position = settings.value("Position", QVariant(QPoint(0, 0)))
        self.move(position)
        #        self.restoreState(settings.value("MainWindow/State").toByteArray())
        if settings.value("HorzSplitter") is not None:
            self.horzSplitter.restoreState(settings.value("HorzSplitter"))
        if settings.value("VertSplitter") is not None:
            self.vertSplitter.restoreState(settings.value("VertSplitter"))
        settings.endGroup()

        # Start rotating photos
        self.photos.start()

        # # Grid layout
        # layout = QGridLayout()
        # # layout.setContentsMargins(0,0,0,0)
        # layout.setSpacing(0)
        # layout.addWidget(self.clock, 0, 0)
        # layout.addWidget(self.calendar, 1, 0)
        # layout.addWidget(self.photos, 0, 1, 2, 1)
        # layout.setColumnStretch(0, 1)
        # layout.setColumnStretch(1, 2.5)
        # self.setLayout(layout)
        # # Start photo animation
        # self.photos.start()

    def closeEvent(self, event):
        print("Main window close event")
        self.calendar.stop()
        self.clock.stop()
        self.photos.stop()
        event.accept()

    def resizeEvent(self, evt=None):
        xWindowSize = self.width()
        yWindowSize = self.height()
        print("MainWindow size x,y", xWindowSize, yWindowSize);
