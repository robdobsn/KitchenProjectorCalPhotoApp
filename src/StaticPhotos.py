from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (QParallelAnimationGroup, QTimer, QCoreApplication, Qt, qsrand, QTime, QRectF, QPointF, pyqtSignal, QSize, QObject, pyqtProperty)
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPixmap, QFont, QPalette, QImage, QTransform)
from PyQt5.QtWidgets import (QWidget, QApplication, QGraphicsScene, QGraphicsView, QPushButton, QVBoxLayout, QTextEdit, QGridLayout, QGraphicsRectItem, QGraphicsTextItem, QSizePolicy, QGraphicsPixmapItem, QGraphicsItem)

import datetime
from PhotoFileManager import PhotoFileManager
from PhotoInfo import PhotoInfo

class StaticPhotos(QGraphicsView):
    def __init__(self, photoBaseDir, validPhotoFileExts, picChangeMs, parent=None):
        QGraphicsView.__init__(self, parent)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # Vars
        self.picChangeMs = picChangeMs
        self.photoBaseDir = photoBaseDir
        # Widget
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setBackgroundBrush(QColor("black"))
        self.setLineWidth(0)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        # Class vars
        self.picChgTimer = None
        self.photoFileManager = PhotoFileManager(validPhotoFileExts, self.photoBaseDir, 7200.00)
        self.photoFileManager.startPhotoListUpdate()

    # def sizeHint(self):
    #     return QSize(600, 400)

    def resizeEvent(self, evt=None):
        xWindowSize = self.width()
        yWindowSize = self.height()
        pass

    def start(self):
        self.picChgTimer = QTimer()
        self.picChgTimer.setInterval(self.picChangeMs)
        self.picChgTimer.setSingleShot(True)
        self.picChgTimer.timeout.connect(self.picChangeFn)
        self.picChgTimer.start()
        # self.picChangeFn()

    def stop(self):
        if self.picChgTimer is not None:
            self.picChgTimer.stop()
            print("Stopping photo update timer")
            # self.picChgTimer.disconnect(self.picChangeFn)
        self.photoFileManager.stop()

    def picChangeFn(self):
        # pass
        self.getNextPicItem()
        self.picChgTimer.setInterval(self.picChangeMs)
        self.picChgTimer.start()

    def loadImage(self):
        self.newImg = QImage()
        self.newImg.load(self.photoFileManager.getCurPhotoFilename())
        self.newImgInfo = self.photoFileManager.getCurPhotoInfo()
        transform = QTransform()
        transform.rotate(self.newImgInfo.rotationAngle)
        self.interImg = self.newImg.transformed(transform, Qt.SmoothTransformation)
        # xReqdSize = self.cellSize.width() * xFactor + self.xBetweenPics * (xFactor-1)
        # yReqdSize = self.cellSize.height() * yFactor + self.yBetweenPics * (yFactor-1)
        self.inter2Img = self.interImg.scaled(QSize(self.width(),self.height()),
                                                    Qt.KeepAspectRatio, Qt.SmoothTransformation)
        # finalImg = interImg.copy(0,0,xReqdSize,yReqdSize)
        # print("XY Size", xFactor, yFactor, xReqdSize,yReqdSize)
        return self.inter2Img, self.newImgInfo


    def getNextPicItem(self):
        if self.photoFileManager.getNumPhotos() == 0:
            return None
        (newImg, newImgInfo) = self.loadImage()
        # print ("Loaded photo", self.sourcePhotoList[self.curPhotoIdx], " w", finalImg.width(), " h", finalImg.height(), " facs", xFactor, yFactor)
        self.photoFileManager.moveNext()
        # return PicItem(Pixmap(QPixmap(newImg)), -1, -1, xFactor, yFactor, newImgInfo)
        self.scene.clear()
        imgSz = newImgInfo.imgSize
        pixMap = QPixmap.fromImage(newImg)
        # pixMap.setWidth(self.width())
        pixMapItem = self.scene.addPixmap(pixMap)
        pixMapItem.setPos(50,50)
        # self.fitInView(QRectF(0, 0, self.width(), self.height()), Qt.KeepAspectRatio)
        # Add caption
        caption = QGraphicsTextItem()
        caption.setDefaultTextColor(QColor(255,255,255))
        caption.setPos(0, self.height()-200);
        caption.setTextWidth(self.width());
        caption.setHtml('<h1 style="text-align:center;width:100%">Things are looking up</h1>');
        self.scene.addItem(caption)
        self.scene.update()
