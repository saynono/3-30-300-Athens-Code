import os.path

from sentinelhub import (
    CRS,
    BBox,
    SHConfig
)
import geopandas as gpd
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

from shapely.geometry import (
    Point
)

import A30_Sentinel_Utilities as A30_utility
import utils
import cv2

if __name__ == "__main__":

    config = SHConfig("Athens-330300")
    config.sh_token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'

    aoi_gdf = gpd.read_file("/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/maps/Kypseli-All/Kypseli-All.shp")

    satellite_img_path = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/temp/sentinel.png"
    satellite_np_path = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/temp/sentinel"

    root = '../../3-30-300-Athens-Data/maps/Kypseli-All/'
    shape_file = "Kypseli-All.shp"

    root = os.path.abspath(root)
    root_generated = os.path.join(root, "generated/")

    shape_file_name = os.path.splitext(os.path.basename(shape_file))[0]
    pathResidentialBuildingsShp = os.path.join(root_generated, shape_file_name+"-Residential-Buildings.gpkg")

    if os.path.exists(pathResidentialBuildingsShp):
        buildings_gdf = gpd.read_file(pathResidentialBuildingsShp)
    else:
        print(f"Couldn't Find Buildings File: {pathResidentialBuildingsShp}")
        exit(1)
    if 'green_coverage' not in buildings_gdf.columns:
        buildings_gdf['green_coverage'] = float(-1)


# Ensure GeoDataFrame is in the same CRS as the raster
    if aoi_gdf.crs != 'EPSG:4326':
        aoi_gdf = aoi_gdf.to_crs('EPSG:4326')


    aoi_buffered_gdf = utils.create_buffer_in_meters(aoi_gdf,300)

    bounds = aoi_buffered_gdf.total_bounds  # [minx, miny, maxx, maxy]
    geometry = aoi_gdf.geometry.unary_union

    # Define the bounding box for Sentinel Hub
    area_bbox = BBox(bbox=[bounds[0], bounds[1], bounds[2], bounds[3]], crs=CRS.WGS84)

    time_interval = ("2024-09-01", "2024-09-30")  # Time range for the query


    geometry = aoi_gdf.geometry.unary_union

    if os.path.exists(satellite_np_path+".npy"):
        # ndvi = cv2.imread(satellite_img_path)
        image = np.load(satellite_np_path+".npy")
    else:
        A30_utility.get_image_list_from_sentinel(config, area_bbox, time_interval)
        image = A30_utility.get_latest_nvdi_from_bbox(config, area_bbox, time_interval)
        np.save(satellite_np_path,image)
        print(f"len(image.shape) : {len(image.shape)}")
        # image = cv2.cvtColor(ndvi, cv2.COLOR_RGB2BGR)
        # image = ndvi
        # normalized_image = (image / np.max(image) * 255).astype(np.uint8)
        cv2.imwrite(satellite_img_path, image)


    circle_gdf = gpd.GeoDataFrame(geometry=[Point(geometry.centroid)], crs="EPSG:4326")  # WGS84
    circle_gdf = utils.create_buffer_in_meters(circle_gdf,300)
    circle_geom = circle_gdf.geometry.unary_union

    threshold = 160

    ndvi = image[:,:,2]
    ndvi_perimeter = A30_utility.create_mask(ndvi, geometry, bounds)
    ndvi_threshold = ndvi_perimeter.copy()
    ndvi_threshold[ndvi_threshold < threshold] = np.nan
    green_coverage_selected, ndvi_threshold = A30_utility.get_green_coverage(ndvi_threshold, bounds, geometry.centroid, 600, threshold)


    green_coverage_overall, _ = A30_utility.get_green_coverage(ndvi_perimeter, bounds, geometry.centroid, 30000, threshold)
    green_coverage_selected, img_masked = A30_utility.get_green_coverage(ndvi, bounds, geometry.centroid, 300, threshold)


    do_calculate_buildings = False

    if do_calculate_buildings:
        for idx, building in buildings_gdf.iterrows():

            green_coverage_building, img_masked = A30_utility.get_green_coverage(ndvi, bounds, building.geometry.centroid, 300, threshold)
            print(f"#{idx} green_coverage_building: {(green_coverage_building*100):.2f}%")
            buildings_gdf.at[idx, 'green_coverage'] = green_coverage_building

        buildings_gdf.to_file(pathResidentialBuildingsShp, driver="GPKG")  # Save as shapefile


    print(f"Green percentage Selected: {(green_coverage_overall*100):.2f}%")
    print(f"Green percentage Selected: {(green_coverage_selected*100):.2f}%")


    raster_extent = [bounds[0], bounds[2], bounds[1], bounds[3]]

    fig, ax = plt.subplots(figsize=(8, 8))
    im = ax.imshow(ndvi_perimeter, cmap='Greys_r', extent=bounds, interpolation="nearest")


    cbar = fig.colorbar(im, ax=ax, orientation="vertical")
    cbar.set_label("NDVI Index")  # Label for the colorbar

    ax.imshow(ndvi_threshold, cmap='winter', extent=bounds, interpolation="nearest")
    ax.imshow(img_masked, cmap='RdBu', extent=bounds, interpolation="nearest")
    ax.legend()
    aoi_gdf.plot(ax=ax,color="none", edgecolor="black", alpha=0.9)
    aoi_buffered_gdf.plot(ax=ax,facecolor="none", edgecolor="gray", alpha=0.9)

    plt.title(f"Tree coverage [Threshold {threshold}] | Overall: {(green_coverage_overall*100):.2f}%    Selection: {(green_coverage_selected*100):.2f}%")
    plt.axis("equal")
    plt.show()

    # plt.imshow(vegetation, cmap="RdYlGn")  # Use colormap for vegetation
    # plt.axis("off")
    # plt.show()

    print(f"Base URL: {config.sh_base_url}")
    print(f"Token URL: {config.sh_token_url}")




