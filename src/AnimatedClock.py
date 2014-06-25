from PyQt5.QtCore import (QTimer, QPointF)
from PyQt5.QtGui import (QColor, QFont, QBrush)
from PyQt5.QtWidgets import (QGraphicsTextItem, QGraphicsRectItem)

import threading
import time
from datetime import datetime
from datetime import timedelta

class AnimatedClock():
    updateTimer = None
    calDataLock = threading.Lock()
    calDataUpdated = False
    curCalendars = None
    
    def __init__(self, scene, widthClkTextArea, heightClkTextArea, borders, updateSecs):
        self.masterScene = scene
        self.widthClkTextArea = widthClkTextArea
        self.heightClkTextArea = heightClkTextArea
        self.borders = borders
        self.updateSecs = updateSecs
        # Background
        self.textBkgd = QGraphicsRectItem(0, 0, self.widthClkTextArea, self.heightClkTextArea)
        self.textBkgd.setPos(self.borders[3], self.borders[0])
        self.textBkgd.setBrush(QColor("light green"))
        self.textBkgd.setZValue(10)
        scene.addItem(self.textBkgd)
        # Text Item
        self.textItem = QGraphicsTextItem()
        self.textItem.setFont(QFont("Segoe UI", 80))
        self.textItem.setDefaultTextColor(QColor("black"))
        self.textItem.setPos(QPointF(self.borders[3]+10,self.borders[0]+5))
        self.textItem.setHtml("<B>Clock</B>")
        self.textItem.setZValue(20)
        self.textItem.setTextWidth(self.widthClkTextArea-20)
        scene.addItem(self.textItem)
        
    def start(self):
        self.updateTimer = QTimer()
        self.updateTimer.setInterval(self.updateSecs * 1000)
        self.updateTimer.timeout.connect(self.updateClock)
        self.updateTimer.start()

    def stop (self):
        if self.updateTimer != None:
            self.updateTimer.stop()
    
    def updateClock(self):
        localtime = time.localtime()
#        dateString  = time.strftime("%a %d %b %Y", localtime)
        timeString  = time.strftime("%H:%M:%S", localtime)
        self.textItem.setHtml(timeString)
#        self.textItem.setTextWidth(self.widthCalTextArea-20)
        self.textItem.update()
