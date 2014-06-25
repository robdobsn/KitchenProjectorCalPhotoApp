from PyQt5.QtCore import (QTimer, QPointF)
from PyQt5.QtGui import (QColor, QFont, QBrush)
from PyQt5.QtWidgets import (QGraphicsTextItem, QGraphicsRectItem)

import urllib.request
import ICalParser
import threading
import time
from datetime import datetime
from datetime import timedelta
import tempfile
import os

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
            
#                print ("Calupdate")
            calendars = []
            for calFeed in self.calFeeds:
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

                if len(icsStr) <= 0:
                    continue
                
                #try:
                if True:
                    tempFname = ""
 #                   tempFname = "C:/Users/rob/Downloads/testFile.ics"
 #                   tempFile = open(tempFname, "w")
                    (tempFile, tempFname) =tempfile.mkstemp(prefix="robcaltmp", text=True)
                    print(tempFname)
                    os.write(tempFile, icsStr) #.decode("utf-8"))
                    os.close(tempFile)
##                except:
##                    print("Failed in writing cal file to temp", tempFname)
##                    if tempFname != "":
##                        try:
##                            os.remove(tempFname)
##                        except:
##                            None
##                    tempFname = ""

                if tempFname == "":
                    continue
                    
                #try:
                # Parse ICS file
                icsfile=tempFname
                cal_parser = ICalParser.ICalParser()
                cal_parser.local_load(icsfile)
#                mycal = pyicalendar.pyicalendar.ics()
#                mycal.local_load(icsfile)
                os.remove(tempFname)
                #mycal.parse_loaded()
                dtNow = datetime.now()
                dtEnd = dtNow + timedelta(days=7)
#                dates = mycal.get_event_instances(dtNow.strftime("%Y%m%d"),dtEnd.strftime("%Y%m%d"))
                dates = cal_parser.get_event_instances(dtNow.strftime("%Y%m%d"),dtEnd.strftime("%Y%m%d"))
#                print(len(dates))
#                    for date in dates:
#                        print(date)
                calendars.append(dates)
#                   print("calhere")
                self.theParent.setNewCalendarEntries(calendars)
                #except:
                   #print("Failed in Calendar Module")
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
        self.textItem = QGraphicsTextItem()
        self.textItem.setFont(QFont("Segoe UI", 24))
        self.textItem.setDefaultTextColor(QColor("black"))
        self.textItem.setPos(QPointF(self.borders[3]+10,self.borders[0]+10))
        self.textItem.setHtml("<B>Hello</B>Hello")
        self.textItem.setZValue(20)
        self.textItem.setTextWidth(self.widthCalTextArea-20)
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
                for calEvents in self.curCalendars:
                    calStr = ""
                    lastDay = -1
                    for anEvent in calEvents:
                        # date, duration, summary, location, UID
                        eventDate = anEvent[0]
                        duration = anEvent[1]
                        summary = anEvent[2]
                        location = anEvent[3]
                        if lastDay != eventDate.day:
                            if lastDay != -1:
                                calStr += "<br/>"
                            calStr += "<b>" + anEvent[0].strftime("%a") + " (" + anEvent[0].strftime("%d %B)") + ")</b><br/>"
                            lastDay = eventDate.day
                        strDurTime = str(duration).rpartition(":")[0]
                        durStr = (str(duration.days) + "day" + ("s" if duration.days != 1 else "")) if duration.days > 0 else strDurTime
                        locStr = "<small>("+location+")</small>" if location != "" else ""
                        calStr += anEvent[0].strftime("%H:%M") + " <small>(" + durStr + ")</small> " + summary + " " + locStr + "<br/>"
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
