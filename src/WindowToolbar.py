# Toolbar with buttons for close, max/restore

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (QTimer, QCoreApplication, Qt, qsrand, QTime, QRectF, QPointF, pyqtSignal, QSize, QPoint, QSettings, QVariant)
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPixmap, QFont, QPalette)
from PyQt5.QtWidgets import (QWidget, QApplication, QGraphicsScene, QGraphicsView, QLabel, QSplitter, QPushButton, QHBoxLayout, QVBoxLayout, QTextEdit, QGridLayout, QGraphicsRectItem, QGraphicsTextItem, QSizePolicy, QListWidget, QListWidgetItem)

class WindowToolbar(QWidget):
    def __init__(self, closeWindowCallback, parent=None):
        QWidget.__init__(self, parent)
        self._parent = parent
        self._closeWindowCallback = closeWindowCallback
        self.setAutoFillBackground(True)
        palette = QPalette()
        palette.setColor(QPalette.Background, Qt.black)
        self.setPalette(palette)
        # Layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch(1)
        # self.filterOptions = FilterOptionsWidget()
        # # Collapsible layout
        # layout = QHBoxLayout()
        # layout.setContentsMargins(0, 0, 0, 0)
        # layout.setSpacing(0)
        # self.filterOptions.setFixedHeight(0)
        # layout.addWidget(self.filterOptions)
        # # Filter button
        # self.filterIcon = QtGui.QIcon('images/appbar.list.check.svg')
        # self.collapseButton = QPushButton()
        # self.collapseButton.setIcon(self.filterIcon)
        # self.collapseButton.clicked.connect(self.collapseToggle)
        # self.collapseButton.setIconSize(QtCore.QSize(50, 50))
        # self.collapseButton.setStyleSheet("background-color: black")
        # layout.addWidget(self.collapseButton, alignment=Qt.AlignTop)
        # Min/Max button
        self.maxIcon = QtGui.QIcon('images/appbar.max.svg')
        self.restoreIcon = QtGui.QIcon('images/appbar.restore.svg')
        self.minMaxButton = QPushButton()
        self.minMaxButton.setIcon(self.maxIcon)
        self.minMaxButton.clicked.connect(self.minMaxHandler)
        self.minMaxButton.setIconSize(QtCore.QSize(50, 50))
        self.minMaxButton.setStyleSheet("background-color: black")
        layout.addWidget(self.minMaxButton, alignment=Qt.AlignTop|Qt.AlignRight)
        # Exit button
        self.exitIcon = QtGui.QIcon('images/appbar.exit.svg')
        self.exitButton = QPushButton()
        self.exitButton.setIcon(self.exitIcon)
        self.exitButton.clicked.connect(self.exitHandler)
        self.exitButton.setIconSize(QtCore.QSize(50, 50))
        self.exitButton.setStyleSheet("background-color: black")
        layout.addWidget(self.exitButton, alignment=Qt.AlignTop|Qt.AlignRight)
        # Set layout
        self.setLayout(layout)

    # def collapseToggle(self):
    #     if self.filterOptions.height() < 10:
    #         self.filterOptions.setFixedHeight(200)
    #         # self.collapseButton.setText("Hide Filters")
    #     else:
    #         self.filterOptions.setFixedHeight(0)
    #         # self.collapseButton.setText("Show Filters")

    def exitHandler(self):
        self._closeWindowCallback()
        #self._parent.test()

    def minMaxHandler(self):
        if QApplication.topLevelWidgets()[0].isMaximized():
            print("Window going back to normal mode")
            [o.showNormal() and o.setFlags(0) for o in QApplication.topLevelWidgets()]
            self.minMaxButton.setIcon(self.maxIcon)
            self.minMaxButton.setIconSize(QtCore.QSize(50, 50))
            self.minMaxButton.show()
            # if self._parent is not None:
            #     self._parent.setWindowFlags(self._parent.windowFlags & ~Qt.FramelessWindowHint)
        else:
            print("Maximising window")
            [o.showMaximized() and o.setFlags(Qt.FramelessWindowHint) for o in QApplication.topLevelWidgets()]
            self.minMaxButton.setIcon(self.restoreIcon)
            self.minMaxButton.setIconSize(QtCore.QSize(50, 50))
            self.minMaxButton.show()
            # if self._parent is not None:
            #     self._parent.setWindowFlags(Qt.FramelessWindowHint)

    def keyPressEvent(self, event): #QKeyEvent
        event.ignore()