

import matplotlib.pyplot as plt

import geopandas as gpd
import osmnx as ox
# import osmnx.utils_geo
from pyproj import CRS
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import Point, LineString, Polygon
from shapely import wkt
import utils
import random
import math

if __name__ == "__main__":

    import os, os.path


    print("Starting...")

    pathRoot = "/home/nono/Documents/workspaces/cpp/darknet/Training/Athens-3-30-300-Panorama-Grey/"
    pathNames		= os.path.join(pathRoot,"Athens-3-30-300-Panorama-Grey.names")
    pathImage		= os.path.join(pathRoot,"panorama-final-depth/img_0w4VcFFiFSGZWk022DL-zg_panorama.png")
    pathResults		= os.path.join(pathRoot,"panorama-final-results/")



