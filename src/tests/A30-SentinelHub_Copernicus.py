import datetime
import os

import matplotlib.pyplot as plt
import numpy as np

from sentinelhub import (
    CRS,
    BBox,
    DataCollection,
    DownloadRequest,
    MimeType,
    MosaickingOrder,
    SentinelHubDownloadClient,
    SentinelHubRequest,
    bbox_to_dimensions,
)

from sentinelhub import SHConfig

# The following is not a package. It is a file utils.py which should be in the same folder as this notebook.
# from utils import plot_image
from PIL import Image

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import geopandas as gpd

import A30


# # Step 1: Configure Sentinel Hub API
# config = SHConfig()
# config.instance_id = "Athens-330300"
#
# config.instance_id = 'f91eb966-d94d-42f6-87aa-0787d8342e8e'  # Your Sentinel Hub instance ID
# # config.sh_client_id = 'sh-ded8c602-718a-4872-93df-fabac9f3ecd2'  # Your Sentinel Hub client ID
# # config.sh_client_secret = 'rBdw2AmzqRHajhcIUceFVhmsaRI90XrJ'  # Your Sentinel Hub client secre
#
# config.sh_client_id = 'sh-f7827d59-15a4-4e66-9e1c-db25ccfe0ad1'  # Your Sentinel Hub client ID
# config.sh_client_secret = 'WCaQEVWeEz0koBN4pQznlFvqaYruyAJF'  # Your Sentinel Hub client secre
#
# # config.sh_token_url = 'https://service.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
# config.sh_token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
# config.sh_auth_base_url = 'https://identity.dataspace.copernicus.eu'
# config.sh_base_url = 'https://sh.dataspace.copernicus.eu'
# config.save("Athens-330300")


shapefile = gpd.read_file("/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/Kypseli-All.shp")
bounds = shapefile.total_bounds  # [minx, miny, maxx, maxy]
# Define the bounding box for Sentinel Hub
area_bbox = BBox(bbox=[bounds[0], bounds[1], bounds[2], bounds[3]], crs=CRS.WGS84)


config = SHConfig("Athens-330300")
config.sh_token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'


def get_access_token(cfg):
    client = BackendApplicationClient(client_id=cfg.sh_client_id)
    oauth = OAuth2Session(client=client)
    print(cfg)
    # Get token for the session
    access_token = oauth.fetch_token(token_url=cfg.sh_token_url,
                                     client_secret=cfg.sh_client_secret, include_client_id=True)
    return access_token['access_token']






# Test Sentinel Hub connection
from sentinelhub import SentinelHubCatalog
catalog = SentinelHubCatalog(config=config)
print("Connection successful!")

# curl --request POST --url https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token --header 'content-type: application/x-www-form-urlencoded' --data 'grant_type=client_credentials&client_id=sh-ded8c602-718a-4872-93df-fabac9f3ecd2' --data-urlencode 'client_secret=rBdw2AmzqRHajhcIUceFVhmsaRI90XrJ'

# curl --request POST --url https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token --header 'content-type: application/x-www-form-urlencoded' --data 'grant_type=client_credentials&client_id="sh-ded8c602-718a-4872-93df-fabac9f3ecd2"' --data-urlencode 'client_secret="rBdw2AmzqRHajhcIUceFVhmsaRI90XrJ"'
# access_token = get_token(config)

cfg = config
client = BackendApplicationClient(client_id=cfg.sh_client_id)
oauth = OAuth2Session(client=client)
print(cfg)
# Get token for the session
access_token = oauth.fetch_token(token_url=cfg.sh_token_url,
                                 client_secret=cfg.sh_client_secret, include_client_id=True)

# config.sh_auth_token = access_token
config.sh_auth_token = get_access_token(config)
print(f"Token: {access_token}")



evalscript_true_color = """
    //VERSION=3

    function setup() {
        return {
            input: [{
                bands: ["B02", "B03", "B04"]
            }],
            output: {
                bands: 3
            }
        };
    }

    function evaluatePixel(sample) {
        return [sample.B04, sample.B03, sample.B02];
    }
"""

# Define the evalscript for NDVI
evalscript_ndvi = """
//VERSION=3
function setup() {
    return {
        input: ["B04", "B08"],  // Fetch RED (B04) and NIR (B08) bands
        output: { bands: 2 }
    };
}
function evaluatePixel(sample) {
    return [sample.B04, sample.B08];  // Return RED and NIR bands
}
"""


sentinel_request = SentinelHubRequest(
    evalscript=evalscript_ndvi,
    input_data=[
        SentinelHubRequest.input_data(
            data_collection=DataCollection.SENTINEL2_L2A.define_from(
                name="s2l2a", service_url=config.sh_base_url
            ),
            time_interval=("2023-06-01", "2024-06-30"),
            other_args={"dataFilter": {"mosaickingOrder": "leastCC"}},
        )
    ],
    responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
    bbox=area_bbox,
    size=(2048, 2048),
    config=config,
)
true_color_imgs = sentinel_request.get_data()
print(true_color_imgs)
#
image_array = true_color_imgs[0]


# Extract RED (B04) and NIR (B08) bands
red = image_array[:, :, 0].astype(np.float32)
nir = image_array[:, :, 1].astype(np.float32)

# Calculate NDVI
ndvi = (nir - red) / (nir + red + 1e-6)  # Add small value to avoid division by zero

# Clip NDVI values to range [-1, 1]
ndvi = np.clip(ndvi, -1, 1)
threshold = 0.2
vegetation = ndvi > threshold
total_pixels = ndvi.size
pixels_above_threshold = np.sum(ndvi > threshold)
percentage_above_threshold = (pixels_above_threshold / total_pixels) * 100
print(f"Green percentage: {percentage_above_threshold:.2f}%")

image = Image.fromarray(image_array)
print(f"images: {len(true_color_imgs)}")
plt.imshow(ndvi, cmap="RdYlGn")  # Use colormap for vegetation
# plt.imshow(image)
plt.axis("off")
plt.show()

# plt.imshow(vegetation, cmap="RdYlGn")  # Use colormap for vegetation
# plt.axis("off")
# plt.show()

print(f"Base URL: {config.sh_base_url}")
print(f"Token URL: {config.sh_token_url}")









