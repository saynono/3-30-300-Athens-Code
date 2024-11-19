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

def is_pixel_within_threshold(pixel, pixel_org, threshold):

    pixel = pixel.astype(np.int32)
    pixel_org = pixel_org.astype(np.int32)
    # Subtract Saturation and Value directly
    saturation_diff = abs(pixel[1] - pixel_org[1])
    value_diff = abs(pixel[2] - pixel_org[2])

    # Subtract Hue with wrapping
    hue_diff = abs(pixel[0] - pixel_org[0])
    if hue_diff < 0:
        hue_diff += 180  # Wrap-around for OpenCV hue range [0, 179]
    elif hue_diff >= 180:
        hue_diff -= 180

    # Combined result with wrapped Hue
    result_pixel = np.array([hue_diff, saturation_diff, value_diff], dtype=np.int32)
    result_within = bool((result_pixel < threshold).all())
    # print(f"\nPixel: {pixel}      Pixel_Org: {pixel_org}         hue_diff: {hue_diff}")
    # print(f"pixel[0]: {pixel[0]}        pixel_org[0]: {pixel_org[0]}")
    # print("Result Pixel (HSV difference):", result_pixel, " within threshold: ", result_within)
    # result_within = False
    return result_within

def segment_depth_object(depth_image, start_pixel, threshold):
    """
    Segments an object in a depth image based on the depth value at the specified pixel.

    Parameters:
        depth_image (np.ndarray): The depth image (2D numpy array).
        start_pixel (tuple): The (row, col) of the initial pixel.
        threshold (int): The allowable depth difference to include a pixel in the segment.

    Returns:
        np.ndarray: A binary mask with the segmented object.
    """

    print(f"segment_depth_object : threshold:{threshold}")


    # Get the depth value of the start pixel
    start_depth = depth_image[start_pixel]
    pixel_depth = start_depth
    # Create a mask to keep track of segmented pixels
    mask = np.zeros_like(depth_image, dtype=np.uint8)

    # Create a queue for region growing and initialize with the start pixel
    queue = [start_pixel]
    mask[start_pixel] = 255  # Mark the start pixel as part of the segment
    threshold_total = 20

    temp_pixels_added = 0

    # Region growing
    while queue:
        x, y = queue.pop(0)
        pixel_depth = int(depth_image[x, y])

        # Check the 8-neighborhood of the current pixel
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nx, ny = x + dx, y + dy

            # # Ensure the neighbor is within bounds
            # if 0 <= nx < depth_image.shape[0] and 0 <= ny < depth_image.shape[1]:
            #     # Debugging: Print the values for depth_image[nx, ny] and start_depth
            #     # to confirm they are scalars
            #     # print(f"Checking pixel ({nx}, {ny}) with depth value {depth_image[nx, ny]} against start depth {start_depth}")
            #
            #     # Ensure we're working with scalar depth values for comparison
            #     neighbor_depth = int(depth_image[nx, ny])
            #
            #     # Only proceed if this pixel hasn't been added to the mask yet and meets the depth threshold
            #     if mask[nx, ny] == 0 and abs(neighbor_depth - start_depth) <= threshold:
            #         mask[nx, ny] = 255  # Mark as part of the object
            #         queue.append((nx, ny))


            # Ensure the neighbor is within bounds
            if 0 <= nx < depth_image.shape[0] and 0 <= ny < depth_image.shape[1]:
                neighbor_depth = int(depth_image[nx, ny])

                # Condition: add to mask only if it hasn't been visited and meets the depth criteria
                if (mask[nx, ny] == 0 and
                        abs(pixel_depth-neighbor_depth) <= threshold and
                        abs(start_depth-neighbor_depth) <= threshold_total):
                    mask[nx, ny] = 255  # Mark as part of the object
                    queue.append((nx, ny))

    return mask



def segment_colour_object(image, start_pixel, threshold=(20,40,40)):
    """
    Segments an object in a depth image based on the depth value at the specified pixel.

    Parameters:
        image (np.ndarray): The depth image (2D numpy array).
        start_pixel (tuple): The (row, col) of the initial pixel.
        threshold (int): The allowable depth difference to include a pixel in the segment.

    Returns:
        np.ndarray: A binary mask with the segmented object.
    """

    print(f"segment_colour_object : threshold:{threshold}")


    hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

    # Get the depth value of the start pixel
    start_colour = hsv_image[start_pixel]
    pixel_colour = start_colour
    # Create a mask to keep track of segmented pixels
    height, width = image.shape[:2]
    mask = np.zeros((height,width), dtype=np.uint8)
    # mask = np.full((height,width), 255, dtype=np.uint8)

    # Create a queue for region growing and initialize with the start pixel
    queue = [start_pixel]
    mask[start_pixel] = 255  # Mark the start pixel as part of the segment
    threshold_total = 20
    temp_pixels_added = 0

    # Region growing
    while queue:
        x, y = queue.pop(0)
        pixel_colour = hsv_image[x, y]

        # Check the 8-neighborhood of the current pixel
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nx, ny = x + dx, y + dy

            # # Ensure the neighbor is within bounds
            # if 0 <= nx < depth_image.shape[0] and 0 <= ny < depth_image.shape[1]:
            #     # Debugging: Print the values for depth_image[nx, ny] and start_depth
            #     # to confirm they are scalars
            #     # print(f"Checking pixel ({nx}, {ny}) with depth value {depth_image[nx, ny]} against start depth {start_depth}")
            #
            #     # Ensure we're working with scalar depth values for comparison
            #     neighbor_depth = int(depth_image[nx, ny])
            #
            #     # Only proceed if this pixel hasn't been added to the mask yet and meets the depth threshold
            #     if mask[nx, ny] == 0 and abs(neighbor_depth - start_depth) <= threshold:
            #         mask[nx, ny] = 255  # Mark as part of the object
            #         queue.append((nx, ny))


            # Ensure the neighbor is within bounds
            if 0 <= nx < hsv_image.shape[0] and 0 <= ny < hsv_image.shape[1]:
                neighbor_colour = hsv_image[nx, ny]

                # Condition: add to mask only if it hasn't been visited and meets the depth criteria
                if (mask[nx, ny] == 0 and
                        is_pixel_within_threshold(neighbor_colour, pixel_colour, threshold) ):

                    mask[nx, ny] = 255  # Mark as part of the object
                    queue.append((nx, ny))
                    temp_pixels_added+=1

    print(f"temp_pixels_added: {temp_pixels_added}")

    return mask


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

        do_depth_segment = False
        if do_depth_segment:

            segmented_mask = segment_depth_object(depth_image, clicked_point, threshold=1)
            # Overlay: using 50% transparency for the mask
            color = np.array([0.2, 0.5, 1.0])  # Adjust the values to get the desired color tint

            # Multiply the grayscale image by the color
            mask_3c = cv2.cvtColor(segmented_mask, cv2.COLOR_GRAY2BGR)
            colored_mask = (mask_3c / 255.0) * color
            # colored_mask = (segmented_mask.astype(np.float32) / 255.0) * color  # Normalize grayscale image to [0, 1] range
            colored_mask = (colored_mask * 255).astype(np.uint8)  # Scale back to [0, 255] range

            display_image = cv2.addWeighted(display_image, 1.0, colored_mask, 0.3, 0)
        # else:
        #     display_image = depth_image.copy()


        # grey_value = depth_image[clicked_point[0],clicked_point[1]]
        # raw_depth = depth_data[clicked_point[0],clicked_point[1]]*100
        #
        # selected_points.append((clicked_point[1],clicked_point[0],raw_depth))
        # distance_approx = utils.map_value(grey_value, 10, 122, 200, 500)
        # degrees_clicked = utils.map_value(clicked_point[1],0,2400,-30,330)

        # str = f"[{clicked_point[1]},{clicked_point[0]}] raw distance: {raw_depth:.0f}cm"
        # if clicked_point_prev:
        #     print(f"clicked_point_prev: {clicked_point_prev}    => clicked_point: {clicked_point}")
        #     # Given data
        #     d1 = depth_data[clicked_point[0],clicked_point[1]]*100  # Distance from the third point to the first point
        #     d2 = depth_data[clicked_point_prev[0],clicked_point_prev[1]]*100  # Distance from the third point to the second point
        #     degrees_clicked_prev = utils.map_value(clicked_point_prev[1],0,2400,-30,330)
        #     theta_degrees = abs(degrees_clicked-degrees_clicked_prev)  # Angle between the two points from the third point (in degrees)
        #
        #     # Convert angle to radians
        #     theta = math.radians(theta_degrees)
        #
        #     # Calculate the distance using the law of cosines
        #     D = math.sqrt(d1**2 + d2**2 - 2 * d1 * d2 * math.cos(theta))
        #     str += f"    Distance between two points: {D:.0f}"
        #     cv2.line(display_image, (clicked_point[1], clicked_point[0]), (clicked_point_prev[1], clicked_point_prev[0]), (255, 0, 0), 1)
        #     # cv2.circle(display_image, (clicked_point_prev[1], clicked_point_prev[0]), radius=5, color=(255, 0, 0), thickness=-1)



        # cv2.circle(display_image, (clicked_point[1], clicked_point[0]), radius=5, color=(255, 0, 0), thickness=-1)
        # cv2.addText(display_image, str,(clicked_point[1]+20, clicked_point[0]), "OpenSans", 10, color=(255, 0, 0) )
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

        # Set Saturation to maximum (255)
        # hsv_image[:, :, 1] = 255

        # Set Value to maximum (255)
        hsv_image[:, :, 2] = 255

        # Convert back to RGB
        display_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)
        # cv2.drawContours(display_image, contours, -1, color=(0,255,255), thickness=1)


        do_colour_segment = False
        if do_colour_segment:
            color = np.array([0.2, 0.0, 0.3])
            colour_mask = segment_colour_object(regular_image, clicked_point, threshold=(4,30,200))
            contours, _ = cv2.findContours(colour_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(display_image, contours, -1, color=(255,255,0), thickness=1)

            overlap_mask = cv2.bitwise_and(segmented_mask, colour_mask)


            # colour_mask = cv2.cvtColor(colour_mask, cv2.COLOR_GRAY2RGB)
            mask_3c = cv2.cvtColor(colour_mask, cv2.COLOR_GRAY2BGR)
            colour_mask = (mask_3c / 255.0) * color
            # colored_mask = (segmented_mask.astype(np.float32) / 255.0) * color  # Normalize grayscale image to [0, 1] range
            colour_mask = (colour_mask * 255).astype(np.uint8)  # Scale back to [0, 255] range

            contours, _ = cv2.findContours(overlap_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(display_image, contours, -1, color=(255,0,255), thickness=3)

            display_image = cv2.addWeighted(display_image, 1.0, colour_mask, 1.0, 0)
            # display_image = colour_mask
        else:
            display_image = np.copy(regular_image)


        draw_points(display_image, selected_points)
        # str = f"Degrees: {degrees_clicked:.0f} \nDistance (approx): {distance_approx:.0f}"
        # cv2.addText(display_image, str,(20,30), "OpenSans", 10, color=(255, 0, 0) )
        # add_text(display_image,str,(20,30))


        stacked_images[2*height:3*height, :] = display_image

        display_image = regular_image.copy()
        draw_points(display_image, selected_points)

        stacked_images[0:height, 0:] = display_image

#
#
# def create_gsv_map(metadata_df):
#
#     gdf = gpd.GeoDataFrame(
#         metadata_df,
#         geometry=[Point(xy) for xy in zip(metadata_df['longitude'], metadata_df['latitude'])],
#         crs="EPSG:4326"  # Use WGS84 (latitude/longitude) CRS
#     )
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

    # gsvRoot         = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/GSV-Data/panodata-cache"
    # pathRoot = "/home/nono/Documents/workspaces/cpp/darknet/Training/Athens-3-30-300-Panorama-Grey/"
    # pathNames		= os.path.join(pathRoot,"Athens-3-30-300-Panorama-Grey.names")
    # pathImage		= os.path.join(pathRoot,"panorama-final-depth/img_0w4VcFFiFSGZWk022DL-zg_panorama.png")

    # pathImage            = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/images/img_0bU8ymfqZtXa9Z88P4ImPQ_panorama__sharper.jpg"
    # pathImage            = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/images/img_0bU8ymfqZtXa9Z88P4ImPQ_panorama__sharper.jpg"
    # pathImageDepth       = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/temp/img_0bU8ymfqZtXa9Z88P4ImPQ_panorama__sharper.png"


    # pathImage            = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/images/img_0A1aUxQvyr_KqmaokVoqvQ_300.0_0.jpg"
    # pathImageDepth       = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/temp/img_0A1aUxQvyr_KqmaokVoqvQ_300.0_0.png"

    # pathImage            = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/images/img_0BNMX3AxiQWOvZo_82dOyA_180.0_0.jpg"
    # pathImageDepth       = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/temp/img_0BNMX3AxiQWOvZo_82dOyA_180.0_0.png"

    # pathImage            = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/images/img_0A1aUxQvyr_KqmaokVoqvQ_panorama.jpg"
    # pathImageDepth       = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/temp/img_0A1aUxQvyr_KqmaokVoqvQ_panorama_stitched_sharper.png"

    # pathImageStiched     = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/temp/img_0A1aUxQvyr_KqmaokVoqvQ_panorama_stitched_sharper.jpg"

    pathMetaData         = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/metadata"
    pathMetaDataSelected = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/selected_pano_ids.txt"

    pathGSVPoints        = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/generated/Kypseli-All-GSV-Points.gpkg"
    pathGSVPointsTemp    = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/generated/Kypseli-All-GSV-Points-TEMP.gpkg"



    # regular_image = cv2.imread(pathImage, cv2.IMREAD_UNCHANGED)
    # depth_image = cv2.imread(pathImageDepth, cv2.IMREAD_UNCHANGED)  # Load your depth image

    # metadata_df = utils.load_all_csvs(pathMetaData)
    metadata_df = utils.load_all_csvs(pathMetaDataSelected)
    # res = utils.find_entry_by_panoID(metadata_df,"0A1aUxQvyr_KqmaokVoqvQ")
    # utils.print_df_results(res)


    pano_id_1 = "gp3wUHUQypyd-Eyody0NgA"
    pano_id_2 = "Dr-EZ9xWZKcx5jzWfX7kQQ"

    # Create a window and set the mouse callback
    cv2.namedWindow("Depth Image")
    cv2.setMouseCallback("Depth Image", mouse_callback)


    pano_id = pano_id_1
    load_panorama(pano_id)

    # create_gsv_map()

    gdf_gsv_points = create_gsv_map(metadata_df)
    # gdf_gsv_points.to_file(pathGSVPoints, layer='locations', driver="GPKG")
    #
    # gdf_temp_gsv_points = temp_create_gsv_map(metadata_df)
    # gdf_temp_gsv_points.to_file(pathGSVPointsTemp, layer='locations', driver="GPKG")


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

