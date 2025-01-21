# The following film has been modified from its original version. It has been formatted to fit this screen.

# This program is used to calculate the green view index based on the collected metadata. The
# Object based images classification algorithm is used to classify the greenery from the GSV imgs
# in this code, the meanshift algorithm implemented by pymeanshift was used to segment image
# first, based on the segmented image, we further use the Otsu's method to find threshold from
# ExG image to extract the greenery pixels.

# For more details about the object based image classification algorithm
# check: Li et al., 2016, Who lives in greener neighborhoods? the distribution of street greenery and it association with residents' socioeconomic conditions in Hartford, Connectictu, USA

# This program implementing OTSU algorithm to chose the threshold automatically
# For more details about the OTSU algorithm and python implmentation
# cite: http://docs.opencv.org/trunk/doc/py_tutorials/py_imgproc/py_thresholding/py_thresholding.html

import os
import time
import itertools
from PIL import Image
from io import BytesIO

import requests
import numpy as np
import pymeanshift as pms
from dotenv import load_dotenv
import re
import utils

from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.utils.download_util import load_file_from_url

from realesrgan import RealESRGANer
from realesrgan.archs.srvgg_arch import SRVGGNetCompact


from directories import PANO_DIR, GVI_DIR, format_folder_name

load_dotenv()


def loadGSVImage(imgCachePath, URL):
    if os.path.exists(imgCachePath):
        print("Loading cached image file: ", imgCachePath )
        return Image.open(imgCachePath)
    else:
        print("Loading image from server: ", URL)
        # let the code to pause by 1s, in order to not go over data limitation of Google quota
        time.sleep(0.25)
        response = requests.get(URL)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        try:
            img.save(imgCachePath)
            print("Saved image to: ", imgCachePath )
        except IOError:
            print("Cannot save image! ", imgCachePath)
        return img

    return None


def download_panoramas(GSVinfoFolder, greenmonth, GSVcacheFolder, GSVpanoramaFolder, keylist):


    # set a series of heading angle
    photos_per_panorama = 6
    fov = 360/photos_per_panorama
    gsv_width = round(400.0/60.0*fov)*2
    gsv_width_total = photos_per_panorama*gsv_width
    gsv_key = keylist[0]
    # np.arange(0, 10, 1)
    headingArr = 360/photos_per_panorama*np.arange(0,photos_per_panorama,1)
    pixel_step = photos_per_panorama
    # number of GSV images for Green View calculation, in my original Green View View paper, I used 18 images, in this case, 6 images at different horizontal directions should be good.
    numGSVImg = len(headingArr)*1.0
    pitch = 0
    
    # the input GSV info should be in a folder
    if not os.path.isdir(GSVinfoFolder):
        print('You should input a folder for GSV metadata')
        return
    else:
        allTxtFiles = os.listdir(GSVinfoFolder)
        panoramaCntTotal = 0
        panoramaCntProcessed = 0
        panoramaCntDownloaded = 0
        for txtfile in allTxtFiles:
            if not txtfile.endswith('.txt'):
                continue
            match = re.search(r'_end(\d+)', txtfile)
            if match:
                last_number = int(match.group(1))
                panoramaCntTotal = max(panoramaCntTotal,last_number)

        print('Total Panoramas to download:', panoramaCntTotal)
        # return

        for txtfile in allTxtFiles:
            if not txtfile.endswith('.txt'):
                continue
            
            txtfilename = os.path.join(GSVinfoFolder,txtfile)
            lines = open(txtfilename,"r")
            
            # create empty lists, to store the information of panos,and remove duplicates
            panoIDLst = []
            panoDateLst = []
            panoLonLst = []
            panoLatLst = []
            
            # loop all lines in the txt files
            for line in lines:
                metadata = line.split(" ")
                panoID = metadata[1]
                panoDate = metadata[3]
                month = panoDate[-2:]
                lon = metadata[5]
                lat = metadata[7][:-1]
                
                # print (lon, lat, month, panoID, panoDate)
                
                # in case, the longitude and latitude are invalide
                if len(lon)<3:
                    continue
                
                # only use the months of green seasons
                if month not in greenmonth:
                    continue
                else:
                    panoIDLst.append(panoID)
                    panoDateLst.append(panoDate)
                    panoLonLst.append(lon)
                    panoLatLst.append(lat)

            # check whether the file already generated, if yes, skip. Therefore, you can run several process at same time using this code.
            #TODO: removed this for now because it is annoying
            # if os.path.exists(GreenViewTxtFile):
            #     continue

            cntSpots = len(panoIDLst)
            for i in range(cntSpots):
                panoDate = panoDateLst[i]
                panoID = panoIDLst[i]
                lat = panoLatLst[i]
                lon = panoLonLst[i]

                cntPerSpot = 0

                panoramaCachePath = f"__img_{panoID}_panorama.jpg"
                panoramaCachePath = os.path.join(GSVpanoramaFolder,panoramaCachePath)
                createPanorama = not os.path.exists(panoramaCachePath)
                if(createPanorama):
                     # = photos_per_panorama*
                    panorama = Image.new('RGB', (gsv_width_total, 400))
                    # panorama = Image.new('RGB', (2400, 400))
                    panoramaCntDownloaded += 1
                x_offset = 0

                for heading in headingArr:
                    # print(round(100*(i/cntSpots),2), "%  ", cntPerSpot, "/", headingArr.size, "Heading is: ", heading)
                    cntPerSpot += 1

                    try:

                        URL = f"http://maps.googleapis.com/maps/api/streetview?size={gsv_width}x400&pano=%s&fov={fov}&heading=%d&pitch=%d&sensor=false&key={gsv_key}"%(panoID,heading,pitch)
                        imgCachePath = f"__img_{panoID}_{heading}_{pitch}.jpg"
                        imgCachePath = os.path.join(GSVcacheFolder,imgCachePath)
                        img = loadGSVImage(imgCachePath, URL)
                        if createPanorama:
                            panorama.paste(img, (x_offset, 0))
                            x_offset += img.size[0]

                    # if the GSV images are not download successfully or failed to run, then return a null value
                    except Exception as e:
                        print(f"Error type: {type(e).__name__}")
                        print(f"Error message: {str(e)}")
                        break

                if createPanorama:
                    panorama.save(panoramaCachePath)

                panoramaCntProcessed += 1

                print(round(100*(panoramaCntProcessed/panoramaCntTotal),2), "%  [", panoramaCntDownloaded, " set downloads] ", "\tPanorama-file: ", panoramaCachePath)



# ------------------------------Main function-------------------------------
# if __name__ == "__main__":
#     area_number = 1
#     # GSVinfoRoot = 'MYPATH//spatial-data/metadata'
#     GSVinfoRoot = PANO_DIR / format_folder_name(area_number)
#     # outputTextPath = r'MYPATH//spatial-data/greenViewRes'
#     outputTextPath = GVI_DIR / format_folder_name(area_number)
#     # greenmonth = ['01','02','03','04','05','06','07','08','09','10','11','12']
#     greenmonth = ['05','06','07','08','09']
#     # key_file = 'MYPATH/src/src/keys.txt'
#
#     GreenViewComputing_ogr_6Horizon(GSVinfoRoot, outputTextPath, greenmonth)
#

# def get_keys(key_file):
#     lines = open(key_file,"r")
#     keylist = []
#     for line in lines:
#         key = line[:-1]
#         keylist.append(key)
#
#     print('The key list is:=============', keylist)
#
#     return keylist

# ------------------------------Main function-------------------------------
if __name__ == "__main__":

    import os,os.path
    import itertools

    root = os.path.abspath('../3-30-300-Athens-Data/')

    GSVcache = os.path.join(root, './GSV-Data/panodata-cache')
    GSVpanoramaFolder = os.path.join(root, './GSV-Data/panoramas-final-new')
    GSVinfoRoot = os.path.join(root, 'maps/Kypseli-All/metadata/')
    # outputTextPath = os.path.join(root, './spatial-data/Kypseli-Center/greenViewRes')
    greenmonth = ['01','02','03','04','05','06','07','08','09','10','11','12']
    # greenmonth = ['04','05','06','07','08','09','10','11']

    if not os.path.exists(GSVcache):
        os.makedirs(GSVcache)
    if not os.path.exists(GSVpanoramaFolder):
        os.makedirs(GSVpanoramaFolder)


    # print(f"GreenViewTxtFile: {outputTextPath}")



    # read the Google Street View API key files, you can also replace these keys by your own
    # api_key = os.environ["GOOGLE_MAPS_API_KEY"]
    # keylist = [api_key]

    key_file = './keys.txt'
    keylist = utils.get_keys(key_file)

    download_panoramas(GSVinfoRoot, greenmonth, GSVcache, GSVpanoramaFolder, keylist)

    # GreenViewComputing_ogr_6Horizon(GSVinfoRoot,outputTextPath, greenmonth, key_file)