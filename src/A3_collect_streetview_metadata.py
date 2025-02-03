# The following film has been modified from its original version. It has been formatted to fit this screen.

# This function is used to collect the metadata of the GSV panoramas based on the sample point shapefile
# Copyright(C) Xiaojiang Li, Ian Seiferling, Marwa Abdulhai, Senseable City Lab, MIT 

import json

# import urllib
import numpy as np
from urllib.request import urlopen
import xmltodict
# from io import StringIO
# import ogr
# import osr
from osgeo import ogr, osr
import time
import os, os.path
from tqdm import tqdm
from dotenv import load_dotenv
import requests
import utils

from directories import POINT_GRIDS, PANO_DIR, format_folder_name


load_dotenv()


def GSVpanoMetadataCollector(samplesFeatureClass, num, ouputTextFolder, api_key,
                             replace_existing=False):
    '''
    This function is used to call the Google API url to collect the metadata of
    Google Street View Panoramas. The input of the function is the shpfile of the create sample site, the output
    is the generate panoinfo matrics stored in the text file 
    
    Parameters: 
        samplesFeatureClass: the shapefile of the create sample sites
        num: the number of sites proced every time
        ouputTextFolder: the output folder for the panoinfo
        
    '''
    if not os.path.exists(ouputTextFolder):
        os.makedirs(ouputTextFolder)
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    
    # change the projection of shapefile to the WGS84
    dataset = driver.Open(str(samplesFeatureClass))
    layer = dataset.GetLayer()
    
    sourceProj = layer.GetSpatialRef()
    targetProj = osr.SpatialReference()
    targetProj.ImportFromEPSG(4326)
    transform = osr.CoordinateTransformation(sourceProj, targetProj)
    
    # loop all the features in the featureclass
    feature = layer.GetNextFeature()
    featureNum = layer.GetFeatureCount()
    batch = featureNum/num
    batch = int(np.ceil(batch))
    
    for b in range(batch):
        # for each batch process num GSV site
        start = b*num
        end = (b+1)*num
        if end > featureNum:
            end = featureNum
        
        ouputTextFile = 'Pnt_start%s_end%s.txt'%(start,end)
        ouputGSVinfoFile = os.path.join(ouputTextFolder,ouputTextFile)
        
        # skip over those existing txt files
        if os.path.exists(ouputGSVinfoFile) and replace_existing:
            continue
        
        time.sleep(1)
        
        with open(ouputGSVinfoFile, 'w') as panoInfoText:
            # process num feature each time
            for i in tqdm(range(start, end), desc="Fetching Panorama IDs"):
                feature = layer.GetFeature(i)        
                geom = feature.GetGeometryRef()
                
                # trasform the current projection of input shapefile to WGS84
                #WGS84 is Earth centered, earth fixed terrestrial ref system
                geom.Transform(transform)
                lon = geom.GetX()
                lat = geom.GetY()
                
                # get the meta data of panoramas 
                urlAddress = format_metadata_url(lon, lat, api_key)
                response = requests.get(urlAddress)
                data = response.json()
                
                # Take a Breath
                time.sleep(0.05)
                
                # in case there is not panorama in the site, therefore, continue
                if data['pano_id']==None:
                    continue
                else:
                    panoId = data["pano_id"]
                    panoDate = data["date"]
                    panoLat = data["location"]["lat"]
                    panoLon = data["location"]["lng"]
                    lineTxt = 'panoID: %s panoDate: %s longitude: %s latitude: %s\n'%(panoId, panoDate, panoLon, panoLat)
                    panoInfoText.write(lineTxt)
                    
        panoInfoText.close()


def format_metadata_url(lon, lat, api_key):
    base_url = "https://maps.googleapis.com/maps/api/streetview/metadata?"
    url = base_url + f"location={lon},{lat}"
    url += f"&key={api_key}"
    return url

#
# def metadata_community_area(area_number=1, batch_size=1000,
#                             replace_existing=False):
#     inputShp = POINT_GRIDS / format_folder_name(area_number)
#     outputTxt = PANO_DIR / format_folder_name(area_number)
#     GSVpanoMetadataCollector(inputShp, batch_size, outputTxt,
#                              replace_existing=replace_existing)
#
#
# # ------------Main Function -------------------
# if __name__ == "__main__":
#     metadata_community_area(replace_existing=False)

    # ------------Main Function -------------------
if __name__ == "__main__":
    import os, os.path

    # root = './spatial-data/Kypseli-All/'
    root = '/Users/nono/Documents/workspaces/GIS/3-30-300-Athens-data/maps/Kypseli-All/'
    # inputShp = os.path.join(root, 'Kypseli-All.shp')
    inputShp = os.path.join(root, 'Kypseli-Center-Streets-10m.shp')

    key_file = './keys.txt'
    keylist = utils.get_keys(key_file)
    api_key = keylist[0]

    # api_key = os.environ["GOOGLE_MAPS_API_KEY"]


    # inputShp = '/Users/nono/Documents/workspaces/GIS/3-30-300-Athens/maps/Kypseli-All/Kypseli-All-Outlines.shp'
    outputTxt = os.path.join(root, 'metadata/')

    GSVpanoMetadataCollector(inputShp,1000, api_key, outputTxt)

