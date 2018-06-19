
import exifread
from PhotoInfo import PhotoInfo

#path_name = "p:\\PhotosMain\\1980-1989\\19880101_000000_0000_2T47SkiingItaly_027_SCAN_T47.jpg"
#path_name = "P:\\PhotosMain\\2008\\07\\20080503_174444_IMG_0662_31293.JPG"
# path_name = "P:\\PhotosMain\\2008\\07\\20080512_192615_IMG_0675_31306.JPG"
path_name = "P:\\PhotosMain\\2012\\03\\20120330_111351_IMG_7073_33912.JPG"

f = open(path_name, 'rb')

# Return Exif tags
tags = exifread.process_file(f)
f.close()

for tag in tags.keys():
    if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
        print("Key: %s, value %s" % (tag, tags[tag]))


# Read using module
photoInfo = PhotoInfo()
photoInfo.setFromFile(path_name)

print("Extracted items ...............")
for k, v in photoInfo.imgInfo.items():
    print(k, v)