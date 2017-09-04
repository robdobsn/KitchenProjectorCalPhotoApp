#!/usr/bin/env python33

from PyQt5.QtCore import (pyqtProperty, QEasingCurve, QObject,
        QPointF, QPropertyAnimation, qrand, QSize, Qt)
from PyQt5.QtGui import (QPixmap, QImage, QTransform)
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsPixmapItem, QGraphicsView)
import datetime
import gc
from PhotoFileManager import PhotoFileManager
from PhotoInfo import PhotoInfo


def randNo(low, high):
    qr = qrand() % ((high + 1) - low) + low;
    return qr

# PyQt doesn't support deriving from more than one wrapped class so we use
# composition and delegate the property.
class Pixmap(QObject):
    pixmapSize = QSize(0,0)
    def __init__(self, pix):
        super(Pixmap, self).__init__()

        self.pixmap_item = QGraphicsPixmapItem(pix)
        self.pixmap_item.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.pixmap_item.setZValue(0)

    def _set_pos(self, pos):
        self.pixmap_item.setPos(pos)

    def _set_scale(self, scale):
        self.pixmap_item.setScale(scale)

    pos = pyqtProperty(QPointF, fset=_set_pos)
    scale = pyqtProperty(float, fset=_set_scale)
        
class PicItem():
    pixmap = None
    gridRow = -1
    gridCol = -1
    dateTimeAdded = None
    photoInfo = PhotoInfo()
    
    def __init__(self, pixmap, gridRow, gridCol, xFactor, yFactor, photoInfo):
        self.pixmap = pixmap
        self.gridRow = gridRow
        self.gridCol = gridCol
        self.dateTimeAdded = datetime.datetime.now()
        self.xFactor = xFactor
        self.yFactor = yFactor
        self.photoInfo = photoInfo


class PicManager():
#    curPhotoIdx = 0
#    sourcePhotoList = []
    photosInGrid = []
    nextPixmap = None
    photoFileManager = None
    shrinkDuration = 600
    moveDuration = 600
    moveModifier = 100
    insertDuration = 600
    
    def __init__(self, masterScene, photoBaseDir, validPhotoFileExts, maxCols, maxRows, cellSize, borders, xBetweenPics, yBetweenPics):
        self.masterScene = masterScene
        self.maxCols = maxCols
        self.maxRows = maxRows
        self.cellSize = cellSize
        self.borders = borders
        self.xBetweenPics = xBetweenPics
        self.yBetweenPics = yBetweenPics
        self.photoBaseDir = photoBaseDir
        self.validPhotoFileExts = validPhotoFileExts
        self.photoFileManager = PhotoFileManager(validPhotoFileExts, self.photoBaseDir, 7200.00)
        self.photoFileManager.startPhotoListUpdate()
#        self.curPhotoIdx = 0
#        self.sourcePhotoList = []
#        for root,dirs,files in os.walk(self.photoBaseDir):
#            for file in files:
#                if file.endswith(".jpg"):
#                    self.sourcePhotoList.append(file)
#        print ("Photos " + str(len(self.sourcePhotoList)) + " " + (self.sourcePhotoList[0] if len(self.sourcePhotoList)>0 else ""))

    def resize(self, cellSize):
        self.cellSize = cellSize

    def stop(self):
        self.photoFileManager.stop()
        
    def getCellTLCoords(self, lin, col):
        cellW = self.cellSize.width()
        cellH = self.cellSize.height()
        qp = QPointF(self.borders[3] + (cellW+self.xBetweenPics) * col, self.borders[0] + (cellH+self.yBetweenPics) * lin)
    #    print(lin,col,qp, cellW, cellH, randNo(0,1))
        return qp

    def loadImage(self, xFactor, yFactor):
        newImg = QImage()
        newImg.load(self.photoFileManager.getCurPhotoFilename())
        newImgInfo = self.photoFileManager.getCurPhotoInfo()
        transform = QTransform()
        transform.rotate(newImgInfo.rotationAngle)
        interImg = newImg.transformed(transform, Qt.SmoothTransformation)
        xReqdSize = self.cellSize.width() * xFactor + self.xBetweenPics * (xFactor-1)
        yReqdSize = self.cellSize.height() * yFactor + self.yBetweenPics * (yFactor-1)
        inter2Img = interImg.scaled(QSize(xReqdSize,yReqdSize), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        finalImg = inter2Img.copy(0,0,xReqdSize,yReqdSize)
#        print("XY Size", xFactor, yFactor, xReqdSize,yReqdSize)
        return (finalImg, newImgInfo)

    def getNextPicItem(self, xFactor, yFactor):
        if self.photoFileManager.getNumPhotos() == 0:
            return None
        (newImg, newImgInfo) = self.loadImage(xFactor, yFactor)
#        print ("Loaded photo", self.sourcePhotoList[self.curPhotoIdx], " w", finalImg.width(), " h", finalImg.height(), " facs", xFactor, yFactor)
        self.photoFileManager.moveNext()
        return PicItem(Pixmap(QPixmap(newImg)),-1,-1,xFactor,yFactor,newImgInfo)

    def getValidCells(self, xFactor, yFactor):
        validCellRows = []
        occupiedRows = []
        # Apply the mathematical rules below        
        for row in range(self.maxRows):
            validCellCols = []
            occupiedCols = []
            for col in range(self.maxCols):
                # For 1x1 any cell is valid
                # For 1x2 (less wide than high) cells in even numbered rows (starting at 0) and excluding bottom row are valid
                # For 2x2 cells in even rows except bottom and excluding rightmost column are valid
                cellValid = True
                if xFactor == 1 and yFactor == 1:
                    cellValid = True
                elif yFactor == 2:
                    cellValid = ((row % 2) == 0)
                    if row == self.maxRows-1:
                        cellValid = False
                    if xFactor == 2:
                        if col == self.maxCols-1:
                            cellValid = False
                validCellCols.append(cellValid)
                occupiedCols.append(-1)
            validCellRows.append(validCellCols)
            occupiedRows.append(occupiedCols)
        # Check the existing photos in the grid
        for photoIdx in range(len(self.photosInGrid)):
            photo = self.photosInGrid[photoIdx]
            # A cell which is part of a larger cell isn't valid unless it is the top-left corner
            for iy in range(photo.yFactor):
                for ix in range(photo.xFactor):
                    try:
                        occupiedRows[photo.gridRow+iy][photo.gridCol+ix] = photoIdx
                    except:
                        print("Error picmanager148 ", photo.gridRow, iy, photo.gridCol, ix)
                    if (ix != 0) and (iy != 0):
                        validCellRows[photo.gridRow+iy][photo.gridCol+ix] = False
            # Now rule out cells on the odd numbered rows if there is a double height photo above it
            if ((photo.gridRow % 2) == 0) and (photo.yFactor == 2):
                for ix in range(self.maxCols):
                    validCellRows[photo.gridRow+1][ix] = False
        # Debug
        __debugrob = False
        if __debugrob:
            print ("ReqFactors x,y ", xFactor, yFactor)
            for iy in range(self.maxRows):
                for ix in range(self.maxCols):
                    print ('{0: >2}'. format(occupiedRows[iy][ix]), end="")
                print ("   ", end="")
                for ix in range(self.maxCols):
                    print ("V " if validCellRows[iy][ix] else "  ", end="")
                print ("")
        return (validCellRows, occupiedRows)

    def checkForDoubleHeightCellInRow(self, row):
        for photo in self.photosInGrid:
            if (photo.gridRow == row) and (photo.yFactor == 2):
                return True
        return False
    
    def findPhotosToRemove(self, newXFactor, newYFactor):
        (validCellRows, occupiedRows) = self.getValidCells(newXFactor, newYFactor)
        candidatesToRemove = []
        # Add valid unoccupied cells to the candidate list
        isUnoccupied = False
        for iy in range(self.maxRows):
            for ix in range(self.maxCols):
                if validCellRows[iy][ix]:
                    if occupiedRows[iy][ix] == -1:
                        candidatesToRemove.append((iy, ix, datetime.datetime(1,1,1,1,1)))
                        isUnoccupied = True
                    else:
                        photoIdx = occupiedRows[iy][ix]
                        candidatesToRemove.append((iy, ix, self.photosInGrid[photoIdx].dateTimeAdded))
        # Sort the candidate list by age (empty cells have oldest age)
        candidatesByAge = sorted(candidatesToRemove, key = lambda tupYXDate: tupYXDate[2])
#        print (candidatesByAge)
        # Select photo to remove
        if isUnoccupied:
            picIdx1 = 0
            picIdx = 0
        else:
            picIdx1 = randNo(0,len(candidatesByAge)-1)
            picIdx = randNo(0,picIdx1)
        if picIdx >= len(candidatesByAge):
            print ("PicIdxOutOfRange", picIdx, len(candidatesByAge), picIdx1, isUnoccupied)
        topLeftCellToRemove = candidatesByAge[picIdx]
        topLeftRemovalRow = topLeftCellToRemove[0]
        topLeftRemovalCol = topLeftCellToRemove[1]
#        topLeftPhotoIdxToRemove = occupiedRows[topLeftCellToRemove[0]][topLeftCellToRemove[1]]
        # Find which cells are affected
        photoIdxsToRemove = []
        numRowsInvolved = 2 # if self.checkForDoubleHeightCellInRow(topLeftRemovalRow) else newYFactor
        numColsInvolved = newXFactor
        for iy in range(numRowsInvolved):
            for ix in range(numColsInvolved):
                try:
                    photoIdx = occupiedRows[topLeftRemovalRow+iy][topLeftRemovalCol+ix]
                    if (photoIdx != -1) and (not photoIdx in photoIdxsToRemove):
                        photoIdxsToRemove.append(photoIdx)
                        if numColsInvolved < self.photosInGrid[photoIdx].xFactor:
                            numColsInvolved = self.photosInGrid[photoIdx].xFactor
                except:
                    None
#        print ("PhotoIdxsToRemove", photoIdxsToRemove, "tlRemRow", topLeftRemovalRow, "tlRemCol", topLeftRemovalCol, "numRows", numRowsInvolved, "numCols", numColsInvolved)
        return (photoIdxsToRemove, topLeftRemovalRow, topLeftRemovalCol, numRowsInvolved, numColsInvolved)

    def findPhotosThatAreMoving(self, topLeftRemovalRow, topLeftRemovalCol, numRowsInvolved, numColsInvolved):
        # Photos that move are to the left of the removal cell
        photosToMove = []
        for phIdx in range(len(self.photosInGrid)):
            ph = self.photosInGrid[phIdx]
            if ph.gridRow >= topLeftRemovalRow and ph.gridRow < (topLeftRemovalRow + numRowsInvolved):
                if ph.gridCol < topLeftRemovalCol:
                    photosToMove.append(phIdx)
        return photosToMove

    def getPicItemsToAdd(self, xFactor, yFactor, insertionRow, numRowsInvolved, numColsInvolved):
        picItemsToAdd = []
        for rowIdx in range(numRowsInvolved // yFactor):
            for colIdx in range(numColsInvolved // xFactor):
                newPicItem = self.getNextPicItem(xFactor, yFactor)
                if newPicItem != None:
                    picItemsToAdd.append((newPicItem, insertionRow+rowIdx, colIdx))
#        print ("Adding", len(picItemsToAdd), numRowsInvolved, yFactor)
        return picItemsToAdd
        
    def setupChange(self):
        # Prep next bitmap
        curImgInfo = self.photoFileManager.getCurPhotoInfo()
        if curImgInfo.imgSize.height() > curImgInfo.imgSize.width():
            newYFactor = 2
            newXFactor = 1
        elif curImgInfo.rating >= 3:
            newYFactor = 2
            newXFactor = 2
        else:
            newYFactor = randNo(1,2)
            newXFactor = newYFactor
        # Find photos to remove to accommodate new photo(s)
        (self.photoIdxsToRemove, topLeftRemovalRow, topLeftRemovalCol, numRowsInvolved, numColsInvolved) = self.findPhotosToRemove(newXFactor, newYFactor)
        # Photos to move
        self.photoIdxsToMove = self.findPhotosThatAreMoving(topLeftRemovalRow, topLeftRemovalCol, numRowsInvolved, numColsInvolved)
        # Photos to add
        self.picItemsToAdd = self.getPicItemsToAdd(newXFactor, newYFactor, topLeftRemovalRow, numRowsInvolved, numColsInvolved)
#        print ("PhotosToAdd", self.picItemsToAdd)
        self.columnMovementDist = numColsInvolved

    def addNewPhotosToScene(self):
        # Add pixmaps to scene
        for picItem in self.picItemsToAdd:
            picItem[0].pixmap.pixmap_item.setVisible(False)
            self.masterScene.addItem(picItem[0].pixmap.pixmap_item)
#            print ("Added pixmap to scene", picItem[0].pixmap.pixmap_item)
    
    def instantInsert(self):
        for ph in self.picItemsToAdd:
            # Set pixmap start location
            newPixmap = ph[0].pixmap
            row = ph[1]
            col = ph[2]
            xFact = ph[0].xFactor
            endCoords = self.getCellTLCoords(row, col)
            startCoords = QPointF(endCoords.x()-self.cellSize.width()*xFact, endCoords.y())
            newPixmap.pixmap_item.setPos(endCoords)
            newPixmap.pixmap_item.setVisible(True)
            
    def instantMove(self):
        for phIdx in self.photoIdxsToMove:
            item = self.photosInGrid[phIdx]
            startCoords = self.getCellTLCoords(item.gridRow, item.gridCol)
            endCoords = self.getCellTLCoords(item.gridRow, item.gridCol + self.columnMovementDist)
            item.pixmap.pixmap_item.setPos(endCoords)
            
    def instantRemove(self):
        for phIdx in self.photoIdxsToRemove:
            item = self.photosInGrid[phIdx]
            startCoords = self.getCellTLCoords(item.gridRow, item.gridCol)
            endCoords = QPointF(startCoords.x()+self.cellSize.width()*item.xFactor, startCoords.y() + item.pixmap.pixmapSize.height() / 2)
            item.pixmap.pixmap_item.setPos(endCoords)
            item.pixmap.pixmap_item.setVisible(False)
        
        
    def addInsertionAnimation(self, animGroup):
        # Animation for added
#        print(">>>InsAnim")
        for ph in self.picItemsToAdd:
            # Set pixmap start location
            newPixmap = ph[0].pixmap
            row = ph[1]
            col = ph[2]
            xFact = ph[0].xFactor
            endCoords = self.getCellTLCoords(row, col)
            startCoords = QPointF(endCoords.x()-self.cellSize.width()*xFact, endCoords.y())
            newPixmap.pixmap_item.setPos(startCoords)
            newPixmap.pixmap_item.setVisible(True)
            # Animate in
            anim = QPropertyAnimation(newPixmap, b"pos")
            anim.setDuration(self.insertDuration)
            anim.setStartValue(startCoords)
            anim.setEasingCurve(QEasingCurve.Linear)
            anim.setEndValue(endCoords)
            animGroup.addAnimation(anim)
 #           print(row,col,xFact,endCoords,startCoords)
 #       print("<<InsAnim")
            
#        self.photosInGrid.append(PicItem(self.getNextPic(randNo(1,2),randNo(1,2)),0,0))
        # Decide on picture to remove
#        photosByAge = sorted(self.photosInGrid, key = lambda picItem: picItem.dateTimeAdded)

    def addMovementAnimation(self, animGroup):
#        print(">>MoveAnim")
        for phIdx in self.photoIdxsToMove:
            item = self.photosInGrid[phIdx]
            anim = QPropertyAnimation(item.pixmap, b"pos")
            anim.setDuration(self.moveDuration - item.gridCol * self.moveModifier)
            anim.setEasingCurve(QEasingCurve.Linear)
            startCoords = self.getCellTLCoords(item.gridRow, item.gridCol)
            endCoords = self.getCellTLCoords(item.gridRow, item.gridCol + self.columnMovementDist)
            anim.setStartValue(startCoords)
            anim.setEndValue(endCoords)
            animGroup.addAnimation(anim)
#            print(item.gridRow, item.gridCol,item.xFactor,endCoords,startCoords)
#        print("<<MoveAnim")

    def addRemovalAnimation(self, animGroup):
#        print(">>RemoveAnim")
        for phIdx in self.photoIdxsToRemove:
            item = self.photosInGrid[phIdx]
            anim = QPropertyAnimation(item.pixmap, b"scale")
            anim.setDuration(self.shrinkDuration)
            anim.setEasingCurve(QEasingCurve.Linear)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            animGroup.addAnimation(anim)
            anim = QPropertyAnimation(item.pixmap, b"pos")
            anim.setDuration(self.shrinkDuration)
            anim.setEasingCurve(QEasingCurve.Linear)
            startCoords = self.getCellTLCoords(item.gridRow, item.gridCol)
            endCoords = QPointF(startCoords.x()+self.cellSize.width()*item.xFactor, startCoords.y() + item.pixmap.pixmapSize.height() / 2)
            anim.setStartValue(startCoords)
            anim.setEndValue(endCoords)
            animGroup.addAnimation(anim)
 #           print(item.gridRow, item.gridCol,item.xFactor,endCoords,startCoords)
 #       print("<<RemoveAnim")
        
    def completeChange(self):
#        print ("Completing")
        # Change location on photos that have moved
        for phIdx in self.photoIdxsToMove:
            self.photosInGrid[phIdx].gridCol += self.columnMovementDist
        self.photoIdxsToMove = []
        
        # Remove reqd photos from list and scene
        photosToRemove = [self.photosInGrid[phIdx] for phIdx in self.photoIdxsToRemove]        
        for ph in photosToRemove:
            self.masterScene.removeItem(ph.pixmap.pixmap_item)
 #           print ("Removed pixmap from scene", ph.pixmap.pixmap_item)
            self.photosInGrid.remove(ph)
        self.photoIdxsToRemove = []

        # Add photo to grid
        for ph in self.picItemsToAdd:
            picItem = ph[0]
            row = ph[1]
            col = ph[2]
            picItem.gridRow = row
            picItem.gridCol = col
            self.photosInGrid.append(picItem)
        self.picItemsToAdd = []

        # Garbage collect
        gc.collect()        
    
