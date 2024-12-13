
import pandas as pd
import geopandas as gpd
import osmnx as ox
# import osmnx.utils_geo
from pyproj import CRS
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import Point, LineString, Polygon, MultiPoint
from shapely import wkt
import utils
import random
import math
import sys
import select


def get_residential_buildings(shape_in):


    # Step 3: Get the boundary polygon from the shapefile
    boundary_polygon = shape_in.unary_union

    # Step 4: Query OSM for buildings within the boundary polygon
    # building_tags = {'building': True}  # 'True' gets all buildings
    building_tags = {'building': True, 'addr:housenumber': True}

    buildings = ox.features_from_polygon(boundary_polygon, tags=building_tags)

    # Step 5: Print and inspect the building data
    # print(buildings.head())

    return buildings



def get_walking_routes_to_parks(buildings_gdf, parks_gdf, graph, routes_file_list):

    parks_gdf = parks_gdf.to_crs(epsg=4326)
    buildings_gdf = buildings_gdf.to_crs(epsg=4326)


    if 'closest_park_name' not in buildings_gdf.columns:
        buildings_gdf['closest_park_name'] = None
    if 'closest_park_distance' not in buildings_gdf.columns:
        buildings_gdf['closest_park_distance'] = float('inf')
    if 'closest_park_dist' not in buildings_gdf.columns:
        buildings_gdf['closest_park_dist'] = float('inf')
    # if 'closest_park_node' not in buildings_gdf.columns:
    #     buildings_gdf['closest_park_node'] = None
    if 'closest_park_distance' not in buildings_gdf.columns:
        buildings_gdf['closest_park_distance'] = buildings_gdf['closest_park_distance'].astype(float)
    if 'closest_park_dist' not in buildings_gdf.columns:
        buildings_gdf['closest_park_dist'] = buildings_gdf['closest_park_dist'].astype(float)
    if 'closest_park_route_id' not in buildings_gdf.columns:
        buildings_gdf['closest_park_route_id'] = int(0)
    if 'closest_park_osmid' not in buildings_gdf.columns:
        buildings_gdf['closest_park_osmid'] = None

    if 'closest_park_iteration_no' not in buildings_gdf.columns:
        buildings_gdf['closest_park_iteration_no'] = int(0)




    # Step 7: Find the nearest park for each building
    routes = []
    # routes_data is for saving the LineString to export it later on
    routes_data = []

    # route = ox.shortest_path(G, orig, dest, weight="length")
    # fig, ax = ox.plot_graph_route(G, route, route_color="y", route_linewidth=6, node_size=0)

    cnt = 0

    with open(routes_file_list, 'a') as file:


        for idx, building in buildings_gdf.iterrows():

            # building_centroid = building.geometry.centroid
            print(f"Building #{cnt} {idx} / osmid:{building['osmid']}   iteration_no:{iteration_no}")

            if building['closest_park_iteration_no'] == iteration_no:
            # if not math.isinf(building['closest_park_route_id']):
                print(f"Closest Park Value is already set to {building['closest_park_distance']}")
            # TODO add again... for now  always the first 10
                continue

            closest_area = None
            closest_area_id = 0
            closest_node = None
            closest_route = None
            walking_distance_min = float('inf')

            for idx2, park_area in parks_gdf.iterrows():

                try:
                    walking_route = utils.get_route_building_park(graph, building, park_area)
                    walking_route = utils.clip_route_to_park_boundries(graph, walking_route, park_area)
                    walking_distance = utils.get_route_length(graph, walking_route)
                    # print(f"park_area   idx = {idx2[1]}")

                    # Keep track of the closest area
                    if walking_distance < walking_distance_min:
                        walking_distance_min = walking_distance
                        closest_area = park_area
                        #TODO : this seems hacked... need to retrieve the osmid in the correct way
                        closest_area_id = idx2[1]
                        # closest_node = park_node
                        closest_route = walking_route

                except nx.NetworkXNoPath:
                    print(f"No walking path to area {idx2}")

            buildings_gdf.at[idx, 'closest_park_name'] = closest_area['name']
            buildings_gdf.at[idx, 'closest_park_distance'] = walking_distance_min
            buildings_gdf.at[idx, 'closest_park_dist'] = round(walking_distance_min)
            buildings_gdf.at[idx, 'closest_park_osmid'] = closest_area_id
            buildings_gdf.at[idx, 'closest_park_iteration_no'] = iteration_no


            # print(f"closest_area: {closest_area}")


            # Calculate the shortest route between the building and the nearest park
            try:
                # route = nx.shortest_path(graph, building_point_node, closest_node, weight='length')
                route = closest_route
                print(f"     Distance to area {closest_area['name']}: {walking_distance_min:.2f} meters")
                # print(f"     From [{building_centroid.y:.6f}, {building_centroid.x:.6f}] to [{graph.nodes[closest_node]['y']:.6f}, {graph.nodes[closest_node]['x']:.6f}]")
                # print('route',route)
                # route_length = sum(ox.utils_graph.get_route_edge_attributes(graph, route, 'length'))
                # Convert the route (list of nodes) to a LineString

                route_coords = [(graph.nodes[node]['x'], graph.nodes[node]['y']) for node in route]
                if len(route_coords) > 1 :
                    route_line = LineString(route_coords)
                    print("Adding route...", idx)
                    # Store the route as a dictionary for later conversion to GeoDataFrame
                    routes_data.append({'route_id': idx, 'geometry': route_line})

                routes.append({'route_id': idx, 'route': route})
                nodes_str = ", ".join(map(str, route))
                line = f"{idx}, {building['osmid']}, [{nodes_str}]\n"
                buildings_gdf.at[idx, 'closest_park_route_id'] = idx
                print(f"{line}")
                file.write(line)
                
            except nx.NetworkXNoPath:
                print(f"No path found for building {idx}")
                routes.append(None)

            cnt += 1
            if cnt >= 5:
                break




# Create a GeoDataFrame to hold the route
    gdf_routes = gpd.GeoDataFrame(routes_data, crs="EPSG:4326")

    return gdf_routes, buildings_gdf, routes
    # return buildings_gdf



def get_walking_routes_to_parks_nodes(buildings_gdf, parks_nodes, graph, routes_file_list):

    buildings_gdf = buildings_gdf.to_crs(epsg=4326)


    if 'closest_park_name' not in buildings_gdf.columns:
        buildings_gdf['closest_park_name'] = None
    if 'closest_park_distance' not in buildings_gdf.columns:
        buildings_gdf['closest_park_distance'] = float('inf')
    if 'closest_park_dist' not in buildings_gdf.columns:
        buildings_gdf['closest_park_dist'] = float('inf')
    # if 'closest_park_node' not in buildings_gdf.columns:
    #     buildings_gdf['closest_park_node'] = None
    if 'closest_park_distance' not in buildings_gdf.columns:
        buildings_gdf['closest_park_distance'] = buildings_gdf['closest_park_distance'].astype(float)
    if 'closest_park_dist' not in buildings_gdf.columns:
        buildings_gdf['closest_park_dist'] = buildings_gdf['closest_park_dist'].astype(float)
    if 'closest_park_route_id' not in buildings_gdf.columns:
        buildings_gdf['closest_park_route_id'] = int(0)
    if 'closest_park_osmid' not in buildings_gdf.columns:
        buildings_gdf['closest_park_osmid'] = None

    if 'closest_park_iteration_no' not in buildings_gdf.columns:
        buildings_gdf['closest_park_iteration_no'] = int(0)




    # Step 7: Find the nearest park for each building
    routes = []
    # routes_data is for saving the LineString to export it later on
    routes_data = []

    # route = ox.shortest_path(G, orig, dest, weight="length")
    # fig, ax = ox.plot_graph_route(G, route, route_color="y", route_linewidth=6, node_size=0)

    cnt = 0
    iterations_per_round = 5

    with open(routes_file_list, 'a') as file:

        print(f"buildings_gdf : osmid column: {buildings_gdf.columns}")

        for idx, building in buildings_gdf.iterrows():

            # building_centroid = building.geometry.centroid
            print(f"Building #{cnt} {idx} / osmid:{building['osmid']}   iteration_no:{iteration_no}")

            if building['closest_park_iteration_no'] == iteration_no:
                # if not math.isinf(building['closest_park_route_id']):
                print(f"Closest Park Value is already set to {building['closest_park_distance']}")
                # TODO add again... for now  always the first 10
                continue

            closest_area = None
            closest_area_id = 0
            closest_node = None
            closest_route = None
            walking_distance_min = float('inf')

            for park_nodes in parks_nodes:

                park_nodes = park_nodes.to_crs(epsg=4326)

                try:
                    walking_route = utils.get_route_building_park_nodes(graph, building, park_nodes)
                    # walking_route = utils.clip_route_to_park_boundries(graph, walking_route, park_nodes)
                    walking_distance = utils.get_route_length(graph, walking_route)
                    # print(f"park_area   idx = {idx2[1]}")

                    # Keep track of the closest area
                    if walking_distance < walking_distance_min:
                        walking_distance_min = walking_distance
                        closest_area = park_nodes
                        #TODO : this seems hacked... need to retrieve the osmid in the correct way
                        closest_area_id = park_nodes['osmid_park']
                        # closest_node = park_node
                        closest_route = walking_route

                except nx.NetworkXNoPath:
                    print(f"No walking path to area {park_nodes.name}")

            buildings_gdf.at[idx, 'closest_park_name'] = closest_area['name']
            buildings_gdf.at[idx, 'closest_park_distance'] = walking_distance_min
            buildings_gdf.at[idx, 'closest_park_dist'] = round(walking_distance_min)
            buildings_gdf.at[idx, 'closest_park_osmid'] = closest_area_id
            buildings_gdf.at[idx, 'closest_park_iteration_no'] = iteration_no


            # print(f"closest_area: {closest_area}")


            # Calculate the shortest route between the building and the nearest park
            try:
                # route = nx.shortest_path(graph, building_point_node, closest_node, weight='length')
                route = closest_route
                print(f"     Distance to area {closest_area['name']}: {walking_distance_min:.2f} meters")
                # print(f"     From [{building_centroid.y:.6f}, {building_centroid.x:.6f}] to [{graph.nodes[closest_node]['y']:.6f}, {graph.nodes[closest_node]['x']:.6f}]")
                # print('route',route)
                # route_length = sum(ox.utils_graph.get_route_edge_attributes(graph, route, 'length'))
                # Convert the route (list of nodes) to a LineString

                route_coords = [(graph.nodes[node]['x'], graph.nodes[node]['y']) for node in route]
                if len(route_coords) > 1 :
                    route_line = LineString(route_coords)
                    print("Adding route...", idx)
                    # Store the route as a dictionary for later conversion to GeoDataFrame
                    routes_data.append({'route_id': idx, 'geometry': route_line, 'closest_park_iteration_no':iteration_no})

                routes.append({'route_id': idx, 'route': route})
                nodes_str = ", ".join(map(str, route))
                line = f"{idx}, {building['osmid']}, [{nodes_str}]\n"
                buildings_gdf.at[idx, 'closest_park_route_id'] = idx
                print(f"{line}")
                file.write(line)

            except nx.NetworkXNoPath:
                print(f"No path found for building {idx}")
                routes.append(None)

            cnt += 1
            if cnt >= iterations_per_round:
                break

    done = cnt < iterations_per_round


    # Create a GeoDataFrame to hold the route
    if len(routes_data) > 0:
        gdf_routes = gpd.GeoDataFrame(routes_data, crs="EPSG:4326")
    else:
        gdf_routes = gpd.GeoDataFrame()

    return gdf_routes, buildings_gdf, routes, done
    # return buildings_gdf



def get_address_for_building(buildings, building_osmid):
    # buildings = ox.features_from_place('Κυψέλη, Αθήνα, Greece', tags={'building': True})
    building = buildings[buildings.osmid == building_osmid]
    # If the building exists, get its geometry
    if not building.empty:
        geometry = building.geometry.values[0]
        centroid = geometry.centroid  # Get the centroid of the building for reverse geocoding
        latitude = centroid.y
        longitude = centroid.x
        address = utils.retrieveAddressFromLocationViaNomination(latitude,longitude)
        print(f"Building OSMID: {building_osmid}, Centroid Coordinates: Latitude = {latitude}, Longitude = {longitude}")
    else:
        print("Building with the given OSMID not found.")


def temp_distance_test(graph, home, selected_park) :
    print('-------------------------------------------------------')
    print(home)
    print(selected_park)

    route = utils.get_route_building_park(graph, home, selected_park)
    print('-------------------------------------------------------')

    # home_location = [float(home.centroid.x), float(home.centroid.y)]
    # print(home.centroid)
    # print(type(home.centroid))
    #
    # # print(home)
    # # home_location = [23.735704, 37.999781]
    #
    # #park
    # # park_location = [23.737078, 37.993286]
    # # selected_park = parks_and_forests_filtered.sample(n=1)
    #
    # # print('selected_park\n', selected_park,selected_park.geometry.centroid)
    # park_boundries = selected_park.geometry
    # park_location = [selected_park.geometry.centroid.x, selected_park.geometry.centroid.y]
    #
    #
    # print(f"PARK CRS is set to: {parks_and_forests_filtered.crs}")
    # print(f"BUILDINGS CRS is set to: {buildings.crs}")
    # print(f"HOME LOCATION = {home_location}")
    # print(f"PARK LOCATION = {park_location}")
    #
    #
    # home_node = ox.nearest_nodes(graph,home_location[0], home_location[1])
    # home_edge = ox.nearest_edges(graph,home_location[0], home_location[1])
    #
    # park_node = ox.nearest_nodes(graph,park_location[0], park_location[1])
    #
    # route = nx.shortest_path(graph, home_node, park_node, weight='length')

    route_truncated = utils.clip_route_to_park_boundries(graph, route, selected_park)
    route_length = sum(ox.utils_graph.get_route_edge_attributes(graph, route_truncated, 'length'))

    print('route_length', route_length)

    # route_truncated = []
    # for node in route:
    #     point = Point(graph.nodes[node]['x'], graph.nodes[node]['y'])
    #     route_truncated.append(node)
    #     if park_boundries.contains(point):  # Check if the node is inside the park
    #         break  # Stop the route here when the node is inside the park

    # route_length = sum(ox.utils_graph.get_route_edge_attributes(graph, route_truncated, 'length'))
    # print('route_length', route_length)
    fig, ax = ox.plot_graph(graph, show=False, close=False)

    buildings.plot(column='distance_park_display', cmap='viridis', legend=True, edgecolor='black', ax=ax)

    ox.plot_graph_route(graph,route,ax=ax, show=False, close=False)
    ox.plot_graph_route(graph,route_truncated,ax=ax, color='lightgreen', route_linewidth=2, node_size=0, bgcolor='g', show=False, close=False)

    selected_park_gdf = gpd.GeoDataFrame([selected_park], geometry='geometry')
    selected_park_gdf.plot(ax=ax, color='blue', alpha=0.5, edgecolor='black')

    # ax.scatter(home_location[0], home_location[1], color='orange', label='HOME', s=8)
    # ax.scatter(graph.nodes[home_node]['x'], graph.nodes[home_node]['y'], color='red', label='HOME-Node', s=8)
    # # plt.scatter(graph.nodes[home_edge]['y'], graph.nodes[home_edge]['x'], color='yellow', label='HOME-Edge', s=8)  # 's' controls the size of the point
    # ax.scatter(graph.nodes[park_node]['x'], graph.nodes[park_node]['y'], color='lightgreen', label='PARK-Node', s=10)
    # ax.scatter(park_location[0], park_location[1], color='green', label=f"PARK {selected_park['name']}", s=10)


    # Customize the plot (optional)
    plt.title(f"Walking Distance to nearest Park in Kypseli ({selected_park['name']}) => {route_length:.0} meters")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid(True)

    # Show the plot
    plt.show()

    # get_address_for_building(buildings, 489737943)

    # # Step 8: Plot or save the results
    # import matplotlib.pyplot as plt
    # fig, ax = plt.subplots()
    # ox.plot_graph(graph, ax=ax)
    #
    #
    # # Plot the buildings
    # buildings.plot(ax=ax, color='blue', alpha=0.5, markersize=5)
    #
    # # Plot the parks
    # parks_and_forests_filtered.plot(ax=ax, color='green', alpha=0.7, markersize=5)
    #
    # routes.plot(ax=ax, color='yellow', alpha=0.7, markersize=5)
    #
    # plt.show()

def get_park_edge_intersection(park, edges):
    # Check each edge
    edges_metric = edges.to_crs(epsg=4326)
    # park_metric = park.to_crs(epsg=4326)
    polygon = park.geometry
    partial_edges = []
    for idx, edge in edges_metric.iterrows():
        if not edge.geometry.within(polygon):
            intersection = edge.geometry.intersection(polygon)
            # Check if part of the edge is outside
            # if not edge.equals(intersection):
            partial_edges.append(intersection)
            print(f"Found intersection: {edge['osmid']}  {type(edge.geometry)}   => {len(edge.geometry.coords)}                {intersection}")

    points_outside = []
    polygon = polygon.buffer(-.000001)
    for geom in partial_edges:
        if geom.geom_type == 'LineString':
            # Extract points from LineString
            for coord in geom.coords:
                point = Point(coord)
                if not polygon.contains(point):  # Check if the point is outside the polygon
                    points_outside.append(point)
        elif geom.geom_type == 'MultiLineString':
            # Extract points from each LineString in the MultiLineString
            for line in geom.geoms:
                for coord in line.coords:
                    point = Point(coord)
                    if not polygon.contains(point):  # Check if the point is outside the polygon
                        points_outside.append(point)

    return points_outside

def get_all_park_boundary_nodes(parks_gdf, nodes_gdf, edges_gdf):
    # Initialize a dictionary to store results
    park_boundary_nodes = {}
    parks_metric = parks_gdf.to_crs(epsg=4326)
    edges_metric = edges_gdf.to_crs(epsg=4326)
    # Iterate over each park
    for idx, park in parks_metric.iterrows():
        # Get the park boundary as a LineString or MultiLineString
        # boundary = park['geometry'].boundary
        boundary = park.geometry#.unary_union


        # get_park_edge_intersection(park, edges_metric)

        # Find all nodes that intersect with the boundary
        boundary_nodes = edges_gdf[edges_metric.intersects(boundary)]

        if not boundary_nodes.empty:
            nodes = get_park_edge_intersection(park, boundary_nodes)
            if len(nodes) > 0:
                partial_edges_gdf = gpd.GeoDataFrame({'geometry': nodes}, crs="EPSG:4326")
                park_boundary_nodes[idx] = partial_edges_gdf
            else:
                print("bah")
        else:
            if boundary.geom_type == "LineString":
                # points = MultiPoint(boundary.coords)
                points = boundary.coords
            elif boundary.geom_type == "MultiLineString":
                points = []
                for line in boundary.geoms:
                    # print(type(line.coords),line.coords)
                    points += line.coords
                # points = MultiPoint(points)
            elif boundary.geom_type == "Polygon":
                # points = MultiPoint(boundary.exterior.coords)
                points = []
                for p in boundary.exterior.coords:
                    p = Point(p)
                    # print(type(p),p)
                    points.append(p)
                # print(points)
                # points = boundary.exterior.coords
            else:
                points = [Point()]  # Empty geometry as a fallback

            # Convert points to GeoDataFrame
            # fallback_gdf = gpd.GeoDataFrame(geometry=[points], crs=parks_metric.crs)
            partial_edges_gdf = gpd.GeoDataFrame({'geometry': points}, crs="EPSG:4326")
            park_boundary_nodes[idx] = partial_edges_gdf

        attributes = park.drop('geometry').drop('nodes').drop('ways').to_dict()
        # Step 3: Assign the attributes to all rows in points_gdf
        for key, value in attributes.items():
            partial_edges_gdf[key] = value


    # Combine results into a single GeoDataFrame (optional)
    results_gdfs = [gdf for gdf in park_boundary_nodes.values()]
    return results_gdfs
    # all_boundary_nodes_gdf = gpd.GeoDataFrame(pd.concat(results_gdfs, ignore_index=True))
    # # parks_metric = parks_gdf.to_crs(epsg=4326)
    # return all_boundary_nodes_gdf



if __name__ == "__main__":
    import os, os.path


    iteration_no = 9

    # move this to an external specs file
    # in hectares
    area_min_size = 1.0

    # in meters
    max_distance = 300

    root = '../3-30-300-Athens-Data/maps/Kypseli-All/'
    shape_file = "Kypseli-All.shp"


    root = os.path.abspath(root)
    root_generated = os.path.join(root, "generated/")
    shape_file_name = os.path.splitext(os.path.basename(shape_file))[0]
    shape_file_boundry = shape_file_name+"-Parks-Boundry-temp.shp"
    shape_file_park_forests = shape_file_name+"-Parks-Forests-All.gpkg"
    shape_file_park_forests_selected = shape_file_name+"-Parks-Forests-Selected.gpkg"
    shape_file_routes = shape_file_name+"-Routes-A300.gpkg"
    shape_file_residential_buildings = shape_file_name+"-Residential-Buildings.gpkg"
    shape_file_residential_buildings_org = shape_file_name+"-Residential-Buildings-org.gpkg"
    shape_file_residential_buildings_A300 = shape_file_name+"-Residential-Buildings-A300.gpkg"
    routes_list = shape_file_name+"-Routes.txt"

    graph_file = shape_file_name+"-Graph-Walking.graphml"
    # graph_file = shape_file_name+"-Graph-Walking-extended.graphml"
    # graph_file = shape_file_name+"-Graph-Walking-undirected.graphml"
    csv_file_residential_buildings = shape_file_name+"-Residential-Buildings.csv"

    os.makedirs(root_generated, exist_ok=True)

    inputShp = os.path.join(root, shape_file)
    outputShp = os.path.join(root_generated, shape_file_boundry)
    outputParksForestsShp = os.path.join(root_generated, shape_file_park_forests)
    outputParksForestsSelectedShp = os.path.join(root_generated, shape_file_park_forests_selected)
    outputResidentialBuildingsShp = os.path.join(root_generated, shape_file_residential_buildings)
    outputResidentialBuildingsA300Shp = os.path.join(root_generated, shape_file_residential_buildings_A300)
    outputResidentialBuildingsOrgShp = os.path.join(root_generated, shape_file_residential_buildings_org)

    outputResidentialBuildingsCsv = os.path.join(root_generated, csv_file_residential_buildings)
    outputGraphWalking = os.path.join(root_generated, graph_file)
    outputRoutesShp = os.path.join(root_generated, shape_file_routes)
    routes_list = os.path.join(root_generated, routes_list)

    gdf_in = gpd.read_file(inputShp)


# print("Columns parks_and_forests_filtered",parks_and_forests_filtered.columns)

    # gdf_in.plot()
    # parks_and_forests_filtered.plot()
    # plt.show()


    # Step 3: Query OSM for park entrances using highway=entrance or barrier=gate
    # OSM uses 'highway=entrance' and 'barrier=gate' to define park/forest entrances
    # entrance_tags = {'highway': 'entrance', 'barrier': 'gate'}
    # gdf_entrances = ox.features_from_place("Pedion Areos", entrance_tags)
    # print(gdf_entrances)


    # if( outputResidentialBuildingsShp)
    if os.path.exists(outputResidentialBuildingsShp):
        buildings = gpd.read_file(outputResidentialBuildingsShp)
    else:
        buildings = get_residential_buildings(gdf_in)
        buildings = buildings[~(buildings.geometry.geom_type == 'Point')]
        buildings = buildings[~(buildings.geometry.geom_type == 'LineString')]
        if 'closest_park_iteration_no' not in buildings.columns:
            buildings['closest_park_iteration_no'] = int(0)

        buildings.to_file(outputResidentialBuildingsShp, driver="GPKG")  # Save as shapefile
        buildings.to_file(outputResidentialBuildingsOrgShp, driver="GPKG")  # Save as shapefile


    # print(buildings)
    # # Step 6: Save the building geometries to a new shapefile or a CSV file
    # buildings[['name', 'building','addr:housenumber']].to_csv(outputResidentialBuildingsCsv, index=true)  # Save attributes to CSV

    if os.path.exists(outputGraphWalking):
        # graph = nx.read_gml(outputGraphWalking)
        graph = ox.load_graphml(outputGraphWalking)
        # graph = ox.save_graph_geopackage(outputGraphWalking)
        for u, v, key, data in graph.edges(data=True, keys=True):
            geom = data.get('geometry', None)  # Get the geometry object (e.g., LineString)
            if isinstance(geom, str):
                data['geometry'] = wkt.loads(geom)  # Convert the geometry to WKT (string format)
                # print('Convert please:', geom, data['geometry'])
    else:
        graph_shape_boundry = utils.expand_area(gdf_in, max_distance)
        graph_boundry = graph_shape_boundry.unary_union
        graph = ox.graph_from_polygon(graph_boundry, network_type='walk')

        # latitude = 37.9838
        # longitude = 23.7275
        # graph = ox.graph_from_point((latitude, longitude), dist=5000, network_type='walk')
        # Converting Graph to Shapes
        nodes, edges = ox.graph_to_gdfs(graph)
        # Save nodes for QGIS
        nodes.to_file(os.path.join(root_generated, shape_file_name+"-Graph-Nodes.gpkg"), layer='nodes', driver="GPKG")
        # Save edges for QGIS
        edges.to_file(os.path.join(root_generated, shape_file_name+"-Graph-Edges.gpkg"), layer='edges', driver="GPKG")

        # Step 2: Convert geometries (like LineString) to WKT format for each edge
        # for u, v, key, data in graph.edges(data=True, keys=True):
        #     geom = data.get('geometry', None)  # Get the geometry object (e.g., LineString)
        #     if isinstance(geom, LineString):
        #         data['geometry'] = geom.wkt  # Convert the geometry to WKT (string format)

        # nx.write_gml(graph, outputGraphWalking)
        # ox.save_graph_geopackage(graph, filepath=outputGraphWalking)
        ox.save_graphml(graph, outputGraphWalking)

    # ox.plot_graph(graph)

    parks_and_forests_filtered = utils.get_parks_and_forests(gdf_in, area_min_size, max_distance)
    parks_and_forests_filtered.to_file(outputParksForestsSelectedShp, driver="GPKG")
    # parks_and_forests_filtered['park_nodes'] = parks_and_forests_filtered.apply(lambda row: [ox.nearest_nodes(graph, point[0], point[1]) for point in row.geometry.exterior.coords], axis=1)







    # Convert graph to GeoDataFrame
    nodes_gdf, edges_gdf = ox.graph_to_gdfs(graph)
    all_park_nodes = get_all_park_boundary_nodes(parks_and_forests_filtered, nodes_gdf, edges_gdf)
    all_park_nodes_gdf = gpd.GeoDataFrame(pd.concat(all_park_nodes, ignore_index=True))

    parks_metric = parks_and_forests_filtered.to_crs(epsg=4326)
    parks_metric.plot(color='green', alpha=0.5, edgecolor='black')

    # Plot boundary nodes
    if not all_park_nodes_gdf.empty:
        # print(all_park_nodes_gdf)
        all_park_nodes_gdf.set_crs(epsg=4326, inplace=True)
        # all_park_nodes_gdf.plot(color='red', markersize=10, ax=plt.gca())
        outputAllParkNodes = os.path.join(root_generated, "temp/PARK_NODES_ALL.gpkg")
        # print(outputAllParkNodes)
        all_park_nodes_gdf.to_file(outputAllParkNodes, driver="GPKG")
    #
    # plt.title("Boundary Nodes of Parks")
    # plt.show()



    # do_routes = False
    do_routes = True
    # do_routes = False
    if do_routes:

        # parks_gdf = parks_gdf.to_crs(epsg=4326)
        # buildings_gdf = buildings_gdf.to_crs(epsg=4326)
        buildings_total = len(buildings)
        print(f"Buildings Total: {buildings_total}")
        # if closest_park_iteration_no

        if os.path.exists(outputRoutesShp):
            routes_gdf = gpd.read_file(outputRoutesShp)
            if ('closest_park_iteration_no' not in buildings.columns or
                    'closest_park_iteration_no' not in routes_gdf.columns or
                    routes_gdf.loc[0]['closest_park_iteration_no'] != iteration_no):
        #
        # print(f"Route Iteraction {routes_gdf.loc[0]['closest_park_iteration_no']} vs current iteration = {iteration_no}")
        #     if routes_gdf.loc[0]['closest_park_iteration_no'] != iteration_no:
                routes_gdf = gpd.GeoDataFrame()
        else:
            routes_gdf = gpd.GeoDataFrame()

        if routes_gdf.empty:
            print("Creating a new Routes GDF.")
        else:
            print("Adding to existing Routes GDF.")


        # print(f"routes_gdf ::: {routes_gdf.empty}")
        # exit(0)

        finished = False
        while not finished:
            # routes_part_gdf, buildings, routes_obj = get_walking_routes_to_parks(buildings, parks_and_forests_filtered, graph, routes_list)
            routes_part_gdf, buildings, routes_obj, finished = get_walking_routes_to_parks_nodes(buildings, all_park_nodes, graph, routes_list)


            if routes_gdf.empty:
                routes_gdf = routes_part_gdf
            else:
                # routes_gdf = routes_gdf.merge(routes_part_gdf)
                routes_gdf = gpd.GeoDataFrame(pd.concat([routes_gdf, routes_part_gdf], ignore_index=True))
            if not routes_gdf.empty:
                routes_gdf.to_file(outputRoutesShp, driver="GPKG")  # Save as shapefile
                buildings.to_file(outputResidentialBuildingsShp, driver="GPKG")  # Save as shapefile
                buildings.to_file(outputResidentialBuildingsA300Shp, driver="GPKG")  # Save as shapefile

            print("added routes and saved buildings")
            # finished = True

        # with open(routes_list, 'w') as file:
        #     for obj in routes_obj:
        #         nodes = ", ".join(map(str, obj['route']))
        #         line = f"{obj['route_id']}, [{nodes}]\n"
        #         print(f"{line}")
        #         file.write(line)
        print(f"Objects saved to {routes_list}")


# ox.plot_footprints(buildings, bgcolor='white', color='lightblue', show=True, close=True)

    #
    # buildings['distance_park_display'] = [random.uniform(10, 100) for _ in range(len(buildings))]  # Random height between 10 and 100
    #
    #
    # # plt.show()
    #
    # # Step 3: Plot the buildings using a color map based on the 'height' field
    # # 'cmap' defines the color map and 'column' defines which column to use for coloring
    # # buildings_without_points = [geom for geom in buildings if geom.geom_type != 'Point']
    # # buildings_without_points = buildings[~(buildings.geometry.geom_type == 'Point')]
    # buildings = buildings.to_crs(epsg=4326)
    #
    # parks_and_forests_filtered = parks_and_forests_filtered.to_crs(epsg=4326)
    #
    # #home
    # # home = buildings.iloc[0]
    # home = buildings.sample(n=1)
    # selected_park = parks_and_forests_filtered.iloc[0]
    # # temp_distance_test(graph, home, selected_park)
