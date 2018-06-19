from PIL import (Image, ExifTags)
from PyQt5.QtCore import (QSize)
import re
from bitstring import ConstBitStream
import untangle
import datetime
import arrow
import xmltodict
import json
import dateutil.parser
import exifread
import os

class PhotoInfo():
    exifData = None
    imgSize = None
    rating = None
    fileName = None
    mainDate = None
    rotationAngle = 0
    imgInfo = {}

    def setFromFile(self, imgFileName):
        self.fileName = os.path.basename(imgFileName)
        # Read exif data if present
        try:
            with open(imgFileName, 'rb') as imgFile:
                self.exifData = exifread.process_file(imgFile)
                # Extract data from exif
                self.imgInfo["resolution"] = self.getResolutionFromEXIF(self.exifData)
                self.imgInfo["originalDate"] = self.getTimeFromEXIF(self.exifData, "EXIF DateTimeOriginal")
                self.imgInfo["digitizedDate"] = self.getTimeFromEXIF(self.exifData, "EXIF DateTimeDigitized")
                self.imgInfo["cameraMake"] = self.getStringFromEXIF(self.exifData, "Image Make")
                self.imgInfo["cameraModel"] = self.getStringFromEXIF(self.exifData, "Image Model")
                self.imgInfo["rotationAngle"], self.imgInfo["mirrored"] = self.getRotationFromEXIF(self.exifData)
        except Exception as excp:
            print("Cannot load exif data", excp, imgFileName)

        # Read xmp data if present
        try:
            # Get the XMP data (contains rating)
            xmpStr = self.extractXMP(imgFileName)
            # Convert to dict
            try:
                if len(xmpStr) > 0:
                    xmpData = xmltodict.parse(xmpStr)
                    if "x:xmpmeta" in xmpData:
                        xmpMeta = xmpData["x:xmpmeta"]
                        if "rdf:RDF" in xmpMeta:
                            rdfRDF = xmpMeta["rdf:RDF"]
                            if "rdf:Description" in rdfRDF:
                                rdfDescription = rdfRDF["rdf:Description"]
                                self.imgInfo["xmpCreateDate"] = self.getDateFromISO(rdfDescription, "@xmp:CreateDate")
                                self.imgInfo["xmpModifyDate"] = self.getDateFromISO(rdfDescription, "@xmp:ModifyDate")
                                self.imgInfo["xmpRawFileName"] = self.getStringFromXMP(rdfDescription, "@crs:RawFileName")
                                self.imgInfo["xmpRating"] = self.getIntFromXMP(rdfDescription, "@xmp:Rating")
            except Exception as excp:
                print("Cannot convert xmp to dict", excp, imgFileName)
        except Exception as excp:
            print("Cannot load xmp data", excp, imgFileName)

        if "resolution" in self.imgInfo:
            self.imgSize = QSize(self.imgInfo["resolution"][0], self.imgInfo["resolution"][1])
        if "rotationAngle" in self.imgInfo:
            self.rotationAngle = self.imgInfo["rotationAngle"]
        if "xmpRating" in self.imgInfo:
            self.rating = self.imgInfo["xmpRating"]
        if "originalDate" in self.imgInfo and self.imgInfo["originalDate"] is not None:
            self.mainDate = self.imgInfo["originalDate"]
        elif "xmpCreateDate" in self.imgInfo and self.imgInfo["xmpCreateDate"] is not None:
            self.mainDate = self.imgInfo["xmpCreateDate"]
        elif "digitizedDate" in self.imgInfo and self.imgInfo["digitizedDate"] is not None:
            self.mainDate = self.imgInfo["digitizedDate"]
        elif "xmpModifyDate" in self.imgInfo and self.imgInfo["xmpModifyDate"] is not None:
            self.mainDate = self.imgInfo["xmpModifyDate"]
        if self.mainDate is None:
            print("No dates found in file", imgFileName)
            print("...........................................................")
            print(self.imgInfo)
            print(self.exifData)
            print("...........................................................")

    def extractXMP(self, filename):
        xmpStr = ""
        # Can initialise from files, bytes, etc.
        try:
            s = ConstBitStream(filename=filename)
            # Search for ":xmpmeta" string in file
            keepSearching = True
            while keepSearching:
                keepSearching = False
                colonXmpmetaInHexStr = '0x3a786d706d657461'
                foundSt = s.find(colonXmpmetaInHexStr, bytealigned=True)
                if foundSt:
                    byteStart = (int(foundSt[0]) // 8)
                    # The start of data can be "<xmp:xmpmeta" or "<x:xmpmeta"
                    s.bytepos = byteStart - 4
                    prevals = s.peeklist("4*uint:8")
                    prestr = ''.join(chr(i) for i in prevals)
                    #            print (prestr, prestr[2:])
                    if prestr == "<xmp":
                        byteStart = byteStart - 4
                        prefix = "0x3c2f786d70"  # "<\xmp" in hex
                    elif prestr[2:] == "<x":
                        byteStart = byteStart - 2
                        prefix = "0x3c2f78"  # "<\x" in hex
                    else:
                        #                print ("Cont")
                        keepSearching = True
                        continue
                    #            print("Found start code at byte offset %d." % byteStart)
                    foundEnd = s.find(prefix + colonXmpmetaInHexStr, bytealigned=True)
                    if foundEnd:
                        byteEnd = (int(foundEnd[0]) // 8)
                        s.bytepos = byteStart
                        #                print("Found end code at byte offset %d." % byteEnd)
                        xmpBytes = s.readlist(str(byteEnd - byteStart + len(prefix) // 2 + 9) + "*uint:8")
                        xmpStr = ''.join(chr(i) for i in xmpBytes)
                        # if "Rating" in xmpStr:
                        # print("FOUND XMP STRING " + xmpStr)
        except:
            xmpStr = ""
        return xmpStr

    # def printEXIFinfo(self, imgFileName):
    #         img = Image.open(imgFileName)
    #         exif_data = img._getexif()
    #         for k, v in exif_data.items():
    #             print("EXIF info", ExifTags.TAGS[k],"(",k,")",v)

    def getResolutionFromEXIF(self, exifData):
        xRes = 0
        yRes = 0
        try:
            if "EXIF ExifImageWidth" in exifData:
                xRes = exifData["EXIF ExifImageWidth"].values[0]
            if "EXIF ExifImageLength" in exifData:
                yRes = exifData["EXIF ExifImageLength"].values[0]
        except Exception as excp:
            print("getResolutionFromEXIF", excp)
        return (xRes, yRes)

    def getTimeFromEXIF(self, exifData, tagStr):
        retTime = None
        try:
            if tagStr in exifData:
                timeStr = exifData[tagStr].values
                retTime = datetime.datetime.strptime(timeStr, "%Y:%m:%d %H:%M:%S")
        except Exception as excp:
            print("getTimeFromEXIF", excp)
        return retTime

    def getStringFromEXIF(self, exifData, tagStr):
        retStr = None
        try:
            if tagStr in exifData:
                retStr = exifData[tagStr].values
        except Exception as excp:
            print("getStringFromEXIF", excp)
        return retStr

    def getRotationFromEXIF(self, exifData):
        mirrored = False
        rotation = 0
        try:
            if "Image Orientation" in exifData:
                orientation = exifData["Image Orientation"].values[0]
                if orientation == 2 or orientation == 4 or orientation == 5 or orientation == 7:
                    mirrored = True;
                if orientation == 3:
                    rotation = 180
                elif orientation == 4 or orientation == 6 or orientation == 7:
                    rotation = 90
                elif orientation == 5 or orientation == 8:
                    rotation = 270
        except Exception as excp:
            print("getRotationFromEXIF", excp)
        return rotation, mirrored

    def getDateFromISO(self, xmpDescription, fieldName):
        isoDateStr = self.getStringFromXMP(xmpDescription, fieldName)
        theDate = None
        if isoDateStr is not "":
            try:
                theDate = dateutil.parser.parse(isoDateStr)
            except Exception as excp:
                print("Cannot convert ISO date string ", isoDateStr, excp)
        return theDate

    def getIntFromXMP(self, xmpDescription, fieldName):
        numStr = self.getStringFromXMP(xmpDescription, fieldName)
        val = None
        if numStr is not "":
            try:
                if fieldName in xmpDescription:
                    val = int(xmpDescription[fieldName])
            except Exception as excp:
                print("Cannot get int from string", numStr, excp)
        return val

    def getStringFromXMP(self, xmpDescription, fieldName):
        str1 = ""
        try:
            if fieldName in xmpDescription:
                str1 = xmpDescription[fieldName]
        except Exception as excp:
            print("Cannot get string from XMP", fieldName, excp)
        return str1

    def setRating(self, rating):
        self.rating = rating
