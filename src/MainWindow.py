from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (QTimer, QCoreApplication, Qt, qsrand, QTime, QRectF, QPointF, pyqtSignal, QSize, QPoint, QSettings, QVariant)
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPixmap, QFont, QPalette)
from PyQt5.QtWidgets import (QWidget, QApplication, QGraphicsScene, QGraphicsView, QLabel, QSplitter, QPushButton, QHBoxLayout,
                             QVBoxLayout, QTextEdit, QGridLayout, QGraphicsRectItem, QGraphicsTextItem, QSizePolicy, QListWidget, QListWidgetItem)

from AnimatedClock import AnimatedClock
from AnimatedCalendar import AnimatedCalendar
from StaticPhotos import StaticPhotos
from CaptionedPhotos import CaptionedPhotos
from WindowToolbar import WindowToolbar

class MainWindow(QWidget):
    def __init__(self, appConfig, projectorControl, parent=None):
        QWidget.__init__(self, parent)
        self._projectorControl = projectorControl
        # Frameless window
        self.setWindowFlags(Qt.FramelessWindowHint)
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

        # Toolbar
        self.windowToolbar = WindowToolbar(self.close, self)

        # Left pane of page
        self.leftPane = QSplitter(Qt.Vertical)
        self.leftPane.addWidget(self.clock)
        self.leftPane.addWidget(self.calendar)
        # Right pane of page
        self.rightPane = QSplitter(Qt.Vertical)
        self.rightPane.addWidget(self.windowToolbar)
        self.rightPane.addWidget(self.photos)
        # Splitter between left and right panes
        self.horzSplitter = QSplitter(Qt.Horizontal)
        self.horzSplitter.addWidget(self.leftPane)
        self.horzSplitter.addWidget(self.rightPane)
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.horzSplitter)
        self.setLayout(self.layout)

        # Remember the locations of the splitter bars to restore next time the program is run
        settings = QSettings("PhotoCalendar")
        settings.beginGroup("MainWindow")
        position = settings.value("Position", QVariant(QPoint(0, 0)))
        self.move(position)
        size = settings.value("Size", QVariant(QSize(1920, 1200)))
        self.resize(size)
        if settings.value("HorzSplitter") is not None:
            self.horzSplitter.restoreState(settings.value("HorzSplitter"))
            #print("Restoring horz", settings.value("HorzSplitter"))
        if settings.value("LeftPaneSplitter") is not None:
            self.leftPane.restoreState(settings.value("LeftPaneSplitter"))
            #print("Restoring left pane", settings.value("LeftPaneSplitter"))
        if settings.value("RightPaneSplitter") is not None:
            self.rightPane.restoreState(settings.value("RightPaneSplitter"))
            #print("Restoring right pane", settings.value("RightPaneSplitter"))
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

        # Start photo animation
        self.photos.start()

    def closeEvent(self, event):
        print("Main window close event")
        # Save layout settings
        settings = QSettings("PhotoCalendar")
        settings.beginGroup("MainWindow")
        curSize = self.size()
        settings.setValue("Size", QVariant(curSize))
        curPos = self.pos()
        settings.setValue("Position", QVariant(curPos))
        #settings.setValue("MainWindow/State", QVariant(self.saveState()))
        horzSplitterState = self.horzSplitter.saveState()
        #print("HorzSplitter save", horzSplitterState)
        settings.setValue("HorzSplitter", QVariant(horzSplitterState))
        leftPaneSplitterState = self.leftPane.saveState()
        settings.setValue("LeftPaneSplitter", QVariant(leftPaneSplitterState))
        #print("LeftPaneSplitter save", leftPaneSplitterState)
        rightPaneSplitterState = self.rightPane.saveState()
        settings.setValue("RightPaneSplitter", QVariant(rightPaneSplitterState))
        #print("RightPaneSplitter save", leftPaneSplitterState)
        settings.endGroup()
        # Stop the sub-elements
        self.calendar.stop()
        self.clock.stop()
        self.photos.stop()
        # Accept the close event
        event.accept()

    def resizeEvent(self, evt=None):
        xWindowSize = self.width()
        yWindowSize = self.height()
        print("MainWindow size x,y", xWindowSize, yWindowSize);

    def test(self):
        self._projectorControl.test()
