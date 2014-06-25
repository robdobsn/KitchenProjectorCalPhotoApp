import os
from os.path import join
import threading
import time
import random
from PhotoInfo import PhotoInfo

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
        
    def run(self):
        while (self.continueRunning):
            quickInitialUpdate = True
            totalFileCount = 0
            foldersWithJpegs = []
            for root, dirs, files in os.walk(self.rootPath):
                if not self.continueRunning:
                    return
                jpegCount = len([fname for fname in files if fname[-3:].lower() in self.validFileExtList])
                if jpegCount > 0:
                    foldersWithJpegs.append((root, jpegCount))
                    totalFileCount += jpegCount
                    # Since this process can take a long time - let's get the ball rolling with the first few images found
                    if quickInitialUpdate and totalFileCount > 1000:
                        self.theParent.setNewList(foldersWithJpegs, totalFileCount)
                        quickInitialUpdate = False
            self.theParent.setNewList(foldersWithJpegs, totalFileCount)
            time.sleep(self.listUpdatePeriodSecs)
        
class PhotoFileManager():
    totalPhotoCount = 0
    photoFolderList = []
    curPhotoFilename = ""
    validFileExtList = []
    rootPath = ""
    cachedPhotoInfo = None
    listUpdateThread = None
    listUpdateLock = threading.Lock()
    
    def __init__(self, validFileExtList, rootPath, listUpdateInterval):
        self.listUpdateInterval = listUpdateInterval
        self.validFileExtList = validFileExtList
        self.rootPath = rootPath
        
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
        if self.cachedPhotoInfo != None:
            if self.cachedPhotoInfo[0] == curFileName:
                return self.cachedPhotoInfo[1]
        newPhotoInfo = PhotoInfo()
        newPhotoInfo.setFromFile(curFileName)
        self.cachedPhotoInfo = (curFileName, newPhotoInfo)
        return newPhotoInfo
        
    def moveNext(self):
        with self.listUpdateLock:
            if self.totalPhotoCount > 0:
                photoIdx = random.randrange(0,self.totalPhotoCount-1)
                photoCtr = 0
                for photoFolder in self.photoFolderList:
                    if photoIdx < photoCtr + photoFolder[1]:
    #                    print (photoIdx, photoCtr, photoFolder[1])
                        fileList = os.listdir(photoFolder[0])
                        for fname in fileList:
                            if fname[-3:].lower() in self.validFileExtList:
                                if photoCtr == photoIdx:
                                    self.curPhotoFilename = join(photoFolder[0], fname)
                                photoCtr += 1
                        break
                    photoCtr += photoFolder[1]

### Test code   
##ph = PhotoFileManager(["jpg"], 'P:/PhotosMain/2012/')
##ph.startPhotoListUpdate()
##maxTime = 60
##while maxTime > 0 and ph.getNumPhotos() <= 0:
##    time.sleep(1)
##    print (".", end="")
##    maxTime -= 1
##if ph.getNumPhotos() > 0:
##    print()
##    for i in range(20):
##        ph.moveNext()
##        print (ph.getCurPhotoFilename())
##else:
##    print ("No Photos")
