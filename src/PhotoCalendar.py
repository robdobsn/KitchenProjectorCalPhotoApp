# PhotoCalendar app
# Displays time, calendar and photo slideshow in a simple Qt desktop app

from PyQt5.QtCore import (Qt, qsrand, QTime)
from PyQt5.QtWidgets import (QApplication, QGraphicsView)
from PyQt5.QtGui import (QColor, QPalette)

import sys
import atexit
import time
import logging
import os

from MainWindow import MainWindow
from ProjectorControl import ProjectorControl
from ProgramInstanceHandler import ProgramInstanceHandler

LOGGING_FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"), format=LOGGING_FORMAT)
log = logging.getLogger(__name__)

def setupApplication():
    app = QApplication(sys.argv)
    #app.aboutToQuit.connect(appExitHandler)
    darkPalette = QPalette()
    darkPalette.setColor(QPalette.Window, QColor(0, 0, 0))
    darkPalette.setColor(QPalette.WindowText, Qt.white)
    darkPalette.setColor(QPalette.Base, QColor(25, 25, 25))
    darkPalette.setColor(QPalette.AlternateBase, QColor(0, 0, 0))
    darkPalette.setColor(QPalette.ToolTipBase, Qt.white)
    darkPalette.setColor(QPalette.ToolTipText, Qt.white)
    darkPalette.setColor(QPalette.Text, Qt.white)
    darkPalette.setColor(QPalette.Button, QColor(0, 0, 0))
    darkPalette.setColor(QPalette.ButtonText, Qt.black)
    darkPalette.setColor(QPalette.BrightText, Qt.red)
    darkPalette.setColor(QPalette.Link, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(darkPalette)
    app.setStyleSheet("QScrollBar:vertical {background-color: black}  QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {background: none;}")
    return app

def appExitHandler():
    projectorControl.stop()
    time.sleep(2.0)
    programInstanceHandler.stop()
    print("App exit done")

if __name__ == '__main__':

    # App configuration
    appConfig = {"calServerUrl": "http://domoticzoff:5077/calendar/full/60"}

    # Program instance handler
    programInstanceHandler = ProgramInstanceHandler()
    programInstanceHandler.checkForAnotherInstance()

    # Init the random number generator
    qsrand(QTime(0,0,0).secsTo(QTime.currentTime()))

    # Projector control
    projectorControl = ProjectorControl("PanasonicVZ570", "COM3")

    # Register an exit handler
    #atexit.register(appExitHandler)

    # PyQt application
    app = setupApplication()

    # Main window
    mainWindow = MainWindow(appConfig, projectorControl)
    mainWindow.setWindowTitle("Photo Calendar")
    mainWindow.resize(1280, 1024)
    mainWindow.show()

    # Start the app
    exitCode = app.exec_()
    appExitHandler()
    sys.exit(exitCode)
    
