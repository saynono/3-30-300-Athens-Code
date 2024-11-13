import os, os.path

import numpy as np
from PIL import Image
import math
import cv2
import skimage as ski
from numpy.random import randint

# from /home/nono/Documents/workspaces/ai/Depth-Anything-V2/metric_depth/depth_anything_v2.dpt import DepthAnythingV2
# Load your image and depth map

pathRoot = "/home/nono/Documents/workspaces/cpp/darknet/Training/Athens-3-30-300-Panorama-Grey/"
# pathImage		= os.path.join(pathRoot,"panorama-final-depth/img_0w4VcFFiFSGZWk022DL-zg_panorama.png")
# pathImage		= os.path.join(pathRoot,"panorama-final-depth/img_0BNMX3AxiQWOvZo_82dOyA_panorama.png")

pathImage		= "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/temp/img_0eS4RnxNZPOhv3PhKvm0CQ_240.0_0.jpg"

# pathImageDepth = "/home/nono/Documents/workspaces/cpp/darknet/Training/Athens-3-30-300-Panorama-Grey/panorama-final-depth/img_0BNMX3AxiQWOvZo_82dOyA_panorama.png"
pathImageDepth = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/temp/img_0eS4RnxNZPOhv3PhKvm0CQ_240.0_0_indoors.png"

image = Image.open(pathImage).convert('RGB')
# image = cv2.imread(pathImage)
# image /= 255.0

depth_image = Image.open(pathImageDepth).convert("L")
depth_map = np.array(depth_image).astype(np.float32)
depth_map /= 255.0

depth_max = 80.0

# Get image dimensions
width, height = image.size

# Convert FOV to radians
fov_y = 60  # degrees
fov_y_rad = math.radians(fov_y)
fov_x = 60  # degrees
fov_x_rad = math.radians(fov_x)

# Calculate focal length in pixels
focal_y_length = 346.41 # height / (2 * math.tan(fov_y_rad / 2))
focal_x_length = 346.41 #width / (2 * math.tan(fov_x_rad / 2))

def depth_to_point_cloud(depth_map, image, focal_length_x, focal_length_y ):
    points = []
    # colors = np.array(image).reshape((-1, 3))  # Get color info per pixel
    # height, width = depth_map.shape

    # Generate 3D points
    for y in range(height):
        for x in range(width):
            # Get depth value
            z = depth_map[y, x]
            if z > 0 or True:  # Ignore invalid depths

                # # Calculate angles in spherical coordinates
                # theta = (y / height) * math.radians(60) - math.radians(30)  # Vertical angle (±30 degrees from center)
                # phi = (x / width) * math.radians(360)  # Horizontal angle (0 to 360 degrees)
                #
                # # Convert spherical coordinates to Cartesian coordinates
                # X = r * math.cos(theta) * math.sin(phi)
                # Y = r * math.sin(theta)
                # Z = r * math.cos(theta) * math.cos(phi)

                # x, y = np.meshgrid(np.arange(width), np.arange(height))
                X = (x - width / 2) / focal_length_x
                Y = (y - height / 2) / focal_length_y

                if(randint(1000)>900):
                    print(f"[{x},{y}] : z=>{z}")

                points.append([X*z,Y*z,z])
            else:
                print(f"Z not okay")
    return np.array(points)

# Convert the depth map and image to a point cloud
points = depth_to_point_cloud(depth_map, image, focal_x_length, focal_y_length )

color_image = Image.open(pathImage).convert('RGB')
colors = np.array(color_image).reshape(-1, 3) / 255.0


# Generate mesh grid and calculate point cloud coordinates
x, y = np.meshgrid(np.arange(width), np.arange(height))
x = (x - width / 2) / focal_x_length
y = (y - height / 2) / focal_y_length
z = np.array(depth_map)
# points = np.stack((np.multiply(x, z), np.multiply(y, z), z), axis=-1).reshape(-1, 3)

# Save the point cloud
import open3d as o3d

def save_point_cloud(points, colors, filename="/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/temp/pointcloud.ply"):
    point_cloud = o3d.geometry.PointCloud()
    point_cloud.points = o3d.utility.Vector3dVector(points)
    point_cloud.colors = o3d.utility.Vector3dVector(colors)  # Normalize colors
    o3d.io.write_point_cloud(filename, point_cloud)
    print(f"Point cloud saved to {filename}")




# save_point_cloud(points, colors)


# colors = np.random.rand(len(points), 3)

print(f"Legnth points: {len(o3d.utility.Vector3dVector(points))}")
print(f"Legnth colors: {len(o3d.utility.Vector3dVector(colors))}")
points *= 80.0

# Create an Open3D PointCloud object
point_cloud = o3d.geometry.PointCloud()
point_cloud.points = o3d.utility.Vector3dVector(points)
point_cloud.colors = o3d.utility.Vector3dVector(colors)

# ply_file_path = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/temp/img_0eS4RnxNZPOhv3PhKvm0CQ_240.0_0.ply"
# point_cloud = o3d.io.read_point_cloud(ply_file_path)


# Visualize the point cloud
o3d.visualization.draw_geometries([point_cloud])
# o3d.visualization.draw(point_cloud)
#
#
# ski.io.imshow(np.array(depth_image))
# ski.io.show()

