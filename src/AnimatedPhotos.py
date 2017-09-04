from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (QParallelAnimationGroup, QTimer, QCoreApplication, Qt, qsrand, QTime, QRectF, QPointF, pyqtSignal, QSize)
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPixmap, QFont, QPalette)
from PyQt5.QtWidgets import (QWidget, QApplication, QGraphicsScene, QGraphicsView, QPushButton, QVBoxLayout, QTextEdit, QGridLayout, QGraphicsRectItem, QGraphicsTextItem, QSizePolicy)

from PicManager import PicManager

class AnimatedPhotos(QGraphicsView):
    def __init__(self, photoBaseDir, validPhotoFileExts, maxCols, maxRows, borders, xBetweenPics, yBetweenPics, animationSpeed, picChangeMs, parent=None):
        QGraphicsView.__init__(self, parent)
        # Vars
        self.maxCols = maxCols
        self.maxRows = maxRows
        self.borders = borders
        self.xBetweenPics = xBetweenPics
        self.yBetweenPics = yBetweenPics
        self.animationSpeed = animationSpeed
        self.animationTimeoutMs = 15000
        self.picChangeMs = picChangeMs
        # Border
        self.setLineWidth(0)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        # Widget
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setBackgroundBrush(QColor("light green"))
        # Calc layout
        self.calcCellSize()
        self.animTimeout = QTimer()
        self.picManager = PicManager(self.scene, photoBaseDir, validPhotoFileExts, maxCols, maxRows, QSize(self.xCellSize, self.yCellSize), borders, xBetweenPics, yBetweenPics)
        # Class vars
        self.animationRunning = False
        self.curAnimationGroup = 0
        self.animationGroups = [None] * 2
        self.picChgTimer = None
        self.stepCount = 0

    def resizeEvent(self, evt=None):
        self.calcCellSize()
        self.picManager.resize(QSize(self.xCellSize, self.yCellSize))

    def calcCellSize(self):
        xWindowSize = self.width()
        yWindowSize = self.height()
        self.xCellSize = ((xWindowSize - self.borders[3] - self.borders[1] - self.xBetweenPics*(self.maxCols-1)) / self.maxCols)
        self.yCellSize = ((yWindowSize - self.borders[0] - self.borders[2] - self.yBetweenPics*(self.maxRows-1)) / self.maxRows)
    
    def start(self):
        self.animationRunning = True
        QTimer.singleShot(self.picChangeMs, self.stepAnimation)
        
    def stop (self):
        self.picManager.stop()
        self.animationRunning = False
        if self.picChgTimer != None:
            self.picChgTimer.stop()
        
    def setNextTransition(self):
#        print ("Anim Step ..........", self.stepCount)
        self.picManager.setupChange()
        self.picManager.addNewPhotosToScene()
        group = QParallelAnimationGroup()
        self.picManager.addInsertionAnimation(group)
#        self.picManager.instantInsert()
        self.picManager.addMovementAnimation(group)
#        self.picManager.instantMove()
#        self.picManager.addRemovalAnimation(group)
        self.picManager.instantRemove()
        group.finished.connect(self.animFinished)
        self.stepCount += 1
        return group

    def animFinished(self):
#        print ("AnimFinished")
        self.animTimeout.stop()
        
        self.picManager.completeChange()
        
        # Remove items from scene
        
        if not self.animationRunning:
            return
#        print("Restarting timer")
        self.picChgTimer = QTimer()
        self.picChgTimer.setInterval(self.picChangeMs)
        self.picChgTimer.setSingleShot(True)
        self.picChgTimer.timeout.connect(self.stepAnimation)
        self.picChgTimer.start()

    def stepAnimation(self):
        self.animationGroups[self.curAnimationGroup] = self.setNextTransition()
        self.animationGroups[self.curAnimationGroup].start()
        self.curAnimationGroup = 1 if self.curAnimationGroup == 0 else 0
#        print ("AnimStarting")
        self.animTimeout.setInterval(self.animationTimeoutMs)
        self.animTimeout.setSingleShot(True)
        self.animTimeout.timeout.connect(self.animationTimedOut)
        self.animTimeout.start()

    def animationTimedOut(self):
        try:
            self.ttt = self.ttt + 1
        except:
            self.ttt = 0
            
        print("Animation TimedOut", self.ttt)
        self.animTimeout.stop()
        self.animFinished()
        
