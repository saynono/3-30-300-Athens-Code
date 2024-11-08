import os
import pickle

import osmnx as ox
import geopandas as gpd
import streamlit as st

from directories import DATA_DIR#, STREET_NETWORKS, format_folder_name
from . import utils


@st.cache_data
def load_community_area_boundaries():
    """
    Load and clean the community area boundaries geojson file provided by
    the city of Chicago.
    """
    filepath = DATA_DIR / "Boundaries - Community Areas (current).geojson"
    gdf = gpd.read_file(filepath)

    # Data Types
    non_numeric_columns = ["community", "geometry"]
    float_columns = ["shape_area", "shape_len"]
    columns_to_drop = ["area_num_1"]
    for col in gdf.columns:
        if col not in non_numeric_columns:
            # All columns loaded as strings
            if col in float_columns:
                gdf[col] = gdf[col].astype(float)
            else:
                gdf[col] = gdf[col].astype(int)

            # Many columns are all Zero
            if all(gdf[col] == 0):
                columns_to_drop.append(col)

    gdf.drop(columns=columns_to_drop, inplace=True)

    # Renames & Index
    gdf.rename(columns={"area_numbe": "area_number"}, inplace=True)
    gdf.set_index("area_number", inplace=True)
    gdf.sort_index(inplace=True)

    # Clean
    gdf["community"] = gdf["community"].apply(lambda name: name.title())

    return gdf


def download_shapefile(gdf, community_name):
    """
    Use OSMNX to download the drivable street network within a single community
    area.
    """
    data_dir = utils.format_community_data_directory(community_name)
    shapefile_dir = data_dir / "street-network"
    shapefile_dir.mkdir(parents=True, exist_ok=True)
    graph_path = data_dir / "graph.pkl"

    if "edges.shp" not in os.listdir(shapefile_dir):
        gdf = gdf.set_index("community")
        multipolygon = gdf.loc[community_name].geometry
        graph = ox.graph_from_polygon(multipolygon, network_type="drive")

        # Spatial files must be the expected coordinate system that will align
        # with google street view images
        assert(graph.graph["crs"] == "epsg:4326")

        # Save graph
        utils.save_pickle_file(graph, graph_path)

        # Save to shapefile
        # OSMNX has marked this method and deprecated to move people away from
        # shapefiles, but shapefiles are what the src project accepts as
        # inputs, so we go with it.
        ox.save_graph_shapefile(graph, shapefile_dir)

    return graph_path, shapefile_dir