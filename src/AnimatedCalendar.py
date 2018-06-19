from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (QTimer, QCoreApplication, Qt, qsrand, QTime, QRectF, QPointF, pyqtSignal, QSize)
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPixmap, QFont, QPalette)
from PyQt5.QtWidgets import (QWidget, QApplication, QGraphicsScene, QGraphicsView, QPushButton, QVBoxLayout, QTextEdit, QGridLayout, QGraphicsRectItem, QGraphicsTextItem, QSizePolicy)

import threading
import time
import requests
from datetime import datetime

class CalendarUpdateThread(threading.Thread):
    def __init__(self, parent, calUpdatePeriodSecs, calServerUrl):
        threading.Thread.__init__(self)
        self.theParent = parent
        self.calUpdatePeriodSecs = calUpdatePeriodSecs
        self.calServerUrl = calServerUrl
        self.continueRunning = True

    def stop(self):
        self.continueRunning = False

    def getCalendar(self):
        try:
            req = requests.get(self.calServerUrl)
            if req.status_code != 200:
                print("AnimatedCalendar - failed to get from " + self.calServerUrl)
                return None
            # Get calendar from server
            print("AnimatedCalendar - got calendar")
            return req.json()
        except Exception as excp:
            print("AnimatedCalendar - exception getting from calServer ", str(excp))
            return None

    def run(self):
        # Run forever
        while self.continueRunning:
            # Retrieve calendar
            if self.calServerUrl == "":
                print("AnimatedCalendar - no calServer URL")
            else:
                # Get cal from URL
                calendarInfo = self.getCalendar()
                self.theParent.setNewCalendarEntries(calendarInfo)
            # Wait for a while - sleeping but also checking if we need to exit
            for sleepIdx in range(self.calUpdatePeriodSecs * 10):
                time.sleep(0.1)
                if not self.continueRunning:
                    break
            # Exit the thread if asked to stop
            if not self.continueRunning:
                break
        print("AnimatedCalendar - stopped update thread")

class AnimatedCalendar(QTextEdit):
    MAX_DAYS_OF_CALENDAR_TO_DISPLAY = 60

    def __init__(self, calUpdateSecs, calServerUrl, parent=None):
        QTextEdit.__init__(self, parent)
        self.calendarUpdateSecs = calUpdateSecs
        self.calServerUrl = calServerUrl
        # Class vars
        self.updatesRunning = False
        self.updateTimer = None
        self.listUpdateThread = None
        self.calDataLock = threading.Lock()
        self.calDataUpdated = False
        self.curCalendarInfo = None
        # Appearance
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # Text
        self.setReadOnly(True)
        self.setLineWidth(0)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setStyleSheet('font: 25pt "Segoe UI"; color:"white"; background-color:"black"')
        self.setHtml("<B...</B>")
        self.start()

    def start(self):
        self.updatesRunning = True
        QTimer.singleShot(100, self.updateCalendar)
        self.listUpdateThread = CalendarUpdateThread(self, self.calendarUpdateSecs, self.calServerUrl)
        self.listUpdateThread.start()
        print("AnimatedCalendar - started")

    def stop (self):
        print("AnimatedCalendar - stop requested")
        self.updatesRunning = False
        if self.updateTimer is not None:
            self.updateTimer.stop()
        if self.listUpdateThread is not None:
            self.listUpdateThread.stop()
    
    def setNewCalendarEntries(self, calendarInfo):
        with self.calDataLock:
            self.curCalendarInfo = calendarInfo
            self.calDataUpdated = True

    def formatEvent(self, eventDateTime, event):
        evStr = ""
        try:
            summary = event['summary']
            location = event['location']
            duration = event['duration']
            strDurEls = duration.split(":")
            durStr = duration
            if len(strDurEls) >= 3:
                durDays = int(duration[0])
                durStr = (str(durDays) + "day" + ("s" if durDays != 1 else "")) if durDays > 0 else strDurEls[1] + ":" + strDurEls[2]
            locStr = "<font color=\"White\"><i><small>(" + location + ")</small></i>" if (
            location is not None and location != "") else ""
            evStr = "<font color=\"Lime\">" + eventDateTime.strftime("%H:%M") + "</font>"
            evStr += "<font color=\"White\"> <small>(" + durStr + ")</small> " + summary + " " + locStr + "<br/>"
            return evStr
        except Exception as excp:
            print("AnimatedCalendar - Calendar event error " + str(excp))
        return ""

    def formatEventDay(self, eventDateTime):
        return "<font color=\"Aqua\"><b>" + eventDateTime.strftime("%a") + " (" + eventDateTime.strftime("%d %b") + ")</b><br/>"

    def updateCalendar(self):
        # print("AnimatedCalendar: updateCalendar")
        calStr = ""
        with self.calDataLock:
            if self.calDataUpdated and self.curCalendarInfo is not None and "calEvents" in self.curCalendarInfo:
                calEvents = self.curCalendarInfo["calEvents"]
                lastDay = -1
                # Generate HTML
                for calEvent in calEvents:
                    if "eventDate" not in calEvent or "eventTime" not in calEvent:
                        continue
                    eventDate = calEvent["eventDate"]
                    eventTime = calEvent["eventTime"]
                    eventDateTime = datetime.strptime(eventDate + "-" + eventTime, "%Y%m%d-%H:%M")
                    # nowTime = arrow.now()
                    # if dtEvent.ceil("day") < nowTime.floor("day"):
                    #     continue
                    eventStr = self.formatEvent(eventDateTime, calEvent)
                    if eventStr == "":
                        continue
                    # Get date prefix
                    eventPrefix = ""
                    if lastDay != eventDate:
                        if lastDay != -1:
                            eventPrefix = "<br/>"
                        eventPrefix += self.formatEventDay(eventDateTime)
                        lastDay = eventDate
                    # Add to the whole calendar string
                    calStr += eventPrefix + eventStr
                # Update the calendar text
                self.setHtml(calStr)
                self.update()
                self.calDataUpdated = False
        # Exit if required
        if not self.updatesRunning:
            return
        # Start another timer for next update
        self.updateTimer = QTimer()
        self.updateTimer.setInterval(15000)
        self.updateTimer.setSingleShot(True)
        self.updateTimer.timeout.connect(self.updateCalendar)
        self.updateTimer.start()

    def keyPressEvent(self, event): #QKeyEvent
        key = event.key()
        if key != QtCore.Qt.Key_Down or key != QtCore.Qt.Key_Up:
            event.ignore()
        # print("keypressAnimCalendar", event.text(), event.key())
