from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (QTimer, QCoreApplication, Qt, qsrand, QTime, QRectF, QPointF, pyqtSignal, QSize)
from PyQt5.QtGui import (QBrush, QColor, QPainter, QPixmap, QFont, QPalette)
from PyQt5.QtWidgets import (QWidget, QApplication, QGraphicsScene, QGraphicsView, QPushButton, QVBoxLayout, QTextEdit, QGridLayout, QGraphicsRectItem, QGraphicsTextItem, QSizePolicy)

import urllib.request
from ics import Calendar, Event
import threading
import time
import arrow

from pymongo import MongoClient

class CalendarUpdateThread(threading.Thread):
    def __init__(self, parent, calUpdatePeriodSecs, mongoDbServer):
        threading.Thread.__init__(self)
        self.theParent = parent
        self.calUpdatePeriodSecs = calUpdatePeriodSecs
        self.mongoDbServer = mongoDbServer
        self.calFeeds = []
        self.continueRunning = True

    def stop(self):
        self.continueRunning = False
        
    def run(self):
        # Pause a few moments - this is really just to allow the user to exit the app before
        # the long-running process of getting the calendar starts - mainly useful when debugging
        for sleepIdx in range(30):
            time.sleep(1.0)
            if not self.continueRunning:
                break
        # Run forever
        while self.continueRunning:
            # Get calfeeds
            print("AnimatedCalendar - Getting config from Mongo server")
            mongoClient = MongoClient(self.mongoDbServer)
            print("..")
            calMgrDb = mongoClient.CalendarManager
            print("..")
            calFeedsRec = calMgrDb.CalConfig.find_one()
            print("..")
            self.calFeeds = []
            if calFeedsRec is None or "calFeeds" not in calFeedsRec:
                print("AnimatedCalendar - failed to find calendar config record")
            else:
                self.calFeeds = calFeedsRec["calFeeds"]
                # print("AnimatedCalendar - using calfeeds", self.calFeeds)
            # Exit the thread if asked to stop
            if not self.continueRunning:
                break
            # Retrieve calendars from the feeds
            calendars = []
            for calFeed in self.calFeeds:
                # For each calendar
                icsStr = ""
                try:
                    # Read ICS feed into file
                    calUrl = calFeed["icsUrl"]
                    #print ("AnimatedCalendar - Requesting", calUrl)
                    icsReq = urllib.request.urlopen(calUrl)
                    icsStr = icsReq.read()
                    print ("AnimatedCalendar - cal len = ", len(icsStr))
                except:
                    print("Failed in URLLIB")
                # Continue if empty
                if len(icsStr) <= 0:
                    continue
                # Parse ICS file
                calendar = Calendar(str(icsStr,'utf-8'))
                # print(calendar)
                # dtNow = datetime.now()
                # dtEnd = dtNow + timedelta(days=7)
                events = calendar.events
                # dates = [ ev for ev in events if ev.begin in arrow.Arrow.range("hour", dtNow, dtEnd)]
                # dtNow.strftime("%Y%m%d"), dtEnd.strftime("%Y%m%d")
#                print(len(dates))
#                    for date in dates:
#                        print(date)
                calendars.append(events)
#                   print("calhere")
                #except:
                   #print("Failed in Calendar Module")
            self.theParent.setNewCalendarEntries(calendars)
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

    def __init__(self, calUpdateSecs, mongoDbServer, parent=None):
        QTextEdit.__init__(self, parent)
        self.calendarUpdateSecs = calUpdateSecs
        self.mongoDbServer = mongoDbServer
        # Class vars
        self.updatesRunning = False
        self.updateTimer = None
        self.listUpdateThread = None
        self.calDataLock = threading.Lock()
        self.calDataUpdated = False
        self.curCalendars = None
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
        self.listUpdateThread = CalendarUpdateThread(self, self.calendarUpdateSecs, self.mongoDbServer)
        self.listUpdateThread.start()
        print("AnimatedCalendar - started")

    def stop (self):
        print("AnimatedCalendar - stop requested")
        self.updatesRunning = False
        if self.updateTimer != None:
            self.updateTimer.stop()
        if self.listUpdateThread != None:
            self.listUpdateThread.stop()
    
    def setNewCalendarEntries(self, calendars):
        with self.calDataLock:
            self.curCalendars = calendars
            self.calDataUpdated = True
        
    def updateCalendar(self):
        # print("AnimatedCalendar: updateCalendar")
        with self.calDataLock:
            if self.calDataUpdated and self.curCalendars != None:
                nowTime = arrow.now()
                for calEvents in self.curCalendars:
                    calStr = ""
                    lastDay = -1
                    for anEvent in calEvents:
                        # date, duration, summary, location, UID
                        eventDate = anEvent.begin
                        if eventDate.ceil("day") < nowTime.floor("day"):
                            continue
                        duration = anEvent.duration
                        summary = anEvent.name
                        location = anEvent.location
                        if lastDay != eventDate.day:
                            if lastDay != -1:
                                calStr += "<br/>"
                            calStr += "<font color=\"Aqua\"><b>" + anEvent.begin.strftime("%a") + " (" + anEvent.begin.strftime("%d %b") + ")</b><br/>"
                            lastDay = eventDate.day
                        strDurTime = str(duration).rpartition(":")[0]
                        durStr = (str(duration.days) + "day" + ("s" if duration.days != 1 else "")) if duration.days > 0 else strDurTime
                        locStr = "<font color=\"White\"><i><small>("+location+")</small></i>" if (location is not None and location != "") else ""
                        calStr += "<font color=\"Lime\">" + anEvent.begin.strftime("%H:%M") + "</font><font color=\"White\"> <small>(" + durStr + ")</small> " + summary + " " + locStr + "<br/>"
#                        print (anEvent)
    #                    print(date)
                    self.setHtml(calStr)
                    self.update()
            self.calDataUpdated = False
        
        if not self.updatesRunning:
            return 
        self.updateTimer = QTimer()
        self.updateTimer.setInterval(15000)
        self.updateTimer.setSingleShot(True)
        self.updateTimer.timeout.connect(self.updateCalendar)
        self.updateTimer.start()
