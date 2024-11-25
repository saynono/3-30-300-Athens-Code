import geopandas as gpd
import osmnx as ox
from pyproj import CRS
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import linemerge
import utils
from src.utils import save_gsv_points
from pyproj import Geod

def list_all_gvs_points(walk_gdf, gsv_points_gdf):

    dist = 9 #meters

    walk_gdf_metric = walk_gdf.to_crs("EPSG:3857") # metric conversion
    merged = walk_gdf_metric.geometry.unary_union
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

    points_within_buffer = gsv_points_gdf[gsv_points_gdf.within(gdf_buffer.geometry.unary_union)]
    return points_within_buffer


def get_starting_point(gdf):
    merged = walk_gdf.geometry.unary_union
    if merged.geom_type == "MultiLineString":
        merged = linemerge(merged)
    return Point(merged.coords[0])


# Function to find the closest LineString to a given point
def find_closest(lines, point):
    closest_idx = None
    closest_dist = float('inf')
    for idx, row in lines.iterrows():
        line = row.geometry
        dist_to_start = point.distance(Point(line.coords[0]))
        dist_to_end = point.distance(Point(line.coords[-1]))
        min_dist = min(dist_to_start, dist_to_end)
        if min_dist < closest_dist:
            closest_dist = min_dist
            closest_idx = idx
    return closest_idx

# Function to reorder LineStrings in the GeoDataFrame
def reorder_linestrings(gdf, starting_point):
    remaining_gdf = gdf.copy()  # Copy the GeoDataFrame
    ordered_lines = []

    # Start with the LineString closest to the starting point
    closest_idx = find_closest(remaining_gdf, starting_point)
    current_line = remaining_gdf.loc[closest_idx]
    ordered_lines.append(current_line)
    remaining_gdf = remaining_gdf.drop(index=closest_idx)

    while not remaining_gdf.empty:
        # Find the closest LineString to the current endpoint
        current_endpoint = Point(current_line.geometry.coords[-1])
        closest_idx = find_closest(remaining_gdf, current_endpoint)

        # Append the closest LineString to the order
        next_line = remaining_gdf.loc[closest_idx]
        ordered_lines.append(next_line)
        current_line = next_line  # Update the current LineString
        remaining_gdf = remaining_gdf.drop(index=closest_idx)

    # Return the ordered GeoDataFrame
    return gpd.GeoDataFrame(ordered_lines, crs=gdf.crs)

def normalize_geometry(geom):
    if geom.coords[0] > geom.coords[-1]:
        return LineString(list(geom.coords)[::-1])  # Reverse the geometry
    return geom


def get_all_edge_centers(walk_gdf):

    geod = Geod(ellps="WGS84")  # Use WGS84 ellipsoid
    walk_gdf_copy = walk_gdf.copy()
    walk_gdf_copy['length_meters'] = walk_gdf_copy['geometry'].apply(geod.geometry_length)

    # remove street parts that are obviously too short
    min_edge_length = 25 # in meters
    walk_gdf_copy = walk_gdf_copy[walk_gdf_copy['length_meters'] >= min_edge_length]
    # remove double entries...

    # Normalize geometries: Sort coordinates to make reverse directions identical
    # now we are able to remove double entries
    walk_gdf_copy['normalized_geometry'] = walk_gdf_copy['geometry'].apply(normalize_geometry)
    walk_gdf_copy = walk_gdf_copy.drop_duplicates(subset='normalized_geometry').drop(columns=['normalized_geometry'])
    # walk_gdf_copy = walk_gdf_copy.drop_duplicates(subset='osmid', keep='first')

    # find starting point of walk
    starting_point = get_starting_point(walk_gdf_copy)
    # Reorder the GeoDataFrame
    walk_gdf_copy = reorder_linestrings(walk_gdf_copy, starting_point)
    # when removing rows don't recalculate the indices. So need to do that manually
    walk_gdf_copy = walk_gdf_copy.reset_index(drop=True)

    centers = []
    labels = []
    for idx, part in walk_gdf_copy.iterrows():
        length = part.geometry.length/2.0
        centers.append(part.geometry.interpolate(length))
        length_meters = part.length_meters #geod.geometry_length(part.geometry)
        print(f"#{idx}   Length = {length_meters} ")
        labels.append(len(labels)+1)


    gdf = gpd.GeoDataFrame(
        walk_gdf_copy,
        geometry=centers,
        crs="EPSG:4326",  # Use WGS84 (latitude/longitude) CRS
    )
    gdf['index_field'] = gdf.index
    gdf['labels']=labels

    return gdf


if __name__ == "__main__":
    import os, os.path

    path_root = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Walks/"
    path_gsv_points = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/generated/Kypseli-All-GSV-Points.gpkg"
    path_metadata_selected = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/metadata"

    metadata_df = utils.load_all_csvs(path_metadata_selected)
    gsv_points_gdf = utils.create_gsv_map(metadata_df)
    # gdf_gsv_points.to_file(path_gsv_points, layer='locations', driver="GPKG")
    walk_id = "Walk02/Walk-Team-02"
    path_walk = os.path.join(path_root, f"{walk_id}-Edges-Raw.gpkg")
    path_walk_gsv_points = os.path.join(path_root, f"{walk_id}-GSV-Points.gpkg")
    path_walk_gsv_points_csv = os.path.join(path_root, f"{walk_id}-GSV-Points.txt")
    path_walk_center_points = os.path.join(path_root, f"{walk_id}-center-points.gpkg")

    # gsv_points_gdf = gpd.read_file(path_gsv_points)
    # gsv_points_gdf = gsv_points_gdf.to_crs("EPSG:3857") # metric conversion


    do_save_edge_markers = True
    do_save_gsv_points = True

    if os.path.exists(path_walk):
        walk_gdf = gpd.read_file(path_walk)
        # walk_gdf = walk_gdf.to_crs("EPSG:3857") # metric conversion
        if do_save_gsv_points:
            pano_gdf = list_all_gvs_points(walk_gdf, gsv_points_gdf)
            utils.save_gsv_points(pano_gdf,path_walk_gsv_points_csv)
            pano_gdf = pano_gdf.to_crs("EPSG:4326")
            pano_gdf.to_file(path_walk_gsv_points, layer='locations', driver="GPKG")
        if do_save_edge_markers:
            walk_edge_centers_gdf = get_all_edge_centers(walk_gdf)
            walk_edge_centers_gdf.to_file(path_walk_center_points, layer='locations', driver="GPKG")

            # Plot layers on the same figure
            fig, ax = plt.subplots(figsize=(10, 10))

            walk_gdf.plot(ax=ax, color='blue', figsize=(10, 10), alpha=0.5, edgecolor="k", label="Walk")
            # gdf_line.plot(ax=ax, color='green', figsize=(10, 10), alpha=0.5, edgecolor="k", label="Walk")
            # gdf_point.plot(ax=ax, color='yellow', figsize=(10, 10), alpha=0.5, edgecolor="k", label="Walk")
            walk_edge_centers_gdf.plot(ax=ax, color='red', figsize=(10, 10), alpha=0.5, edgecolor="k", label="Centers")
            plt.show()

