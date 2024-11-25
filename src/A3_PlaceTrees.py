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

def predict_something():
    model = YOLO("yolo11n.pt")

    # Train the model
    # train_results = model.train(
    #     data="coco8.yaml",  # path to dataset YAML
    #     epochs=100,  # number of training epochs
    #     imgsz=640,  # training image size
    #     device="cpu",  # device to run on, i.e. device=0 or device=0,1,2,3 or device=cpu
    # )

    # Evaluate model performance on the validation set
    data = "/home/nono/Documents/workspaces/cpp/darknet/Training/Athens-3-30-300-Panorama-Grey/Athens-3-30-300-Panorama-Grey.yaml"
    model.train(data=data, epochs=5, imgsz=640)
    metrics = model.val()

    # Perform object detection on an image
    # results = model("path/to/image.jpg")
    # results[0].show()

    results = model("/home/nono/Downloads/Screenshot 2024-11-05-sz.png")
    results[0].show()
    # Export the model to ONNX format
    # path = model.export(format="onnx")  # return path to exported model



# Global variables to store clicked point and mask
clicked_point = None
clicked_point_prev = None
segmented_mask = None
stacked_images = None
has_predictions = False


def add_text(image, text, position):
    # Define text properties

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = .4
    font_thickness = 1
    text_color = (200, 200, 200)  # White text color
    box_color = (20, 20, 20)  # Red box color
    border = 5

    # Get the text size for positioning
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, font_thickness)

    # # Calculate position of the text (centered)
    text_x = position[0]
    text_y = position[1]

    # Calculate the box coordinates
    box_x1 = position[0] - border  # Add padding around the text
    box_y1 = text_y - text_height - border  # Top of the box
    box_x2 = text_x + text_width + border  # Right side of the box
    box_y2 = text_y + baseline + border  # Bottom of the box

    # Draw the box (rectangle) behind the text
    cv2.rectangle(image, (box_x1, box_y1), (box_x2, box_y2), box_color, -1)  # -1 to fill the rectangle

    # Draw the text on top of the box
    cv2.putText(image, text, position, font, font_scale, text_color, font_thickness, lineType=cv2.LINE_AA)
    # cv2.addText(image, text,position, font, 10, color=(255, 0, 0) )

def draw_points(image, points):
    for p in points:
        str = f"[{p[0]},{p[1]}] d: {p[2]:.0f}cm"
        cv2.circle(image, (p[0], p[1]), radius=5, color=(255, 0, 0), thickness=-1)
        add_text(image, str,(p[0]+20, p[1]))


# Mouse callback function
def mouse_callback(event, x, y, flags, param):
    global clicked_point, clicked_point_prev, segmented_mask, depth_image, stacked_images, colored_mask, regular_image, stitched_image, depth_data, selected_points

    if event == cv2.EVENT_LBUTTONDOWN:
        height, width = depth_image.shape[:2]
        if clicked_point:
            clicked_point_prev = clicked_point
        clicked_point = (y%height, x)  # Note: OpenCV uses (row, col) format
        raw_depth = depth_data[clicked_point[0],clicked_point[1]]*100
        selected_points.append((clicked_point[1],clicked_point[0],raw_depth))
        redraw()
        print("Mouse Interaction Done")


def redraw():
        global clicked_point, clicked_point_prev, segmented_mask, depth_image, stacked_images, colored_mask, regular_image, stitched_image, depth_data, selected_points
        height, width = depth_image.shape[:2]
        display_image = depth_image.copy()
        display_image = cv2.cvtColor(display_image, cv2.COLOR_GRAY2RGB)


        draw_points(display_image, selected_points)

        str = f"Panorama [{pano_id}]     Predictions: {has_predictions}"
        add_text(display_image, str,(10, 20))

        stacked_images[height:2*height, 0:width] = display_image


        # edges_mask = ski.filters.sobel(segmented_mask)
        contours, _ = cv2.findContours(segmented_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # outline = np.zeros_like(segmented_mask)
        display_image = regular_image.copy()


        # Convert RGB image to HSV
        hsv_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2HSV)
        hsv_image[:, :, 2] = 255

        # Convert back to RGB
        display_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)
        draw_points(display_image, selected_points)
        stacked_images[2*height:3*height, :] = display_image

        display_image = regular_image.copy()
        draw_points(display_image, selected_points)

        stacked_images[0:height, 0:] = display_image

#
#
# def create_gsv_map(metadata_df):
#
    # gdf = gpd.GeoDataFrame(
    #     metadata_df,
    #     geometry=[Point(xy) for xy in zip(metadata_df['longitude'], metadata_df['latitude'])],
    #     crs="EPSG:4326"  # Use WGS84 (latitude/longitude) CRS
    # )
#
#     return gdf
#
#
# def temp_create_gsv_map(metadata_df):
#     gdf = gpd.GeoDataFrame(
#         metadata_df,
#         geometry=[Point(xy) for xy in zip(metadata_df['longitude'], metadata_df['latitude'])],
#         crs="EPSG:4326"  # Use WGS84 (latitude/longitude) CRS
#     )
#
#     random_points = []
#     for idx, row in gdf.iterrows():
#         # Generate random angle (0 to 360 degrees) and distance (e.g., 0 to 100 meters)
#         angle = 90 #random.uniform(0, 360)  # Angle in degrees
#         distance = random.uniform(1.5, 5.0)  # Distance in meters
#
#         # Calculate the new point based on the angle and distance
#         origin = (row['latitude'], row['longitude'])
#         destination = geopy_distance(meters=distance).destination(origin, angle)
#         new_point = Point(destination.longitude, destination.latitude)
#
#         # Add the new point to the list
#         random_points.append(new_point)
#
#     # Step 3: Add the new points as a new column in the GeoDataFrame
#
#     gdf_random = gpd.GeoDataFrame(
#         metadata_df[['panoID']],  # Keep only panoID or other identifiers
#         geometry=random_points,
#         crs="EPSG:4326"
#     )
#
#     return gdf_random


def load_panorama(pano_id):
    global regular_image, depth_image, depth_data, stitched_image, display_image, stacked_images, has_predictions, selected_points

    regular_image, depth_image, depth_data = load_image_set(pano_id)

    selected_points, has_predictions = load_prediction(pano_id)

    if len(depth_image.shape) == 3:
        depth_image = cv2.cvtColor(depth_image, cv2.COLOR_BGR2GRAY)


    display_image = cv2.cvtColor(depth_image, cv2.COLOR_GRAY2RGB)

    stitched_image = np.copy(regular_image)

    doMoveBy180 = False
    if doMoveBy180:
        height, width = stitched_image.shape[:2]
        # Step 2: Calculate the midpoint to split the image by half of its width
        midpoint = width // 2
        # Step 3: Split the image into two halves
        left_half = stitched_image[:, :midpoint]  # Left half of the image
        right_half = stitched_image[:, midpoint:] # Right half of the image
        # Step 4: Stitch the halves together with the right half first
        stitched_image = np.hstack((right_half, left_half))


    stacked_images = np.vstack((regular_image, display_image, stitched_image))
    # selected_points = []


def load_image_set(pano_id):
    global gsvPanoramaRoot, gsvDepthRoot
    print(f"Loading Image Set {pano_id}")
    panorama_image = cv2.imread(os.path.join(gsvPanoramaRoot,f"panorama_{pano_id}.jpg"), cv2.IMREAD_UNCHANGED)
    depth_image = cv2.imread(os.path.join(gsvDepthRoot,f"panorama_{pano_id}_depth.png"), cv2.IMREAD_UNCHANGED)  # Load your depth image
    depth_data = np.load(os.path.join(gsvDepthRoot,f"panorama_{pano_id}_raw_depth_meter.npy"))
    return panorama_image, depth_image, depth_data

def has_all_data(pano_id):
    all_okay = True
    file_paths = []
    file_paths.append( os.path.join(gsvPanoramaRoot,f"panorama_{pano_id}.jpg") )
    file_paths.append( os.path.join(gsvDepthRoot,f"panorama_{pano_id}_depth.png") )
    file_paths.append( os.path.join(gsvDepthRoot,f"panorama_{pano_id}_raw_depth_meter.npy") )

    for file_path in file_paths:
        if not os.path.isfile(file_path):
            print(f"File missing: {file_path}")
            all_okay = False
    return all_okay

def save_prediction(pano_id):
    global selected_points, gsvDataPrediction
    print(f"Saving Predictions [{pano_id}]")
    path = os.path.join(gsvDataPrediction,f"predicted_{pano_id}.csv")
    with open(path, 'w', newline='') as file:
        str = f"x, y, depth, type\n"
        file.write(str)
        for p in selected_points:
            type = 0
            str = f"{p[0]}, {p[1]}, {p[2]}, {type}\n"
            file.write(str)

def load_prediction(pano_id):
    global gsvDataPrediction
    path = os.path.join(gsvDataPrediction,f"predicted_{pano_id}.csv")
    print(f"Loading Preditions. {pano_id} -> exists: {os.path.isfile(path)}")
    if os.path.isfile(path):
        df = pd.read_csv(path, sep=",")
        _selected_points = []
        for index, item in df.iterrows():
            values = item.values
            _selected_points.append((int(values[0]),int(values[1]),values[2]))
        return _selected_points, True
    return [], False


def select_previous_panorama(unpredicted):
    global pano_id
    p_start = pano_id
    for index, row in reversed(list(metadata_df.iterrows())):
        if p_start == row.panoID:
            if index >= 0 :
                pid = metadata_df.iloc[index-1].panoID
                if has_all_data(pid):
                    print(f"Selected Index (Prev) : {index}   => {pid}")
                    return pid
                else:
                    p_start = pid
    return None


def select_next_panorama(unpredicted=True):
    global metadata_df
    # pano_id = None
    print(f" Select Next Panorama [{metadata_df.shape[0]}]")
    found_current_index = True if pano_id == -1 else False
    for index, row in metadata_df.iterrows():

        if not found_current_index:
            if row.panoID == pano_id:
                found_current_index = True
        else:

            pid = row.panoID
            print(f"index: {index}    ")
            if pano_id != pid and has_all_data(pid):
                path = os.path.join(gsvDataPrediction,f"predicted_{pid}.csv")
                # For now only panoramas that haven't been dealt with
                print(f"Prediction: {path} => {os.path.exists(path)} ")

                if (not unpredicted or not os.path.exists(path)):
                    print(f"Selected Index (Next): {index}   => {pid}")
                    return pid

    # If dataset has all been predicted
    if unpredicted:
        print("All Data has been predicted.")
        return metadata_df.iloc[0].panoID
        # return select_previous_panorama(False)
    return None


def add_gsvp_to_buffer(gsvp, buffer_df):
    tree_list,_ = load_prediction(gsvp['panoID'])

    print(f"  tree_list ::: {tree_list}")
    # remove trees that are farther away than 1500cm
    #IMPORTANT
    tree_distance_max = 2000
    tree_list = [item for item in tree_list if item[2] <= tree_distance_max]

    trees = osm_utils.get_tree_points((gsvp.geometry.x,gsvp.geometry.y), tree_list)
    rays = []
    origin = Point(gsvp.geometry.x,gsvp.geometry.y)
    tps = osm_utils.get_tree_points((gsvp.geometry.x,gsvp.geometry.y), tree_list, 1.4,5)
    for tp in tps:
        tree_line = LineString([origin, tp])
        rays.append(tree_line)

    entry = {"pano_id": gsvp['panoID'], "location": gsvp.geometry, "trees": trees, "rays": rays}
    print(f"Adding DataFrame to Buffer: {entry}")
    return pd.concat([buffer_df, pd.DataFrame([entry])], ignore_index=True)


# Function to check distance and intersections
def find_valid_intersections(main_df, other_dfs):
    intersections = []
    main_rays = main_df.rays
    other_rays = []
    for buf in other_dfs:
        other_rays += buf.rays
    print(f"\n\nmain_gdf : {main_df.pano_id} ")
    cnt = 0
    for main_line in main_rays:

        print(f"==== {cnt} ====")

        main_start = main_line.coords[1]  # Start point of main line
        main_start_point = Point(main_start)

        intersections_line = []

        for other_line in other_rays:
            other_start = other_line.coords[0]  # Start point of other line
            other_start_point = Point(other_start)

            # Check intersection
            if main_line.intersects(other_line):
                intersection = main_line.intersection(other_line)

                # Check if the main start is closer to other start
                # if main_start_point.distance(other_start_point) < other_start_point.distance(intersection):
                #     intersections_line.append(intersection)
                intersections_line.append(intersection)

        # make sure only one intersection is added and choose the intersection that is closest to the measured distance of the depth map
        if len(intersections_line) > 1 :
            closest_point = min(intersections_line, key=lambda p: main_df.trees[cnt].distance(p))
            intersections_line = [closest_point]
            print(f" {cnt} / {main_start_point} ================= > intersection : {closest_point}    origin: =====>> {main_df.trees[cnt]}")
        elif len(intersections_line) == 0 :
            print(f" {cnt} / {main_start_point} ================= > Adding Free Floating Tree: {main_df.trees[cnt]}")
            intersections_line = [main_df.trees[cnt]]

        intersections = intersections + intersections_line

        cnt += 1

    gdf_intersections = gpd.GeoDataFrame(
        geometry=intersections,
        crs="EPSG:4326"
    )
    gdf_intersections['panoID'] = [main_df.pano_id] * len(intersections)

    return gdf_intersections


def cluster_points(gdf, cluster_radius = 1):

    # return None if there is nothing to cluster
    if gdf.empty:
        return None

    # Extract coordinates
    coords = np.array([(point.x, point.y) for point in gdf.geometry])

    # DBSCAN clustering
    dbscan = DBSCAN(eps=0.000012715*cluster_radius, min_samples=2)  # eps roughly one meter
    gdf['cluster'] = dbscan.fit_predict(coords)

    # Calculate centroids for each cluster
    centroids = gdf.groupby('cluster')['geometry'].apply(lambda x: x.unary_union.centroid)
    centroids_gdf = gpd.GeoDataFrame(centroids, geometry=centroids, crs=gdf.crs).reset_index()
    return centroids_gdf


def create_intersections(metadata_df):


    gdf_gsv_points_ALL = osm_utils.create_gsv_map(metadata_df)
    gdf_gsv_points_ALL_metric = gdf_gsv_points_ALL.to_crs("EPSG:32633")
    # gdf_gsv_points_ALL_metric = gdf_gsv_points_ALL.to_crs("EPSG:3857")

    # Check the CRS of your GeoDataFrame
    print(gdf_gsv_points_ALL.crs)

    # Determine if the CRS uses metric units
    if gdf_gsv_points_ALL.crs:
        if gdf_gsv_points_ALL.crs.is_projected:
            print("The CRS is projected and likely uses a metric system (e.g., meters).")
        else:
            print("The CRS is geographic and likely uses degrees (not metric).")
    else:
        print("The GeoDataFrame has no CRS defined.")

    columns = ["pano_id", "location", "trees", "rays"]
    tree_buffer_df = pd.DataFrame(columns=columns)
    # tree_buffer_df.set_index("pano_id", inplace=True)

    for idx, gsvp in gdf_gsv_points_ALL.iterrows():
        print(f"\n\n{idx} GSVP : {gsvp['panoID']}   {gsvp.geometry}")
        pano_id = gsvp['panoID']

        # if pano_id in tree_buffer_df['pano_id'].values:
        #     print(f"Index '{pano_id}' exists.")
        #     current_tree_buffer = tree_buffer_df.loc[tree_buffer_df['pano_id'] == pano_id].iloc[0]
        # else:
        if pano_id not in tree_buffer_df['pano_id'].values:
            # entry = {"pano_id": gsvp['panoID'], "location": gsvp.geometry, "trees": [], "rays": []}
            # tree_buffer_df = pd.concat([tree_buffer_df, pd.DataFrame([entry])], ignore_index=True)
            tree_buffer_df = add_gsvp_to_buffer(gsvp, tree_buffer_df)
            # tree_buffer_df.set_index("pano_id", inplace=True)
            print(f"Index '{pano_id}' does not exist.    index:{pano_id in tree_buffer_df.values}")


        # if current_tree_buffer:
        #     current_tree_buffer = {"ID": 4, "Name": "Object D", "Value": 40}
        #     df = tree_buffer_df.append(current_tree_buffer, ignore_index=True)


    gdf_gsv_points_ALL_metric = gdf_gsv_points_ALL.to_crs("EPSG:3857")

    intersections_gdf = None

    for idx, gsvp in gdf_gsv_points_ALL_metric.iterrows():

        pano_id = gsvp['panoID']
        current_tree_buffer = tree_buffer_df.loc[tree_buffer_df['pano_id'] == pano_id].iloc[0]
        # Create a buffer of x meters around the reference point
        #IMPORTANT
        radius = 20  # Radius in meters
        # search_area = Point(gsvp['longitude'],gsvp['latitude']).buffer(radius)
        search_area = gsvp.geometry.buffer(radius)
        # Filter points within the buffer
        points_within_radius = gdf_gsv_points_ALL_metric[gdf_gsv_points_ALL_metric.geometry.within(search_area)]

        print(f"----{idx}---- {type(points_within_radius)}")

        # rays = current_tree_buffer.rays
        # tree = current_tree_buffer.trees



        for idx2, gsvp_radius in points_within_radius.iterrows():
            if gsvp_radius['panoID'] == gsvp['panoID'] :
                points_within_radius = points_within_radius.drop(index=idx2)

        other_tree_buffers = []

        for idx2, gsvp_radius in points_within_radius.iterrows():

            # calculate intersections etc
            # rays = current_tree_buffer.rays
            other_pano_id = gsvp_radius['panoID']


            print(f"=====> {idx2} ===> {other_pano_id}     df={other_pano_id in tree_buffer_df['pano_id'].values}")
            if other_pano_id in tree_buffer_df['pano_id'].values:


                # other_tree_buffer = tree_buffer_df.loc[tree_buffer_df[other_pano_id] == pano_id].iloc[0]
                other_tree_buffer = tree_buffer_df[tree_buffer_df['pano_id'] == other_pano_id].iloc[0]
                other_tree_buffers.append(other_tree_buffer)


        res_gdf = find_valid_intersections(current_tree_buffer, other_tree_buffers)

        if res_gdf is not None:
            if intersections_gdf is None:
                intersections_gdf = res_gdf
            else:
                intersections_gdf = pd.concat([intersections_gdf,res_gdf], ignore_index=True)


    # Cluster all trees to remove double entries
    res_clustered_gdf = cluster_points(intersections_gdf,1.5)
    intersections_gdf = res_clustered_gdf

    return intersections_gdf



if __name__ == "__main__":



    # Example usage

    gsvRoot = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/GSV-Data/"
    gsvPanoramaRoot = os.path.join(gsvRoot,"panoramas-final-new/")
    gsvDepthRoot = os.path.join(gsvRoot,"panoramas-depth-new/")
    gsvDataPrediction = os.path.join(gsvRoot,"prediction-data/")

    pathMetaData         = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/metadata"
    # pathMetaDataSelected = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/selected_pano_ids.txt"
    pathMetaDataSelected = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Walks/Walk-Team-01-GSV-Points.txt"
    # pathMetaDataSelected = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/selected_pano_ids_crossing.txt"

    pathGSVPoints        = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/generated/Kypseli-All-GSV-Points.gpkg"
    pathGSVPointsTemp    = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/generated/Kypseli-All-GSV-Points-TEMP.gpkg"

    pathGSVTreePoints    = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/generated/Kypseli-All-GSV-Tree-Points.gpkg"
    pathDataGenerated    = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/generated/temp"


    # metadata_df = utils.load_all_csvs(pathMetaDataSelected)
    metadata_df = utils.load_all_csvs(pathMetaData)
    # res = utils.find_entry_by_panoID(metadata_df,"0A1aUxQvyr_KqmaokVoqvQ")
    # utils.print_df_results(res)

    if not os.path.exists(pathDataGenerated):
        os.mkdir(pathDataGenerated)





    panos = metadata_df['panoID'].to_numpy()


    intersections_gdf = create_intersections(metadata_df)
    pathIntersectionPoints = os.path.join(pathDataGenerated,f"__Kypseli-All-GSV-Tree-Points-CROSSING-Intersections.gpkg")
    intersections_gdf.to_file(pathIntersectionPoints, layer='locations', driver="GPKG")


    if True:
        exit(0)


    # load_panorama(pano_id)
    #
    # create_gsv_map()

    # gdf_gsv_points = osm_utils.create_gsv_map(metadata_df)
    # gdf_gsv_points = osm_utils.create_gsv_map(metadata_df)

    # gdf_gsv_points.to_file(pathGSVPoints, layer='locations', driver="GPKG")
    #
    # gdf_temp_gsv_points = temp_create_gsv_map(metadata_df)
    # gdf_temp_gsv_points.to_file(pathGSVPointsTemp, layer='locations', driver="GPKG")

    allLines = gpd.GeoDataFrame(columns=['geometry'])
    allTrees = gpd.GeoDataFrame(columns=['geometry'])

    save_single = False
    for pano in panos:
        pano_id = pano
        if has_all_data(pano):
            load_panorama(pano)

            pathTreePoints = os.path.join(pathDataGenerated,f"Kypseli-All-GSV-Tree-Points-{pano}_lines.gpkg")
            gdf_trees = osm_utils.add_trees_to_gsv_map(pano_id, selected_points, metadata_df, False)
            if not gdf_trees.empty and save_single:
                gdf_trees.to_file(pathTreePoints, layer='locations', driver="GPKG")

            pathTreeLines = os.path.join(pathDataGenerated,f"Kypseli-All-GSV-Tree-Points-{pano}.gpkg")
            gdf_Lines = osm_utils.add_trees_to_gsv_map(pano_id, selected_points, metadata_df, True)
            if not gdf_Lines.empty and save_single:
                gdf_Lines.to_file(pathTreeLines, layer='locations', driver="GPKG")

            if allLines.empty:
                allLines = gdf_Lines
            else:
                allLines = pd.concat([gdf_Lines,allLines], ignore_index=True)

            if allTrees.empty:
                allTrees = gdf_trees
            else:
                allTrees = pd.concat([gdf_trees,allTrees], ignore_index=True)

    pathTreeLines = os.path.join(pathDataGenerated,f"__Kypseli-All-GSV-Tree-Points-CROSSING-Lines.gpkg")
    allLines.to_file(pathTreeLines, layer='locations', driver="GPKG")

    pathTreePoints = os.path.join(pathDataGenerated,f"__Kypseli-All-GSV-Tree-Points-CROSSING-Trees.gpkg")
    allTrees.to_file(pathTreePoints, layer='locations', driver="GPKG")


    # intersections = osm_utils.find_intersections(allTrees)
    # pathTreePoints = os.path.join(pathDataGenerated,f"__Kypseli-All-GSV-Tree-Points-CROSSING-Intersections.gpkg")
    # intersections.to_file(pathTreePoints, layer='locations', driver="GPKG")


    # print(f"{metadata_df['panoID'].to_numpy()}")

    if True:
        exit(0)


    # Create a window and set the mouse callback
    cv2.namedWindow("Depth Image")
    cv2.setMouseCallback("Depth Image", mouse_callback)

    redraw()

    while True:
        # Display the original image
        # display_image = depth_image.copy()
        # display_image = cv2.cvtColor(display_image, cv2.COLOR_GRAY2RGB)

        if stacked_images is not None:
            display_image = stacked_images

        # Show the image
        cv2.imshow("Depth Image", display_image)

        key = cv2.waitKey(1) & 0xFF
        # Exit on pressing the 'q' key
        if key == ord('q'):
            break
        if key == ord('s'):
            print("Save input")
            save_prediction(pano_id)
        if key == ord('h'):
            print("Help")
            print(f"Panorama ID: {pano_id}")
            # print(f"Panorama ID: {pano_id}")
        if key == 8:
            if len(selected_points) > 0:
                selected_points.pop()
                redraw()

        if key == ord('x'):
            print("Delete input")
            selected_points = []
            redraw()

        if key == 81: # Left Arrow Key
            pid = select_previous_panorama(False)
            print(f"Selected Panorama: {pano_id}")
            if pid is None:
                print("done.")
                break
            else:
                pano_id = pid
                load_panorama(pano_id)
                redraw()

        if key == 83: # Right Arrow Key
            pid = select_next_panorama(False)
            print(f"Selected Panorama: {pano_id}")
            if pid is None:
                print("done.")
                break
            else:
                pano_id = pid
                load_panorama(pano_id)
                redraw()

        if key == ord(' '):
            print("Select next panorama")
            save_prediction(pano_id)
            pid = select_next_panorama(True)
            print(f"Selected Panorama: {pano_id}")
            if pid is None:
                print("done.")
                break
            else:
                pano_id = pid
                load_panorama(pano_id)
                redraw()
            # regular_image, depth_image, depth_data = load_image_set(pano_id)
            # if len(depth_image.shape) == 3:
            #     print("Yes, converting...")
            #     depth_image = cv2.cvtColor(depth_image, cv2.COLOR_BGR2GRAY)
            #
            # selected_points = []

    cv2.destroyAllWindows()

