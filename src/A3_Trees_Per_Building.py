import csv

import matplotlib.pyplot as plt

import pandas as pd
import geopandas as gpd
import osmnx as ox
from pympler.garbagegraph import start_debug_garbage
# import osmnx.utils_geo
from pyproj import CRS
import matplotlib.pyplot as plt
import networkx as nx
from scipy.constants import point
from shapely.geometry import Point, LineString, Polygon
from shapely import wkt
import utils
import random
import math
from ultralytics import YOLO
import os, os.path
import cv2
import numpy as np
import skimage as ski
from sklearn.cluster import DBSCAN

import A3_StitchImprove
import osm_utils



def get_trees_per_building(buildings_gdf, trees_gdf, radius):

    trees_metric_gdf = trees_gdf.to_crs(epsg=3857)
    buildings_metric_gdf = buildings_gdf.to_crs(epsg=3857)

    # with open(trees_building_list_file, 'a') as file:

    max_tree = 0


    trees_in_building = []

    for idx, building in buildings_metric_gdf.iterrows():

        building_buffer = building.geometry.buffer(15)
        # building_centroid = building.geometry.centroid
        points_within = trees_metric_gdf[trees_metric_gdf.within(building_buffer)]
        print(f"Building {idx} / osmid:{building['osmid']}  Tree Count:{len(points_within)}")
        trees_in_building.append(len(points_within))
        max_tree = max(max_tree,len(points_within))

    print("max_tree", max_tree)
    buildings_gdf['trees'] = trees_in_building
    return buildings_gdf



if __name__ == "__main__":


    root = '/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/'
    shape_file = "Kypseli-All.shp"



    root_generated = os.path.join(root, "generated/")
    shape_file_name = os.path.splitext(os.path.basename(shape_file))[0]

    pathDataGenerated    = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/generated/temp/"

    # graph_file = shape_file_name+"-Graph-Walking.graphml"
    csv_file_residential_buildings = shape_file_name+"-Trees_Per-Building.csv"
    residentialBuildings_path = os.path.join(root_generated, shape_file_name+"-Residential-Buildings.gpkg")
    # residentialBuildings_path = os.path.join(root_generated, shape_file_name+"-Residential-Buildings.gpkg")
    residentialBuildings_A3 = os.path.join(root_generated, shape_file_name+"-Residential-Buildings-A3.gpkg")
    # trees_path = os.path.join(root_generated, shape_file_name+"-Residential-Buildings.gpkg")
    trees_path = os.path.join(pathDataGenerated,f"__Kypseli-All-GSV-Tree-Points-CROSSING-Intersections.gpkg")


    if os.path.exists(residentialBuildings_path):
        buildings_gdf = gpd.read_file(residentialBuildings_path)
    else:
        print(f"Buildings File not found. {residentialBuildings_path}")
        exit(0)

    if os.path.exists(trees_path):
        trees_gdf = gpd.read_file(trees_path)
    else:
        print(f"Buildings File not found. {trees_path}")
        exit(0)


    buildings_w_trees_gdf = get_trees_per_building(buildings_gdf, trees_gdf, 15 )
    buildings_w_trees_gdf.to_file(residentialBuildings_path, layer='locations', driver="GPKG")
    buildings_w_trees_gdf.to_file(residentialBuildings_A3, layer='locations', driver="GPKG")

    if True:
        exit(0)
