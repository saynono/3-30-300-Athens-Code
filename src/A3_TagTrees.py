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
import A3_StitchImprove
from geopy.distance import distance as geopy_distance


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
    elif event == cv2.EVENT_MOUSEMOVE:
        print(f"Mouse Moved: [{x},{y}]")



def redraw():
        global clicked_point, clicked_point_prev, segmented_mask, depth_image, stacked_images, colored_mask, regular_image, stitched_image, depth_data, selected_points
        height, width = depth_image.shape[:2]
        display_image = depth_image.copy()
        display_image = cv2.cvtColor(display_image, cv2.COLOR_GRAY2RGB)


        draw_points(display_image, selected_points)

        str = f"Panorama [{pano_id}]     Predictions: {has_predictions}"
        add_text(display_image, str,(10, 20))

        stacked_images[height:2*height, 0:width] = display_image


        display_image = regular_image.copy()


        # Convert RGB image to HSV
        hsv_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2HSV)

        # Set Saturation to maximum (255)
        # hsv_image[:, :, 1] = 255

        # Set Value to maximum (255)
        hsv_image[:, :, 2] = 255

        # Convert back to RGB
        display_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)
        # cv2.drawContours(display_image, contours, -1, color=(0,255,255), thickness=1)



        # display_image = np.copy(regular_image)


        draw_points(display_image, selected_points)
        # str = f"Degrees: {degrees_clicked:.0f} \nDistance (approx): {distance_approx:.0f}"
        # cv2.addText(display_image, str,(20,30), "OpenSans", 10, color=(255, 0, 0) )
        # add_text(display_image,str,(20,30))


        stacked_images[2*height:3*height, :] = display_image

        display_image = regular_image.copy()
        draw_points(display_image, selected_points)

        stacked_images[0:height, 0:] = display_image


def load_panorama(pano_id):
    global regular_image, depth_image, depth_data, stitched_image, display_image, stacked_images, has_predictions

    regular_image, depth_image, depth_data = load_image_set(pano_id)

    has_predictions = load_prediction(pano_id)

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
    global selected_points, gsvDataPrediction
    path = os.path.join(gsvDataPrediction,f"predicted_{pano_id}.csv")
    print(f"Loading Preditions. {pano_id} -> exists: {os.path.isfile(path)}")
    selected_points = []
    if os.path.isfile(path):
        df = pd.read_csv(path, sep=",")
        selected_points = []
        for index, item in df.iterrows():
            values = item.values
            selected_points.append((int(values[0]),int(values[1]),values[2]))
        return True
    return False


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



if __name__ == "__main__":



    # Example usage

    gsvRoot = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/GSV-Data/"
    gsvPanoramaRoot = os.path.join(gsvRoot,"panoramas-final-new/")
    gsvDepthRoot = os.path.join(gsvRoot,"panoramas-depth-new/")
    gsvDataPrediction = os.path.join(gsvRoot,"prediction-data/")

    pathMetaData         = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/metadata"
    pathMetaDataSelected = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/selected_pano_ids.txt"

    pathGSVPoints        = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/generated/Kypseli-All-GSV-Points.gpkg"
    pathGSVPointsTemp    = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/generated/Kypseli-All-GSV-Points-TEMP.gpkg"


    metadata_df = utils.load_all_csvs(pathMetaDataSelected)

    pano_id = -1
    pano_id = select_next_panorama()
    if pano_id is None:
        print("Error: No data could be loaded.")
        exit()

    cv2.namedWindow("Depth Image")
    cv2.setMouseCallback("Depth Image", mouse_callback)

    load_panorama(pano_id)
    redraw()

    while True:

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

    cv2.destroyAllWindows()

