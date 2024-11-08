
import matplotlib.pyplot as plt

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
segmented_mask = None


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



# Mouse callback function
def mouse_callback(event, x, y, flags, param):
    global clicked_point, segmented_mask, depth_image

    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_point = (y, x)  # Note: OpenCV uses (row, col) format
        print(f"clicked : {clicked_point}")
        segmented_mask = segment_depth_object(depth_image, clicked_point, threshold=1)



if __name__ == "__main__":



    # Example usage

    pathRoot = "/home/nono/Documents/workspaces/cpp/darknet/Training/Athens-3-30-300-Panorama-Grey/"
    pathNames		= os.path.join(pathRoot,"Athens-3-30-300-Panorama-Grey.names")
    pathImage		= os.path.join(pathRoot,"panorama-final-depth/img_0w4VcFFiFSGZWk022DL-zg_panorama.png")

    depth_image = cv2.imread(pathImage, cv2.IMREAD_UNCHANGED)  # Load your depth image
    # Convert to grayscale if the image has multiple channels
    if len(depth_image.shape) == 3:
        print("Yes, converting...")
        depth_image = cv2.cvtColor(depth_image, cv2.COLOR_BGR2GRAY)
    # depth_image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)  # Replace with your depth image
    # start_pixel = (50, 50)  # Example starting point
    # threshold = 10  # Depth difference threshold
    #
    # # Run segmentation
    # segmented_mask = segment_depth_object(depth_image, start_pixel, threshold)
    #
    # # Display result
    # cv2.imshow("Segmented Object", segmented_mask)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # Create a window and set the mouse callback
    cv2.namedWindow("Depth Image")
    cv2.setMouseCallback("Depth Image", mouse_callback)

    edges = ski.filters.sobel(depth_image)

    # Overlay the edge image on the original image
    alpha = 0.7  # Weight for the original image
    beta = 0.3   # Weight for the edges

    # Blend images
    # overlayed_image = (alpha * depth_image + beta * edges)

    # ski.io.imshow(edges)
    # ski.io.show()
    #
    # # log_image = ski.filters.gaussian(depth_image, sigma=2)
    # log_image = ski.filters.laplace(depth_image)
    # ski.io.imshow(log_image)
    # ski.io.show()

    # Compute gradients in x and y directions
    grad_x = ski.filters.sobel_v(depth_image)
    grad_y = ski.filters.sobel_h(depth_image)

    # Compute the gradient magnitude and direction
    gradient_magnitude = np.hypot(grad_x, grad_y)
    gradient_direction = np.arctan2(grad_y, grad_x)

    # Display results
    plt.figure(figsize=(15, 5))
    plt.subplot(1, 3, 1)
    plt.title("Gradient Magnitude")
    plt.imshow(gradient_magnitude, cmap="gray")

    plt.subplot(1, 3, 2)
    plt.title("Gradient Direction")
    plt.imshow(gradient_direction, cmap="hsv")  # HSV colormap for direction visualization

    # Detect folds by identifying smooth changes in direction
    folds = np.abs(np.gradient(gradient_direction)[0]) > 0.5  # Adjust threshold as needed

    plt.subplot(1, 3, 3)
    plt.title("Detected Folds (Smooth Gradient Change)")
    plt.imshow(folds, cmap="gray")
    plt.show()

    # # Apply Sobel filters in the x and y directions
    # sobel_x = ski.filters.sobel_v(depth_image)  # Vertical edges
    # sobel_y = ski.filters.sobel_h(depth_image)  # Horizontal edges
    #
    # # Combine the Sobel x and y results
    # edges_combined = np.hypot(sobel_x, sobel_y)
    #
    # # Optional: Apply a threshold to make edges more pronounced
    # threshold = 0.1  # Adjust as needed
    # edges_thresholded = (edges_combined > threshold).astype(float)
    # ski.io.imshow(edges_thresholded)
    # ski.io.show()



    while True:
        # Display the original image
        display_image = depth_image.copy()

        # Overlay the segmented mask if it exists
        if segmented_mask is not None:
            # Overlay: using 50% transparency for the mask
            display_image = cv2.addWeighted(display_image, 0.7, segmented_mask, 0.3, 0)

        # Mark the clicked point if it exists
        if clicked_point is not None:
            cv2.circle(display_image, (clicked_point[1], clicked_point[0]), radius=5, color=(255, 0, 0), thickness=-1)

        # Show the image
        cv2.imshow("Depth Image", display_image)

        # Exit on pressing the 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

