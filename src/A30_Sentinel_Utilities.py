import datetime
import os

import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_bounds
from rasterio.mask import mask
from rasterio.features import rasterize
from affine import Affine
from shapely import (
    Point
)

from sentinelhub import (
    CRS,
    BBox,
    DataCollection,
    SentinelHubCatalog,
    DownloadRequest,
    MimeType,
    MosaickingOrder,
    SentinelHubDownloadClient,
    SentinelHubRequest,
    bbox_to_dimensions,
)

from shapely.geometry import (
    mapping,
    Polygon,

)

import utils

# The following is not a package. It is a file utils.py which should be in the same folder as this notebook.
# from utils import plot_image

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

# # Step 1: Configure Sentinel Hub API
# config = SHConfig()
# config.instance_id = "Athens-330300"
##
# # config.sh_token_url = 'https://service.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
# config.sh_token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
# config.sh_auth_base_url = 'https://identity.dataspace.copernicus.eu'
# config.sh_base_url = 'https://sh.dataspace.copernicus.eu'
# config.save("Athens-330300")


def get_access_token(cfg):
    client = BackendApplicationClient(client_id=cfg.sh_client_id)
    oauth = OAuth2Session(client=client)
    print(cfg)
    # Get token for the session
    access_token = oauth.fetch_token(token_url=cfg.sh_token_url,
                                     client_secret=cfg.sh_client_secret, include_client_id=True)
    return access_token['access_token']


def get_image_list_from_sentinel(config, area_bbox, time_interval):
    catalog = SentinelHubCatalog(config=config)
    search_iterator = catalog.search(
        DataCollection.SENTINEL2_L2A,  # Sentinel-2 Level-2A collection
        bbox=area_bbox,
        time=time_interval,
        filter="eo:cloud_cover < 50",
        fields={"include": ["id", "properties.datetime", "properties.eo:cloud_cover"], "exclude": []},
    )
    results = list(search_iterator)

    print("-----------------------------")

    for idx, result in enumerate(results):
        print(f"Result {idx + 1}:")
        print(f"  Date: {result['properties']['datetime']}")
        print(f"  Cloud Cover: {result['properties']['eo:cloud_cover']}")
        print(f"  Resolution: {result['properties'].get('resolution', 'N/A')}")
        print(f"  Tile ID: {result}")
        print()

    print("-----------------------------")

    return results

def get_latest_nvdi_from_bbox(config, area_bbox, time_interval):

    if not (hasattr(config, 'sh_auth_token') and config.sh_auth_token):
        config.sh_auth_token = get_access_token(config)

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
                time_interval=time_interval,
                other_args={"dataFilter": {"mosaickingOrder": "leastCC"}},
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=area_bbox,
        size=(2048, 2048),
        config=config,
    )
    true_color_imgs = sentinel_request.get_data()
    image_array = true_color_imgs[0]

    # Extract RED (B04) and NIR (B08) bands
    red = image_array[:, :, 0].astype(np.float32)
    nir = image_array[:, :, 1].astype(np.float32)

    # Calculate NDVI
    ndvi = (nir - red) / (nir + red + 1e-6)  # Add small value to avoid division by zero

    # Clip NDVI values to range [-1, 1]
    ndvi = np.clip(ndvi, -1, 1)
    ndvi_normalized = ((ndvi+1)/2.0 *255).astype(np.uint8)
    # ndvi_normalized = (ndvi / np.max(ndvi) * 255).astype(np.uint8)

    image_array = np.dstack((image_array, ndvi_normalized))

    return image_array


def create_geotiff(img_array, area_bbox):
    # Example data: Create a mock NDVI array
    width, height = 512, 512
    # ndvi_data = np.random.random((height, width)).astype(np.float32)

    # Define the GeoTIFF metadata
    # bounds = [23.6, 37.8, 23.8, 38.0]  # Example bounding box (minx, miny, maxx, maxy)
    transform = from_bounds(*area_bbox, width, height)
    meta = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': 1,  # Single band
        'dtype': 'float32',
        'crs': 'EPSG:4326',  # Coordinate Reference System
        'transform': transform
    }

    # Create the GeoTIFF in memory
    with MemoryFile() as memfile:
        with memfile.open(**meta) as dataset:
            dataset.write(img_array, 1)  # Write the NDVI data to band 1

            # Access the GeoTIFF data as bytes
            memfile.seek(0)
            geotiff_bytes = memfile.read()
            mem_meta = dataset.meta.copy()


        # Save the in-memory GeoTIFF to disk
        output_path = "saved_from_memory.tif"
        with open(output_path, "wb") as f:
            f.write(memfile.read())


    # The GeoTIFF is now stored in `geotiff_bytes` as a byte object
    print(f"GeoTIFF size in memory: {len(geotiff_bytes)} bytes")

    return geotiff_bytes, mem_meta


def mask_as_geotiff(geotiff_men, geometry):
    geometry_geojson = [mapping(geometry)]  # Convert to GeoJSON-like format
    # out_image, out_transform = mask(geotiff_men, geometry_geojson, crop=False)
    # Mask the raster in memory
    with MemoryFile() as memfile:
        with memfile.open(**geotiff_men.meta) as dataset:
            # Apply the mask
            dataset.write(geotiff_men.read())
            out_image, out_transform = mask(dataset, geometry_geojson, crop=False)
            # Update metadata for the cropped raster
            out_meta = memfile.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform
            })
    return out_image, out_meta

def create_mask(image, polygon, extent):
    # Create a mask array where the polygon covers the image
    array_shape = image.shape
    transform = from_bounds(*extent, array_shape[1], array_shape[0])
    mask = rasterize(
        [(polygon, 1)], out_shape=array_shape, transform=transform, fill=0, dtype=np.uint8
    )

    # Apply the mask to the image np.nan == transparent, 0=black, 255:white
    masked_image = np.where(mask == 1, image, np.nan)
    return masked_image

def get_green_coverage(img, bounds, point, radius=300, threshold=150):

    circle_gdf = gpd.GeoDataFrame(geometry=[Point(point)], crs="EPSG:4326")  # WGS84
    circle_gdf = utils.create_buffer_in_meters(circle_gdf,radius)
    circle_geom = circle_gdf.geometry.unary_union

    img_masked = create_mask(img, circle_geom, bounds)

    nan_mask = np.isnan(img_masked)
    non_nan_count = np.sum(~nan_mask)
    total_pixels = non_nan_count

    result = (np.sum(img_masked > threshold) / total_pixels)

    return result, img_masked
