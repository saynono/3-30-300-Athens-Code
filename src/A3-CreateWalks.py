import geopandas as gpd
import osmnx as ox
from pyproj import CRS
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import linemerge
import utils
from src.utils import save_gsv_points
from pyproj import Geod
import numpy as np

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


def get_end_points(gdf):
    from collections import defaultdict

    # Combine start and end points with labels
    endpoint_dict = defaultdict(list)
    # Lists to store start and end points
    start_points = []
    end_points = []

    # Extract start and end points from each LineString
    for line in gdf.geometry:
        # print(">>>>",line.geom_type)
        if line.geom_type == "LineString":
            # List to store the segments
            segments = []
            # Iterate over coordinate pairs
            for i in range(len(line.coords) - 1):
            #     segment = LineString([line.coords[i], coords[i + 1]])
            #     segments.append(segment)
            # for p in len(line.coords):
            #     print(f"p: {p}")
                start_points.append(Point(line.coords[i]))
                end_points.append(Point(line.coords[i+1]))
        else:
            for sl in line.geoms:
                coords = list(sl.coords)
                start_points.append(Point(coords[0]))
                end_points.append(Point(coords[-1]))
    for idx, pt in enumerate(start_points):
        endpoint_dict[(pt.x, pt.y)].append(('start', idx))

    for idx, pt in enumerate(end_points):
        endpoint_dict[(pt.x, pt.y)].append(('end', idx))

    # Find points that occur only once
    gap_points = []
    for coord, occurrences in endpoint_dict.items():
        if len(occurrences) == 1:
            # This point is a gap
            gap_points.append(Point(coord))
            print(f"Adding Point: {coord}")


    # Calculate distances between all pairs of points
    distances = []
    for i in range(len(gap_points)):
        for j in range(i + 1, len(gap_points)):
            # x1, y1 = gap_points[i]
            # x2, y2 = gap_points[j]
            distance = np.sqrt((gap_points[j].x - gap_points[i].x)**2 + (gap_points[j].y - gap_points[i].y)**2)
            distances.append((i, j, distance))

    # Print distances
    for p1, p2, d in distances:
        print(f"Distance between Point {p1} and Point {p2}: {d}")

    return gap_points


def get_starting_point(gdf):
    merged = gdf.geometry.unary_union
    if merged.geom_type == "MultiLineString":
        merged = linemerge(merged)
        print(f"merged : {type(merged)} {merged}")
        return Point(merged.geoms[0].coords[0])
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
    print(f"closest_dist : {closest_dist}")
    return closest_idx

# Function to reorder LineStrings in the GeoDataFrame
def reorder_linestrings(gdf, starting_point):
    remaining_gdf = gdf.copy()  # Copy the GeoDataFrame
    ordered_lines = []

    print(f"====>remaining_gdf: {remaining_gdf.geometry}")

    # Start with the LineString closest to the starting point
    closest_idx = find_closest(remaining_gdf, starting_point)
    current_line = remaining_gdf.loc[closest_idx]
    print(f"current_line : {current_line}")
    ordered_lines.append(current_line)
    remaining_gdf = remaining_gdf.drop(index=closest_idx)

    while not remaining_gdf.empty:
        # Find the closest LineString to the current endpoint
        current_endpoint = Point(current_line.geometry.coords[-1])
        closest_idx = find_closest(remaining_gdf, current_endpoint)
        print(f"closest_idx: {closest_idx}")

        # Append the closest LineString to the order
        next_line = remaining_gdf.loc[closest_idx]
        ordered_lines.append(next_line)
        current_line = next_line  # Update the current LineString
        remaining_gdf = remaining_gdf.drop(index=closest_idx)

    # Return the ordered GeoDataFrame
    gdf = gpd.GeoDataFrame(ordered_lines, crs=gdf.crs)
    gdf = gdf.reset_index(drop=True)
    return gdf

def normalize_geometry(geom):
    if geom.geom_type == "MultiLineString":
        geom = geom.geoms[0]
    if geom.coords[0] > geom.coords[-1]:
        return LineString(list(geom.coords)[::-1])  # Reverse the geometry
    return geom
#
# def sort_segments(segments):
#     # Initialize previous end point
#     prev_end = None
#     ordered_segments = []
#     for idx in ordered_indices:
#         segment = gdf.loc[idx, 'geometry']
#         start, end = get_endpoints(segment)
#
#         if prev_end is None:
#             # First segment; add as is
#             ordered_segments.append(segment)
#             prev_end = end
#         else:
#             if (start.x, start.y) == prev_end:
#                 # Correct orientation
#                 ordered_segments.append(segment)
#                 prev_end = end
#             elif (end.x, end.y) == prev_end:
#                 # Reverse the segment
#                 reversed_segment = LineString(segment.coords[::-1])
#                 ordered_segments.append(reversed_segment)
#                 prev_end = reversed_segment.coords[-1]
#             else:
#                 raise ValueError(f"Segment {idx} does not connect properly.")


def get_single_lines_sorted(gdf, reverse=False):

    segments = []
    for geom in gdf.geometry:
        # print(">>>>",geom.geom_type)
        if geom.geom_type == "LineString":
            for i in range(len(geom.coords) - 1):
                segment = LineString([geom.coords[i], geom.coords[i + 1]])
                segments.append(segment)
                # print(f"Adding Line: {segment}")

        elif geom.geom_type == "MultiLineString":
            for idx, line in enumerate(geom.geoms):
                for i in range(len(line.coords) - 1):
                    segment = LineString([line.coords[i], line.coords[i + 1]])
                    segments.append(segment)
                    # print(f"Adding MLine: {segment}")

    gdf = gpd.GeoDataFrame(geometry=segments,crs=gdf.crs)
    start_point = get_end_points(gdf)[0]
    print(f"1 StartPoint : {start_point}")


    if reverse:
        segments = segments[::-1]


    gdf = gpd.GeoDataFrame(geometry=segments,crs=gdf.crs)
    start_point = get_end_points(gdf)[0]
    print(f"2 StartPoint : {start_point}")

    return gdf


def get_all_edge_centers(walk_gdf, reversed=False):

    geod = Geod(ellps="WGS84")  # Use WGS84 ellipsoid
    walk_gdf_copy = walk_gdf.copy()

    # find starting point of walk
    if reversed:
        starting_point = get_end_points(walk_gdf_copy)[1]
    else:
        starting_point = get_end_points(walk_gdf_copy)[0]
    print(f"starting_point: {starting_point}")
    # starting_point = get_starting_point(walk_gdf_copy)
    # Reorder the GeoDataFrame
    walk_gdf_copy = reorder_linestrings(walk_gdf_copy, starting_point)
    # when removing rows don't recalculate the indices. So need to do that manually
    walk_gdf_copy = walk_gdf_copy.reset_index(drop=True)


    walk_gdf_copy['length_meters'] = walk_gdf_copy['geometry'].apply(geod.geometry_length)

    # remove street parts that are obviously too short
    min_edge_length = 25 # in meters
    walk_gdf_copy = walk_gdf_copy[walk_gdf_copy['length_meters'] >= min_edge_length]
    # walk_gdf_copy = walk_gdf_copy.to_crs("EPSG:3857")
    # remove double entries...

    # Normalize geometries: Sort coordinates to make reverse directions identical
    # now we are able to remove double entries
    walk_gdf_copy['normalized_geometry'] = walk_gdf_copy['geometry'].apply(normalize_geometry)
    walk_gdf_copy = walk_gdf_copy.drop_duplicates(subset='normalized_geometry').drop(columns=['normalized_geometry'])
    # walk_gdf_copy = walk_gdf_copy.drop_duplicates(subset='osmid', keep='first')

    centers = []
    labels = []
    for idx, part in walk_gdf_copy.iterrows():
        length = part.geometry.length/2.0
        centers.append(part.geometry.interpolate(length))
        length_meters = part.length_meters #geod.geometry_length(part.geometry)
        # print(f"#{idx}   Length = {length_meters} ")
        label = len(labels)+1
        labels.append(label)

    gdf = gpd.GeoDataFrame(
        walk_gdf_copy,
        geometry=centers,
        crs=walk_gdf_copy.crs,  # Use WGS84 (latitude/longitude) CRS
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
    # walk_id = "Walk02/Walk-Team-02"

    reverse_order = False
    walk_id = "Walk-Public-04/Walk-Public-04-cleaned"

    path_walk = os.path.join(path_root, f"{walk_id}.gpkg")
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




            end_points = get_end_points(walk_gdf)

            # # Plot the MultiLineString
            # fig, ax = plt.subplots()
            # # for line in multi_line.geoms:
            # #     x, y = line.xy
            # #     ax.plot(x, y, color='blue')
            # walk_gdf.plot(ax=ax, color='blue')
            #
            # # Plot the gap points
            # for pt in end_points:
            #     ax.plot(pt.x, pt.y, 'ro')  # Red dots for gaps
            #
            # ax.set_title('Gaps in MultiLineString')
            # plt.show()


            print(f"=====> remaining_gdf : {walk_gdf.geometry.geom_type}")
            print(walk_gdf.geom_type.unique())

            if walk_gdf.geom_type.unique() == "MultiLineString":
                merged = walk_gdf.geometry.unary_union
                walk_gdf.geometry = [merged]

            print(f"=====> remaining_gdf : {walk_gdf.geometry.geom_type}")

            walk_single_seg = get_single_lines_sorted(walk_gdf, reverse_order)



            walk_edge_centers_gdf = get_all_edge_centers(walk_gdf, reverse_order)
            walk_edge_centers_gdf.to_file(path_walk_center_points, layer='locations', driver="GPKG")

            # Plot layers on the same figure
            fig, ax = plt.subplots(figsize=(10, 10))

            end_points = get_end_points(walk_gdf)


            walk_gdf.plot(ax=ax, color='blue', figsize=(10, 10), alpha=0.5, edgecolor="k", label="Walk")
            # gdf_line.plot(ax=ax, color='green', figsize=(10, 10), alpha=0.5, edgecolor="k", label="Walk")
            x_coords = [p.x for p in end_points]
            y_coords = [p.y for p in end_points]
            # Plot the points
            plt.scatter(x_coords, y_coords, color='purple', label='Shapely Points')
            ax.plot(end_points[0].x,end_points[0].y, marker='o',  color='red', alpha=0.5, label="Walk")
            ax.plot(end_points[1].x,end_points[1].y, marker='o',  color='blue', alpha=0.5, label="Walk")
            walk_edge_centers_gdf.plot(ax=ax, color='red', figsize=(10, 10), alpha=0.5, edgecolor="k", label="Centers")
            # walk_single_seg.plot(ax=ax, color='green', figsize=(10, 10), alpha=0.5, edgecolor="k", label="Centers")
            plt.show()
    else:
        print(f"Walk File not found: {path_walk}")
