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
import cv2

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


# Step 1: Configure Sentinel Hub API
config = SHConfig()
config.instance_id = "Athens-330300"

do_setup_sentinel_hub = True
if do_setup_sentinel_hub:
    config.instance_id = 'f91eb966-d94d-42f6-87aa-0787d8342e8e'  # Your Sentinel Hub instance ID
    config.sh_client_id = 'sh-ded8c602-718a-4872-93df-fabac9f3ecd2'  # Your Sentinel Hub client ID
    config.sh_client_secret = 'rBdw2AmzqRHajhcIUceFVhmsaRI90XrJ'  # Your Sentinel Hub client secre

    config.sh_client_id = 'sh-f7827d59-15a4-4e66-9e1c-db25ccfe0ad1'  # Your Sentinel Hub client ID
    config.sh_client_secret = 'WCaQEVWeEz0koBN4pQznlFvqaYruyAJF'  # Your Sentinel Hub client secre

    # config.sh_token_url = 'https://service.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    config.sh_token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    config.sh_auth_base_url = 'https://identity.dataspace.copernicus.eu'
    config.sh_base_url = 'https://sh.dataspace.copernicus.eu'
    config.save("Athens-330300")

print(config)


test_connection = True
if test_connection:
    try:
        # Test Sentinel Hub connection
        from sentinelhub import SentinelHubCatalog
        catalog = SentinelHubCatalog(config=config)
        print("Connection successful!")

# curl --request POST --url https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token --header 'content-type: application/x-www-form-urlencoded' --data 'grant_type=client_credentials&client_id=sh-ded8c602-718a-4872-93df-fabac9f3ecd2' --data-urlencode 'client_secret=rBdw2AmzqRHajhcIUceFVhmsaRI90XrJ'

# curl --request POST --url https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token --header 'content-type: application/x-www-form-urlencoded' --data 'grant_type=client_credentials&client_id="sh-ded8c602-718a-4872-93df-fabac9f3ecd2"' --data-urlencode 'client_secret="rBdw2AmzqRHajhcIUceFVhmsaRI90XrJ"'

        client = BackendApplicationClient(client_id=config.sh_client_id)
        oauth = OAuth2Session(client=client)

        # Get token for the session
        access_token = oauth.fetch_token(token_url=config.sh_token_url,
                                  client_secret=config.sh_client_secret, include_client_id=True)
        config.sh_auth_token = access_token['access_token']
        print(f"Token: {access_token['access_token']}")
        # All requests using this session will have an access token automatically added
        # resp = oauth.get("https://service.sentinel-hub.com/configuration/v1/wms/instances")
        # print(f"resp.content: {resp.content}")


    except Exception as e:
        print(f"Error: {e}")




betsiboka_coords_wgs84 = (46.16, -16.15, 46.51, -15.58)
resolution = 60
betsiboka_bbox = BBox(bbox=betsiboka_coords_wgs84, crs=CRS.WGS84)
betsiboka_size = bbox_to_dimensions(betsiboka_bbox, resolution=resolution)

print(f"Image shape at {resolution} m resolution: {betsiboka_size} pixels")
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

request = SentinelHubRequest(
    evalscript=evalscript_true_color,
    input_data=[
        SentinelHubRequest.input_data(
            data_collection=DataCollection.SENTINEL2_L1C,
            time_interval=("2020-06-12", "2020-06-13"),
        )
    ],
    responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
    bbox=betsiboka_bbox,
    size=betsiboka_size,
    config=config,
)

print(f"request : {request.config} => {request}")

import requests

# Set the headers and payload
url = "https://sh.dataspace.copernicus.eu/api/v1/process"
headers = {
    "Authorization": f"Bearer {access_token['access_token']}",
    "Content-Type": "application/json"
}
payload = {
    "input": {
        "bounds": {
            "bbox": [23.6, 37.8, 23.8, 38.0]
        },
        "data": [{
            "type": "S2L2A",
            "timeInterval": "2023-01-01/2023-01-31"
        }]
    },
    "output": {
        "width": 512,
        "height": 512,
        "responses": [{"identifier": "default", "format": {"type": "image/png"}}]
    },
    "evalscript": evalscript_true_color
}

print(f"HEADER: {headers}")

# Make the request
response = requests.post(url, headers=headers, json=payload)

# Save the response
if response.status_code == 200:
    with open("output_image.png", "wb") as f:
        f.write(response.content)
    print("Image saved successfully!")
    cv2.imshow("Satellite Image", response.content)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

else:
    print(f"Error: {response.status_code} - {response.text}")




# true_color_imgs = request.get_data()
# #
# image = true_color_imgs[0]
# print(f"Image type: {image.dtype}")

print(f"Base URL: {config.sh_base_url}")
print(f"Token URL: {config.sh_token_url}")









