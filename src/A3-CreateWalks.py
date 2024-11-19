import geopandas as gpd
import osmnx as ox
from pyproj import CRS
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import linemerge
import utils


def list_all_gvs_points(walk_gdf, gsv_points_gdf):

    print(f"walk_gdf.crs: {walk_gdf.crs}    gsv_points_gdf.crs: {gsv_points_gdf.crs}")


    dist = 9 #meters

    walk_gdf_metric = walk_gdf.to_crs("EPSG:3857") # metric conversion
    merged = walk_gdf_metric.geometry.unary_union
    # Step 2: If needed, merge the MultiLineString into a single LineString
    if merged.geom_type == "MultiLineString":
        merged = linemerge(merged)

    walk_gdf_metric = gpd.GeoDataFrame(
        geometry=[merged],
        crs="EPSG:3857"
    )
    buffer_geom = walk_gdf_metric.geometry.buffer(dist)

    gdf_buffer = gpd.GeoDataFrame(
        gsv_points_gdf[['panoID']],
        geometry=buffer_geom,
        crs="EPSG:3857"
    )
    gdf_buffer = gdf_buffer.to_crs(gsv_points_gdf.crs)

    print(f"===> {gdf_buffer.crs}   gsv_points_gdf: {gsv_points_gdf.crs}")

    points_within_buffer = gsv_points_gdf[gsv_points_gdf.within(gdf_buffer.geometry.unary_union)]
    print(f"Solution: {len(points_within_buffer)}   {points_within_buffer.head}")


    # gdf_points = gpd.GeoDataFrame(
    #     # gsv_points_gdf[['panoID']],
    #     geometry=points_within_buffer,
    #     # crs="EPSG:3857"
    # )

    # walk_gdf = walk_gdf.to_crs("EPSG:4326")

    return points_within_buffer

if __name__ == "__main__":
    import os, os.path

    path_root = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Walks/"
    path_gsv_points = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/generated/Kypseli-All-GSV-Points.gpkg"
    path_metadata_selected = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/metadata"

    metadata_df = utils.load_all_csvs(path_metadata_selected)
    gsv_points_gdf = utils.create_gsv_map(metadata_df)
    # gdf_gsv_points.to_file(path_gsv_points, layer='locations', driver="GPKG")

    walk_id = "Walk-Team-01"
    path_walk_02 = os.path.join(path_root, f"{walk_id}-edges.gpkg")
    path_walk_gsv_points = os.path.join(path_root, f"{walk_id}-GSV-Points.gpkg")
    path_walk_gsv_points_csv = os.path.join(path_root, f"{walk_id}-GSV-Points.txt")

    # gsv_points_gdf = gpd.read_file(path_gsv_points)
    # gsv_points_gdf = gsv_points_gdf.to_crs("EPSG:3857") # metric conversion



    if os.path.exists(path_walk_02):
        walk_gdf = gpd.read_file(path_walk_02)
        # walk_gdf = walk_gdf.to_crs("EPSG:3857") # metric conversion
        pano_gdf = list_all_gvs_points(walk_gdf, gsv_points_gdf)
        utils.save_gsv_points(pano_gdf,path_walk_gsv_points_csv)
        pano_gdf = pano_gdf.to_crs("EPSG:4326")
        pano_gdf.to_file(path_walk_gsv_points, layer='locations', driver="GPKG")



