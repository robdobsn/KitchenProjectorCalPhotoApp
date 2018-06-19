import os
from os.path import join
import threading
import time
import random
from PhotoInfo import PhotoInfo
from collections import deque

class PhotoFilelistUpdateThread(threading.Thread):
    theParent = None
    continueRunning = True
    validFileExtList = []
    rootPath = ""
    listUpdatePeriodSecs = 3600

    def __init__(self, parent, validFileExtList, rootPath, listUpdatePeriodSecs):
        threading.Thread.__init__(self)
        self.theParent = parent
        self.validFileExtList = validFileExtList
        self.rootPath = rootPath
        self.listUpdatePeriodSecs = listUpdatePeriodSecs
        
    def stop(self):
        self.continueRunning = False
        print("PhotoFileManager stop requested")
        
    def run(self):
        REPORT_AFTER_N_FOUND = 10000
        while (self.continueRunning):
            quickInitialUpdate = True
            lastFileCount = 0
            totalFileCount = 0
            foldersWithJpegs = []
            for root, dirs, files in os.walk(self.rootPath):
                if not self.continueRunning:
                    break
                jpegCount = len([fname for fname in files if fname[-3:].lower() in self.validFileExtList])
                if jpegCount > 0:
                    foldersWithJpegs.append((root, jpegCount))
                    totalFileCount += jpegCount
                    # Since this process can take a long time - let's get the ball rolling with the first few images found
                    if quickInitialUpdate and totalFileCount > 1000:
                        self.theParent.setNewList(foldersWithJpegs, totalFileCount)
                        quickInitialUpdate = False
                if totalFileCount > lastFileCount + REPORT_AFTER_N_FOUND:
                    print("PhotoFileManager: Found", totalFileCount, "photos")
                    lastFileCount = totalFileCount
            if not self.continueRunning:
                break
            self.theParent.setNewList(foldersWithJpegs, totalFileCount)
            for sleepIdx in range(int(self.listUpdatePeriodSecs)):
                time.sleep(1)
                if not self.continueRunning:
                    break
            if not self.continueRunning:
                break
        print("PhotoFileManager update thread stopped")
        
class PhotoFileManager():
    totalPhotoCount = 0
    photoFolderList = []
    curPhotoFilename = ""
    validFileExtList = []
    rootPath = ""
    listUpdateThread = None
    listUpdateLock = threading.Lock()
    previousPhotoNames = deque()
    MAX_BACK_STEPS_ALLOWED = 100
    curPhotoOffset = 0

    def __init__(self, validFileExtList, rootPath, listUpdateInterval, photoDeltas):
        self.listUpdateInterval = listUpdateInterval
        self.validFileExtList = validFileExtList
        self.rootPath = rootPath
        self.photoDeltas = photoDeltas
        
    def startPhotoListUpdate(self):
        self.listUpdateThread = PhotoFilelistUpdateThread(self, self.validFileExtList, self.rootPath, self.listUpdateInterval)
        self.listUpdateThread.start()
#        print("List Update Started")

    def setRootPath(self, rootPath):
        self.rootPath = rootPath
        
    def setValidFileExts(self, validExts):
        self.validFileExtList = validExts

    def stop(self):
#        print("PFM stopped")
        if self.listUpdateThread != None:
            self.listUpdateThread.stop()
        
    def setNewList(self, folderList, totalCount):
        with self.listUpdateLock:
            self.photoFolderList = folderList
            self.totalPhotoCount = totalCount
#        print(folderList, totalCount)

    def getNumPhotos(self):
        return self.totalPhotoCount
    
    def getCurPhotoFilename(self):
        if self.curPhotoFilename == "":
            self.moveNext()
        return self.curPhotoFilename

    def getCurPhotoInfo(self):
        curFileName = self.getCurPhotoFilename()
        newPhotoInfo = PhotoInfo()
        newPhotoInfo.setFromFile(curFileName)
        self.photoDeltas.applyDeltasToPhotoInfo(curFileName, newPhotoInfo)
        return newPhotoInfo

    def moveNext(self):
        # Check if we're moving back to latest
        if self.curPhotoOffset > 0:
            self.curPhotoOffset -= 1
            self.curPhotoFilename = self.previousPhotoNames[len(self.previousPhotoNames) - 1 - self.curPhotoOffset]
            print("ReMoved to " + self.curPhotoFilename)
            return
        with self.listUpdateLock:
            if self.totalPhotoCount > 0:
                photoIdx = random.randrange(0,self.totalPhotoCount-1)
                photoCtr = 0
                for photoFolder in self.photoFolderList:
                    if photoIdx < photoCtr + photoFolder[1]:
    #                    print (photoIdx, photoCtr, photoFolder[1])
                        try:
                            fileList = os.listdir(photoFolder[0])
                        except:
                            print("Failed to access folder " + photoFolder[0])
                            break
                        for fname in fileList:
                            if fname[-3:].lower() in self.validFileExtList:
                                if photoCtr == photoIdx:
                                    self.curPhotoFilename = join(photoFolder[0], fname)
                                    while len(self.previousPhotoNames) > self.MAX_BACK_STEPS_ALLOWED:
                                        self.previousPhotoNames.popleft()
                                    self.previousPhotoNames.append(self.curPhotoFilename)
                                    print("Moved to " + self.curPhotoFilename)
                                photoCtr += 1
                        break
                    photoCtr += photoFolder[1]

    def movePrev(self):
        if self.curPhotoOffset >= len(self.previousPhotoNames)-1:
            return
        self.curPhotoOffset += 1
        self.curPhotoFilename = self.previousPhotoNames[len(self.previousPhotoNames)-1-self.curPhotoOffset]
        print("Moved back to " + self.curPhotoFilename)

