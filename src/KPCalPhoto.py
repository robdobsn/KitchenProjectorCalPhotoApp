
from PyQt5.QtCore import (Qt, qsrand, QTime)
from PyQt5.QtGui import (QBrush, QColor, QPainter)
from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView)

from AnimatedPhotos import AnimatedPhotos
from AnimatedClock import AnimatedClock
from AnimatedCalendar import AnimatedCalendar

from pymongo import MongoClient

import tempfile
import os
import psutil
import win32gui, win32con, win32process, win32api
import atexit
import sys

class View(QGraphicsView):
    def resizeEvent(self, event):
        super(View, self).resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.IgnoreAspectRatio)

def cleanUpOnExit():
    if os.path.exists(tempFilename):
        try:
            os.remove(tempFilename)
        except:
            print("Failed to clean up " + tempFilename)
    
def instanceAlreadyRunning(tempFilename):
    print ("Checking temp file")
    if os.path.exists(tempFilename):
        print("Temp file found")
        with open(tempFilename, 'r') as f:
            pid = int(f.read())
            f.close()
            print("PID " + str(pid))
            if psutil.pid_exists(pid):
                print ("proc is running " + str(pid))
                return (True, pid)
            else:
                try:
                    os.remove(tempFilename)
                except:
                    print("Failed to remove tmpfile " + tempFilename)
                print ("proc isn't running " + str(pid))
    with open(tempFilename, 'w') as f:
        f.write(str(os.getpid()))
        f.close()
        print ("Temp file written")
    return (False, 0)

def enumWinCb(hwnd, paramPID):
    if win32gui.IsWindowVisible(hwnd):
        (winThreadId, winProcId) = win32process.GetWindowThreadProcessId(hwnd)
        if winProcId == paramPID:
            #if 'Animated Tiles' in win32gui.GetWindowText(hwnd):
            #win32gui.MoveWindow(hwnd, 0, 0, 760, 500, True)
            win32gui.SetForegroundWindow(hwnd)
            print ("Setting to foreground ")
            
def setExistingInstanceToForeground(pid):
    win32gui.EnumWindows(enumWinCb, pid)

if __name__ == '__main__':

    mongoDbServer = "mongodb://macallan/"

    # Check if an instance is already running
    tempFilename = tempfile.gettempdir() + "\\rob_kpcalphoto_sentinel.txt";
    atexit.register(cleanUpOnExit)
    (isRunning, existingPid) = instanceAlreadyRunning(tempFilename)
    if isRunning:
        setExistingInstanceToForeground(existingPid)
        sys.exit(0)

    # Init the random number generator
    qsrand(QTime(0,0,0).secsTo(QTime.currentTime()))
    
    windowWidth = 1280
    windowHeight = 1024
    
    app = QApplication(sys.argv)

    scene = QGraphicsScene(0,0,windowWidth,windowHeight)

    photos = AnimatedPhotos(scene, "//macallan/photos/PhotosMain/", ["jpg"], maxCols=3, maxRows=4, borders=[0,0,0,750], xBetweenPics=5, yBetweenPics=5, animationSpeed=1.0, picChangeMs=5000)

    # Ui.
    view = View(scene)
    view.setWindowTitle("Animated Tiles")
    view.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
    view.setBackgroundBrush(QBrush(QColor("black")))
    view.setCacheMode(QGraphicsView.CacheBackground)
    view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.HighQualityAntialiasing)
    # view.showFullScreen()

    clockHeight = windowHeight/8
    clock = AnimatedClock(scene, widthClkTextArea=740, heightClkTextArea=clockHeight, borders=[0,0,0,0], updateSecs=1)

    mongoClient = MongoClient(mongoDbServer)
    calMgrDb = mongoClient.CalendarManager
    calFeedsRec = calMgrDb.CalConfig.find_one()
    cal_feeds = []
    if calFeedsRec is None or "calFeeds" not in calFeedsRec:
        print("Failed to find calendar config record")
    else:
        cal_feeds = calFeedsRec["calFeeds"]

    calendar = AnimatedCalendar(scene, widthCalTextArea=740, heightCalTextArea=1600-clockHeight, borders=[clockHeight,0,0,0], calFeeds=cal_feeds, calUpdateSecs=600) 
    
    photos.start()
    clock.start()
    calendar.start()

    retc = app.exec_()
    print ("Stopped")
    photos.stop()
    calendar.stop()
    sys.exit(retc)

