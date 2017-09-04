from PyQt5.QtCore import (QTimer, QPointF)
from PyQt5.QtGui import (QColor, QFont, QBrush)
from PyQt5.QtWidgets import (QGraphicsTextItem, QGraphicsRectItem, QScrollArea,QTextEdit)

import urllib.request
from ics import Calendar, Event
import threading
import time
from datetime import datetime
from datetime import timedelta
import arrow

class CalendarUpdateThread(threading.Thread):
    theParent = None
    continueRunning = True
    calFeeds = []
    listUpdatePeriodSecs = 60
    
    def __init__(self, parent, calFeeds, calUpdatePeriodSecs):
        threading.Thread.__init__(self)
        self.theParent = parent
        self.calFeeds = calFeeds
        self.calUpdatePeriodSecs = calUpdatePeriodSecs
        
    def stop(self):
        self.continueRunning = False
        
    def run(self):
        while (self.continueRunning):
            
            calendars = []
            for calFeed in self.calFeeds:
                # For each calendar
                icsStr = ""
                try:
                    # Read ICS feed into file
                    calUrl = calFeed["icsUrl"]
                    print ("Requesting", calUrl)
                    icsReq = urllib.request.urlopen(calUrl)
                    icsStr = icsReq.read()
                    print ("Cal len = ", len(icsStr))
                except:
                    print("Failed in URLLIB")
                # Continue if empty
                if len(icsStr) <= 0:
                    continue
                # Parse ICS file
                calendar = Calendar(str(icsStr,'utf-8'))
                print(calendar)
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
            time.sleep(self.calUpdatePeriodSecs)

class AnimatedCalendar():
    updatesRunning = False
    updateTimer = None
    listUpdateThread = None
    calDataLock = threading.Lock()
    calDataUpdated = False
    curCalendars = None
    
    def __init__(self, scene, widthCalTextArea, heightCalTextArea, borders, calFeeds, calUpdateSecs):
        self.masterScene = scene
        self.widthCalTextArea = widthCalTextArea
        self.heightCalTextArea = heightCalTextArea
        self.borders = borders
        self.calFeeds = calFeeds
        self.calendarUpdateSecs = calUpdateSecs
        # Background
        self.textBkgd = QGraphicsRectItem(0, 0, self.widthCalTextArea, self.heightCalTextArea)
        self.textBkgd.setPos(self.borders[3], self.borders[0])
        self.textBkgd.setBrush(QColor("light green"))
        self.textBkgd.setZValue(10)
        
        scene.addItem(self.textBkgd)
        # Text Item
        self.textItem = QTextEdit()
        self.textItem.setReadOnly(True)
        self.textItem.setCurrentFont(QFont("Segoe UI", 24))
        self.textItem.setTextColor(QColor("black"))
        # self.textItem.setPos(QPointF(self.borders[3]+10,self.borders[0]+10))
        self.textItem.setHtml("<B>Calendar will appear here!</B>")
        # self.textItem.setZValue(20)
        # self.textItem.setTextWidth(self.widthCalTextArea-20)
        # self.textItem.setLineWrapMode(QTextEdit.FixedPixelWidth)

        # # Scroll area
        # scrollArea = QScrollArea()
        scene.addItem(self.textItem)
        
    def start(self):
        self.updatesRunning = True
        QTimer.singleShot(100, self.updateCalendar)
        self.listUpdateThread = CalendarUpdateThread(self, self.calFeeds, self.calendarUpdateSecs)
        self.listUpdateThread.start()
#        print("CalStarted")

    def stop (self):
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
#        print("Update cal")
        
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
                            calStr += "<b>" + anEvent.begin.strftime("%a") + " (" + anEvent.begin.strftime("%d %B)") + ")</b><br/>"
                            lastDay = eventDate.day
                        strDurTime = str(duration).rpartition(":")[0]
                        durStr = (str(duration.days) + "day" + ("s" if duration.days != 1 else "")) if duration.days > 0 else strDurTime
                        locStr = "<small>("+location+")</small>" if (location is not None and location != "") else ""
                        calStr += anEvent.begin.strftime("%H:%M") + " <small>(" + durStr + ")</small> " + summary + " " + locStr + "<br/>"
#                        print (anEvent)
    #                    print(date)
                    self.textItem.setHtml(calStr)
                    self.textItem.setTextWidth(self.widthCalTextArea-20)
                    self.textItem.update()
            self.calDataUpdated = False
        
        if not self.updatesRunning:
            return 
        self.updateTimer = QTimer()
        self.updateTimer.setInterval(5000)
        self.updateTimer.setSingleShot(True)
        self.updateTimer.timeout.connect(self.updateCalendar)
        self.updateTimer.start()
