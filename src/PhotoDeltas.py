import json

class PhotoDeltas:
    def __init__(self, deltaFileName):
        self._deltaFileName = deltaFileName
        self.deltas = {}
        jsonDeltas = "{}"
        try:
            with open(self._deltaFileName, "r") as deltaFile:
                jsonDeltas = deltaFile.read()
                jsonDeltas = jsonDeltas.strip()
                if jsonDeltas[-1] == ",":
                    jsonDeltas = jsonDeltas[:-1]
                jsonDeltas = "{" + jsonDeltas + "}"
        except Exception as excp:
            print("PhotoDeltas: can't read deltas file", self._deltaFileName, excp)
        try:
            tmpDeltas = json.loads(jsonDeltas)
            for delta in deltas:
                if "filename" in delta and "changes" in delta:
                    self.deltas[delta["filename"]] = delta["changes"]
        except Exception as excp:
            print("PhotoDeltas: can't load json from deltas", excp)

    def addDeltaToPhoto(self, photoName, changeJson):
        try:
            # Add locally
            self.deltas[photoName] = json.loads(changeJson)

            for k,v in self.deltas.items():
                print(k,v)
        except Exception as excp:
            print("PhotoDeltas: failed to store locally", excp)
        try:
            # Open the delta file
            with open(self._deltaFileName, 'a') as deltaFile:
                deltaStr = '{"filename":"' + photoName + '", "changes":' + changeJson + "},"
                # Write to the end of the file
                deltaFile.write(deltaStr + "\n")
        except Exception as excp:
            print("PhotoDeltas: failed to write change to ", self._deltaFileName)

    def setRating(self, photoManager, rating):
        self.addDeltaToPhoto(photoManager.getCurPhotoFilename(), '{"rating":' + str(rating) + '}')

    def setLocationError(self, photoManager):
        self.addDeltaToPhoto(photoManager.getCurPhotoFilename(), '{"locerr":"true"}')

    def setDateError(self, photoManager):
        self.addDeltaToPhoto(photoManager.getCurPhotoFilename(), '{"dateerr":"true"}')

    def applyDeltasToPhotoInfo(self, fileName, photoInfo):
        # print("PhotoDeltas: Looking up", fileName)
        if fileName in self.deltas:
            try:
                changes = self.deltas[fileName]
                print("PhtooDeltas: found change record for filename", fileName, changes, "rating" in changes)
                if "rating" in changes:
                    photoInfo.setRating(changes["rating"])
            except Exception as excp:
                print ("PhotoDeltas: unable to apply changes")
