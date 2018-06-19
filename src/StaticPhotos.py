from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (QParallelAnimationGroup, QTimer, QCoreApplication, Qt, qsrand, QTime, QRectF, QPointF, pyqtSignal, QSize, QObject, pyqtProperty)
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPixmap, QFont, QPalette, QImage, QTransform)
from PyQt5.QtWidgets import (QWidget, QApplication, QGraphicsScene, QGraphicsView, QPushButton, QVBoxLayout, QTextEdit, QGridLayout, QGraphicsRectItem, QGraphicsTextItem, QSizePolicy, QGraphicsPixmapItem, QGraphicsItem)

import datetime
from PhotoFileManager import PhotoFileManager
from PhotoInfo import PhotoInfo
import json

class StaticPhotos(QGraphicsView):
    def __init__(self, photoBaseDir, validPhotoFileExts, photoDeltas, picChangeMs, parent=None):
        QGraphicsView.__init__(self, parent)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
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
        self.photoFileManager = PhotoFileManager(validPhotoFileExts, self.photoBaseDir, 7200.00, photoDeltas)
        self.photoFileManager.startPhotoListUpdate()
        self.userMovedBack = False

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
        print("Static Photos - starting")

    def stop(self):
        if self.picChgTimer is not None:
            self.picChgTimer.stop()
            print("Static Photos - stopping")
            # self.picChgTimer.disconnect(self.picChangeFn)
        self.photoFileManager.stop()

    def moveNext(self):
        self.nextPicItem()

    def movePrev(self):
        self.prevPicItem()
        self.userMovedBack = True

    def reshow(self):
        self.showImage()

    def getCurPhotoFilename(self):
        return self.photoFileManager.getCurPhotoFilename()

    def picChangeFn(self):
        # pass
        if self.userMovedBack:
            # Skip this update
            self.userMovedBack = False
        else:
            self.nextPicItem()
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

    def showImage(self):
        (newImg, newImgInfo) = self.loadImage()
        # return PicItem(Pixmap(QPixmap(newImg)), -1, -1, xFactor, yFactor, newImgInfo)
        self.scene.clear()
        imgSz = newImgInfo.imgSize
        self.setSceneRect(QRectF(0,0,imgSz.width(), imgSz.height()))
        pixMap = QPixmap.fromImage(newImg)
        # # pixMap.setWidth(self.width())
        pixMapItem = self.scene.addPixmap(pixMap)
        # pixMapItem.setPos(50,50)
        # self.fitInView(QRectF(0, 0, self.width(), self.height()), Qt.KeepAspectRatio)
        # Add caption
        caption = QGraphicsTextItem()
        caption.setDefaultTextColor(QColor(255,255,255))
        caption.setPos(self.width() * 1/8, self.height()*0.92)
        caption.setFont(QFont("Segoe UI", 30))
        caption.setTextWidth(self.width()*3/4)
        # caption.setPos(100, 100)
        # caption.setTextWidth(1500)
        # if newImgInfo.createDate is not None:
        #     caption.setPlainText(newImgInfo.createDate.format());
        # else:
        #     caption.setPlainText("Image is called bananas");
        # print("Tags", newImgInfo.tags)
        # tagStr = ""
        # for tag in newImgInfo.tags:
        #     if tag != "Duplicate":
        #         tagStr += (", " if len(tagStr) != 0 else "") + tag
        # if tagStr == "":
        #     tagStr = "NO TAGS"
        # captionStr = '<h1 style="text-align:center;width:100%">' + tagStr + '</h1>'
        # if newImgInfo.createDate is not None:
        #     print(newImgInfo.createDate.format())
        #     captionStr += '<BR><h2>' + newImgInfo.createDate.format() + '</h2>'

        captionStr = ""
        try:
            if newImgInfo.rating is not None:
                for i in range(newImgInfo.rating):
                    captionStr += "&#x2605;"
                for i in range(5-newImgInfo.rating):
                    captionStr += "&#x2606;"
            if newImgInfo.mainDate is not None:
                if len(captionStr) != 0:
                    captionStr += "  "
                captionStr += newImgInfo.mainDate.strftime("%d %b %Y")
        except Exception as excp:
            print("StaticPhotos: Cannot set caption")
        captionStr = '<div style="background-color:#000000">' + captionStr + "</div>"
        print(captionStr)
        caption.setHtml(captionStr)
        self.scene.addItem(caption)
        self.scene.update()

    def prevPicItem(self):
        if self.photoFileManager.getNumPhotos() == 0:
            return None
        self.photoFileManager.movePrev()
        # print ("Loaded photo", self.sourcePhotoList[self.curPhotoIdx], " w", finalImg.width(), " h", finalImg.height(), " facs", xFactor, yFactor)
        self.showImage()

    def nextPicItem(self):
        if self.photoFileManager.getNumPhotos() == 0:
            return None
        # print ("Loaded photo", self.sourcePhotoList[self.curPhotoIdx], " w", finalImg.width(), " h", finalImg.height(), " facs", xFactor, yFactor)
        self.photoFileManager.moveNext()
        self.showImage()

    def keyPressEvent(self, event): #QKeyEvent
        event.ignore()
        # print("keypressStaticPhotos", event.text(), event.key())
