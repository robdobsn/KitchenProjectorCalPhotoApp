from PIL import (Image, ExifTags)
from PyQt5.QtCore import (QSize)
import re
from bitstring import ConstBitStream

class PhotoInfo():
    imgSize = QSize()
    rotationAngle = 0
    rating = -1

    def __init__(self):
        self.imgSize = QSize()
        self.rotationAngle = 0
        self.rating = -1    

    def printEXIFinfo(self, imgFileName):
            img = Image.open(imgFileName)
            exif_data = img._getexif()
            for k, v in exif_data.items():
                print (ExifTags.TAGS[k],"(",k,")",v)
        
    def setFromFile(self, imgFileName):
        # Get the EXIF data (contains orientation)
        try:
            img = Image.open(imgFileName)
            exif_data = img._getexif()
            orientation = exif_data[274] if 274 in exif_data else 0
            rotationAngle = 0
            if orientation == 3: rotationAngle = 180
            elif orientation == 6: rotationAngle = 90
            elif orientation == 8: rotationAngle = 270
            width = img.size[0]
            height = img.size[1]
            if orientation == 6 or orientation == 8:
                width = img.size[1]
                height = img.size[0]
        except:
            width = 100
            height = 100
            rotationAngle = 0
            
        # Get the XMP data (contains rating)
        xmpStr = self.extractXMP(imgFileName)
        rating = -1
        try:
            if len(xmpStr) != 0:
                m = re.search('\<xmp:Rating\>\w*?(\d)', xmpStr)
                if m != None:
                    if len(m.groups()) == 1:
                        rating = int(m.group(1))
        except:
            rating = -1

        self.imgSize = QSize(width, height)
        self.rotationAngle = rotationAngle
        self.rating = rating
#        print(imgFileName, "Size", width, height, "Rot", rotationAngle, "Rating", rating)

    def extractXMP(self, filename):
        xmpStr = ""        
        # Can initialise from files, bytes, etc.
        try:
            s = ConstBitStream(filename = filename)
            # Search for ":xmpmeta" string in file
            keepSearching = True
            while keepSearching:
                keepSearching = False
                colonXmpmetaInHexStr = '0x3a786d706d657461'
                foundSt = s.find(colonXmpmetaInHexStr, bytealigned=True)
                if foundSt:
                    byteStart = (int(foundSt[0])//8)
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
                        byteEnd = (int(foundEnd[0])//8)
                        s.bytepos = byteStart
        #                print("Found end code at byte offset %d." % byteEnd)
                        xmpBytes = s.readlist(str(byteEnd-byteStart+len(prefix)//2+9) +"*uint:8")
                        xmpStr = ''.join(chr(i) for i in xmpBytes)
                        #if "Rating" in xmpStr:
        #                print (xmpStr)
        except:
            xmpStr = ""
        return xmpStr
    