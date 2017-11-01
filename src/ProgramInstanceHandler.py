# Handler for program instance
# Attempts to ensure a single instance of the program executes

import tempfile
import os
import psutil
import win32gui, win32process
import sys

class ProgramInstanceHandler:
    def checkForAnotherInstance(self):
        # Check if an instance is already running
        self.sentinelFilename = tempfile.gettempdir() + "\\rd_photocalendar_sentinel.txt";
        (isRunning, existingPid) = self.instanceAlreadyRunning(self.sentinelFilename)
        if isRunning:
            self.setExistingInstanceToForeground(existingPid)
            sys.exit(0)

    def stop(self):
        self.cleanUpOnExit()
        print ("ProgramInstanceHandler: Removed sentinel file and stopped")

    def cleanUpOnExit(self):
        if os.path.exists(self.sentinelFilename):
            try:
                os.remove(self.sentinelFilename)
                print("ProgramInstanceHandler: : Removed sentinel file successfully")
            except:
                print("ProgramInstanceHandler: : Failed to clean up sentinel file " + self.sentinelFilename)

    def instanceAlreadyRunning(self, sentinelFilename):
        print("ProgramInstanceHandler: Checking sentinel file " + sentinelFilename)
        if os.path.exists(sentinelFilename):
            print("ProgramInstanceHandler: Sentinel file found")
            with open(sentinelFilename, 'r') as f:
                pid = int(f.read())
                f.close()
                print("ProgramInstanceHandler: PID " + str(pid))
                if psutil.pid_exists(pid):
                    print("ProgramInstanceHandler: Looks like another instance of this process is running " + str(pid))
                    return (True, pid)
                else:
                    try:
                        os.remove(sentinelFilename)
                        print("ProgramInstanceHandler: removed sentinel successfully")
                    except:
                        print("ProgramInstanceHandler: Failed to remove Sentinel " + sentinelFilename)
        with open(sentinelFilename, 'w') as f:
            f.write(str(os.getpid()))
            f.close()
            print("ProgramInstanceHandler: Sentinel file written")
        return False, 0

    def enumerateWindows(self, hwnd, paramPID):
        if win32gui.IsWindowVisible(hwnd):
            (winThreadId, winProcId) = win32process.GetWindowThreadProcessId(hwnd)
            if winProcId == paramPID:
                # if 'Animated Tiles' in win32gui.GetWindowText(hwnd):
                # win32gui.MoveWindow(hwnd, 0, 0, 760, 500, True)
                win32gui.SetForegroundWindow(hwnd)
                print("Setting to foreground ")

    def setExistingInstanceToForeground(self, pid):
        win32gui.EnumWindows(self.enumerateWindows, pid)

