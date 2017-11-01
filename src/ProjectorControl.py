import serial
import sys
from PyQt5.QtCore import (Qt, QTime, QTimer)
import datetime
import threading

class ProjectorControl:
    _projectorIsOn = True
    _eventTimes = [ ("07:00","on"), ("09:00", "off") ]
    _nextEvent = None

    def __init__(self, projectorModel, comPort):
        self._projectorModel = projectorModel
        self._comPort = comPort
        # Next event time
        self.prepareNextEventTime()
        # Wakeup / turn off timer
#        self._projectorPowerTimer = QTimer()
#        self._projectorPowerTimer.setSingleShot(False)
#        self._projectorPowerTimer.timeout.connect(self.handleTickProjectorPower)
#        self._projectorPowerTimer.start(10 * 1000)
        self._projectorPowerTimer = threading.Timer(10.0, self.handleTick)
        self._projectorPowerTimer.start()
        print("ProjectorControl: construct")

    def stop(self):
        self._projectorPowerTimer.stop()
        print("Stopped projector control timer")

    def prepareNextEventTime(self):
        curTime = datetime.datetime.now()
        self._nextEvent = None
        for event in self._eventTimes:
            evTime = datetime.datetime.strptime(event[0], "%H:%M")
            if evTime.hour < curTime.hour or (evTime.hour == curTime.hour and evTime.minute <= curTime.minute):
                continue
            self._nextEvent = event
            break
        if self._nextEvent is None:
            self._nextEvent = self._eventTimes[0]
        print("Next event at " + self._nextEvent[0] + " projector " +  self._nextEvent[1])

    def handleTick(self):
        # Check for time of next event
        print("Projector tick")
        curTime = datetime.datetime.now()
        nextEventTime = datetime.datetime.strptime(self._nextEvent[0], "%H:%M")
        print("Comparing ", nextEventTime.hour, nextEventTime.minute, "to", curTime.hour, curTime.minute)
        if curTime.hour == nextEventTime.hour and curTime.minute == nextEventTime.minute:
            turnOn = (self._nextEvent[1] == "on")
            self.switchPower(turnOn)
            self.prepareNextEventTime()
        self._projectorPowerTimer = threading.Timer(10.0, self.handleTick)
        self._projectorPowerTimer.start()

    def switchPower(self, turnOn):
        if self._projectorModel is "PanasonicVZ570":
            # Send to panasonic projector
            ser = serial.Serial(self._comPort)
            if turnOn:
                print("Turning projector on")
                ser.write(b'\2PON\3')
                self.monitorOn()
            else:
                print("Turning projector off")
                ser.write(b'\2POF\3')
            ser.close()

    def monitorOn(self):
        if sys.platform.startswith('linux'):
            import os
            os.system("xset dpms force off")

        elif sys.platform.startswith('win'):
            import win32gui
            import win32con
            from os import getpid, system
            from threading import Timer

            def force_exit():
                pid = getpid()
                system('taskkill /pid %s /f' % pid)

            t = Timer(1, force_exit)
            t.start()
            SC_MONITORPOWER = 0xF170
            win32gui.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SYSCOMMAND, SC_MONITORPOWER, 2)
            t.cancel()

# To power on use: b'\2PON\3'
# Power off: b'\2POF\3'
# Input HDMI1: b'\2IIS:HD1\3'
# Manu toggle: b'\2OMN\3'
