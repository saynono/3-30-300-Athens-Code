

import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
import osmnx as ox
import os, os.path
import utils
from geopy.distance import distance as geopy_distance
from pyproj import Geod

def create_gsv_map(metadata_df):

    gdf = gpd.GeoDataFrame(
        metadata_df,
        geometry=[Point(xy) for xy in zip(metadata_df['longitude'], metadata_df['latitude'])],
        crs="EPSG:4326"  # Use WGS84 (latitude/longitude) CRS
    )

    return gdf

def get_tree_points(origin, tree_list, multi=1, max_in_m=0):
    tree_points = []
    origin_rev = (origin[1],origin[0])
    for row in tree_list:
        angle = utils.map_value(row[0],0,2400,-30,330)
        distance = (row[2]/100.0)
        if multi != 0:
            distance_new = distance*multi
            distance_new = distance+max_in_m
            distance = min(distance_new,distance+max_in_m)
        # print(f"========> {origin_rev}")
        tp = geopy_distance(meters=distance).destination(origin_rev, angle)
        tree_points.append(Point(tp.longitude,tp.latitude))
        # lon2, lat2, _ = Geod.fwd_intermediate(origin[0], origin[1], azi1=angle, dist=distance)
        # tree_points.append(Point(lon2, lat2))
    return tree_points


def add_trees_to_gsv_map(pano_id, tree_list, metadata_df, lines = False):
    # gdf = gpd.GeoDataFrame(
    #     metadata_df,
    #     geometry=[Point(xy) for xy in zip(metadata_df['longitude'], metadata_df['latitude'])],
    #     crs="EPSG:4326"  # Use WGS84 (latitude/longitude) CRS
    # )

    pano_df = utils.find_entry_by_panoID(metadata_df,pano_id)
    # print(pano_df)

    origin = (pano_df.iloc[0].longitude,pano_df.iloc[0].latitude)
    print(origin)
    tree_points = []
    # for row in tree_list:
    #     angle = utils.map_value(row[0],0,2400,-30,330)
    #     distance = row[2]/100.0
    #     destination = geopy_distance(meters=distance).destination(origin, angle)
    #     destination2 = geopy_distance(meters=distance*2).destination(origin, angle)
    #     if not lines:
    #         tree_point = Point(destination.longitude, destination.latitude)
    #         tree_points.append(tree_point)
    #     else:
    #         tree_line = LineString([(pano_df.iloc[0].longitude,pano_df.iloc[0].latitude), (destination.longitude, destination.latitude), (destination2.longitude, destination2.latitude)])
    #         tree_points.append(tree_line)

    if not lines:
        tree_points = get_tree_points(origin, tree_list)
    else:
        tps = get_tree_points(origin,tree_list,1.4, 5)
        for tp in tps:
            tree_line = LineString([origin, tp])
            tree_points.append(tree_line)


    gdf_trees = gpd.GeoDataFrame(
        geometry=tree_points,
        crs="EPSG:4326"
    )

    gdf_trees['panoID'] = [pano_id] * len(tree_list)
    gdf_trees['distance'] = [item[2] for item in tree_list]
    gdf_trees['angle'] = [utils.map_value(item[0],0,2400,-30,330) for item in tree_list]
    gdf_trees['x'] = [item[0] for item in tree_list]
    gdf_trees['y'] = [item[1] for item in tree_list]
    return gdf_trees

# Find all intersections
def find_intersections(gdf):
    # Create an empty GeoDataFrame to store intersection points
    intersections = []

    # Iterate over all unique pairs of lines
    for i, line1 in enumerate(gdf.geometry):
        for j, line2 in enumerate(gdf.geometry):
            if i < j:  # Avoid duplicate pairs and self-comparison
                intersection = line1.intersection(line2)
                if not intersection.is_empty:  # Only add non-empty intersections
                    # print(f"Intersction {i} x {j} => {intersection}")
                    if intersection.geom_type == 'Point':  # Add single intersection points
                        if not intersection.equals(Point(line1.coords[0])) and not intersection.equals(Point(line2.coords[0])):
                            intersections.append(intersection)
                    # elif intersection.geom_type == 'MultiPoint':  # Add multiple intersection points
                    #     intersections.extend(intersection.geoms)

    # Create a GeoDataFrame of intersection points
    intersection_gdf = gpd.GeoDataFrame(geometry=intersections, crs=gdf.crs)
    return intersection_gdf
