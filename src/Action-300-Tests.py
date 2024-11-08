
import matplotlib.pyplot as plt

import geopandas as gpd
import osmnx as ox
# import osmnx.utils_geo
from pyproj import CRS
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import Point, LineString, Polygon
from shapely import wkt
import utils
import random
import math



if __name__ == "__main__":
    import os, os.path


    iteration_no = 3

    # move this to an external specs file
    # in hectares
    area_min_size = 1.0

    # in meters
    max_distance = 300

    root = '../3-30-300-Athens-Data/maps/Kypseli-All/'

    project_path = os.path.dirname(os.path.abspath(__file__))
    print("Project Path:", project_path)
    print("Root Path:", os.path.abspath(root))
    root = os.path.abspath(root)

    shape_file = "Kypseli-All.shp"

    root_generated = os.path.join(root, "generated/")
    shape_file_name = os.path.splitext(os.path.basename(shape_file))[0]
    shape_file_boundry = shape_file_name+"-Parks-Boundry-temp.shp"
    shape_file_park_forests = shape_file_name+"-Parks-Forests-All.gpkg"
    shape_file_park_forests_selected = shape_file_name+"-Parks-Forests-Selected.gpkg"
    shape_file_routes = shape_file_name+"-Routes.gpkg"
    shape_file_residential_buildings = shape_file_name+"-Residential-Buildings.gpkg"
    routes_list = shape_file_name+"-Routes.txt"
    graph_file = shape_file_name+"-Graph-Walking.graphml"

    inputShp = os.path.join(root, shape_file)
    outputGraphWalking = os.path.join(root_generated, graph_file)
    print(f"File {inputShp}")

    gdf_in = gpd.read_file(inputShp)

    if not os.path.exists(outputGraphWalking):
        print("Couldn't find graph file")
        exit()

        # graph = nx.read_gml(outputGraphWalking)
    graph = ox.load_graphml(outputGraphWalking)
    # graph = ox.save_graph_geopackage(outputGraphWalking)
    for u, v, key, data in graph.edges(data=True, keys=True):
        geom = data.get('geometry', None)  # Get the geometry object (e.g., LineString)
        if isinstance(geom, str):
            data['geometry'] = wkt.loads(geom)  # Convert the geometry to WKT (string format)
            # print('Convert please:', geom, data['geometry'])

    parks_and_forests_filtered = utils.get_parks_and_forests(gdf_in, area_min_size, max_distance)
    # parks_and_forests_filtered.to_file(outputParksForestsSelectedShp, driver="GPKG")
    parks_and_forests_filtered['park_nodes'] = parks_and_forests_filtered.apply(lambda row: [ox.nearest_nodes(graph, point[0], point[1]) for point in row.geometry.exterior.coords], axis=1)

    selected_park = parks_and_forests_filtered.sample(n=1)

    gdf_entries_near_park = utils.get_entry_points_to_park(graph, selected_park)


    # Plot the park boundary
    ax = selected_park.plot(color="green", edgecolor="black", figsize=(10, 10), alpha=0.5)

    # Plot the entry points on the same plot
    gdf_entries_near_park.plot(ax=ax, color="red", markersize=20, label="Entry Points")

    plt.legend()
    plt.title(f"Entry Points for park")
    plt.show()

