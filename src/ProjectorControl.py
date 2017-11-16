import serial
import sys
import time
import datetime
import threading
import win32api
import win32con

class ProjectorControl:
    _projectorIsOn = True
    _eventTimes = [ ("07:00","on"), ("09:00", "off"), ("15:00","on"), ("20:00", "off") ]
    _nextEvent = None
    _stopRequested = False
    _serialConnection = None
    _userLastActiveTimeSecs = win32api.GetLastInputInfo()
    _turnOffPendingInactivity = False
    MIN_INACTIVE_SECS = 1800

    def __init__(self, projectorModel, comPort):
        self._projectorModel = projectorModel
        self._comPort = comPort
        # Next event time
        self.prepareNextEventTime()
        # Wakeup / turn off timing
        self._projectorPowerTiming = threading.Thread(target=self.powerTimingHandler)
        self._projectorPowerTiming.start()
        # Serial connection
        try:
            self._serialConnection = serial.Serial(self._comPort)
            if self._serialConnection is not None:
                self._serialRxThread = threading.Thread(target=self.serialHandler, args=(self._serialConnection,))
                self._serialRxThread.start()
                print("ProjectorControl - started serial monitoring")
            else:
                self._serialRxThread = None
                print("ProjectorControl - failed to connect to", self._comPort)
        except:
            print("ProjectorControl - failed to connect to", self._comPort)
            if self._serialConnection is not None:
                self._serialConnection.close()
            self._serialConnection = None
            self._serialRxThread = None
        print("ProjectorControl - started")

    def stop(self):
        self._stopRequested = True
        print("ProjectorControl - stop requested")

    def serialHandler(self, serialConn):
        # print("ProjectorControl - serialHandler start", serialConn)
        while True:
            if self._stopRequested:
                break
            if serialConn.inWaiting() > 0:
                newChars = serialConn.read()
                for newCh in newChars:
                    print("{:02X} ".format(newCh), end="")
                    if newCh == 0x03:
                        print()
            time.sleep(100)
        try:
            serialConn.close()
            print("ProjectorControl - Closed serial connection")
        except:
            print("ProjectorControl - Failed to close serial connection")
        print("ProjectorControl - serial monitor stopped")

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
        print("ProjectorControl - Next event at " + self._nextEvent[0] + " projector " +  self._nextEvent[1])

    def powerTimingHandler(self):
        while True:
            if self._stopRequested:
                break
            # Check for next event time
            curTime = datetime.datetime.now()
            print("Checking time at", curTime)
            nextEventTime = datetime.datetime.strptime(self._nextEvent[0], "%H:%M")
            nextEventAction = self._nextEvent[1]
            if curTime.hour == nextEventTime.hour and curTime.minute == nextEventTime.minute:
                if nextEventAction == "on":
                    print("Turning projector on")
                    self.switchPower(True)
                elif nextEventAction == "off":
                    self._turnOffPendingInactivity = True
                    print("ProjectorControl - turn off when inactive")
                self.prepareNextEventTime()
            # Check for turn-off based on inactivity
            if self._turnOffPendingInactivity:
                inactiveSecs = self.getInactiveForSecs()
                print("Wait for inactive", inactiveSecs)
                if inactiveSecs > self.MIN_INACTIVE_SECS:
                    self.switchPower(False)
                    self._turnOffPendingInactivity = False
                    print("ProjectorControl - inactive for", inactiveSecs, "turning off")
            # Wait a bit
            time.sleep(30.0)
        print("PowerControl: powerTimingThread exiting")

    def switchPower(self, turnOn):
        if self._projectorModel is "PanasonicVZ570":
            # Send to panasonic projector
            if turnOn:
                print("ProjectorControl - Turning projector on")
                self._serialConnection.write(b'\2PON\3')
                self.monitorOn()
            else:
                print("ProjectorControl - Turning projector off")
                self._serialConnection.write(b'\2POF\3')

    def monitorOn(self):
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 0, 10, 0)
        time.sleep(0.05)
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 0, -10, 0)    

    def test(self):
        if self._projectorModel is "PanasonicVZ570":
            # Send to panasonic projector
            print("ProjectorControl - Checking power")
            self._serialConnection.write(b'\2QPW\3')

    def getInactiveForSecs(self):
        lastInputSecs = win32api.GetLastInputInfo()
        if lastInputSecs >= self._userLastActiveTimeSecs:
            return lastInputSecs - self._userLastActiveTimeSecs
        return 0xffffffff - self._userLastActiveTimeSecs + lastInputSecs
        
# To power on use: b'\2PON\3'
# Power off: b'\2POF\3'
# Input HDMI1: b'\2IIS:HD1\3'
# Manu toggle: b'\2OMN\3'
