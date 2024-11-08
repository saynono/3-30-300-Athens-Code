import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
with warnings.catch_warnings():
    warnings.simplefilter(action='ignore', category=FutureWarning)

import requests
from OSMPythonTools.nominatim import Nominatim
from shapely.geometry import Point, LineString, Polygon
import osmnx as ox
# import osmnx.utils_graph
import osmnx.routing
import networkx as nx
from pyproj import CRS
import geopandas as gpd



def get_keys(key_file):
    lines = open(key_file,"r")
    keylist = []
    for line in lines:
        key = line[:-1]
        keylist.append(key)

    print('The key list is:=============', keylist)

    return keylist


def retrieveAddressFromLocationViaNomination(latitude, longitude):
    nominatim = Nominatim()
    # Perform reverse geocoding based on latitude and longitude
    location = nominatim.query('latitude=37.9836, longitude=23.7275')

    # Print the full address
    print("::::", type(location), location.toJSON())
    # Step 2: Use Nominatim to reverse geocode the coordinates
    # nominatim_url = f"https://nominatim.openstreetmap.org/details.php?format=json&lat={latitude}&lon={longitude}&zoom=18&addressdetails=1"
    # nominatim_url = f"https://nominatim.openstreetmap.org/reverse.php?lat={latitude}&lon={longitude}&zoom=18&format=jsonv2"
    #
    # # Make a request to the Nominatim API
    # # response = requests.get(nominatim_url)
    # response = requests.get(nominatim_url)
    # response.raise_for_status()
    # print(response.json())
    #
    # # Parse the JSON response
    # if response.status_code == 200:
    #     data = response.json()
    #     if 'address' in data:
    #         address = data['address']
    #         print(f"Address: {address}")
    #         return address
    #     else:
    #         print("No address found.")
    # else:
    #     print("Error contacting Nominatim.")
    #
    # return None

    # Step 2: Your Google Maps API key
    api_key = "AIzaSyDqAHRrEPkCKZdGX0owZtbzCdATlgqbkmE"  # Replace with your actual API key

    # Step 3: Build the request URL
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={api_key}"

    # Step 4: Make the request to Google Geocoding API
    response = requests.get(url)

    # Step 5: Parse the response JSON
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            # Get the first result (most relevant address)
            address = data['results'][0]['formatted_address']
            print(f"Address: {address}")
            print(f"Address Raw: {data}")
        else:
            print(f"Error: {data['status']}")
    else:
        print("Error contacting the Google API.")


def get_route_building_park(graph, building, park):

    # if building.geometry and building.geometry.centroid:
    # if building.geometry is not None:
    home_location = [building.geometry.centroid.x, building.geometry.centroid.y]
    # else:
    #     home_location = [float(building.centroid.x), float(building.centroid.y)]

    # print(building.centroid)
    # print(type(building.centroid))

    # print(home)
    # home_location = [23.735704, 37.999781]

    #park
    # park_location = [23.737078, 37.993286]
    # selected_park = parks_and_forests_filtered.sample(n=1)
    # selected_park = parks_and_forests_filtered.iloc[0]
    # print('selected_park\n', selected_park,selected_park.geometry.centroid)
    park_boundries = park.geometry
    park_location = [park.geometry.centroid.x, park.geometry.centroid.y]


    # print(f"HOME LOCATION = {home_location}")
    # print(f"PARK LOCATION = {park_location}")


    home_node = ox.nearest_nodes(graph, home_location[0], home_location[1])
    home_edge = ox.nearest_edges(graph, home_location[0], home_location[1])

    park_node = ox.nearest_nodes(graph, park_location[0], park_location[1])
    route = nx.shortest_path(graph, home_node, park_node, weight='length')
    # route = ox.routing.shortest_path(graph, home_node, park_node, weight='length')

    return route


def clip_route_to_park_boundries(graph, route, park):
    route_truncated = []
    for node in route:
        point = Point(graph.nodes[node]['x'], graph.nodes[node]['y'])
        route_truncated.append(node)
        if park.geometry.contains(point):  # Check if the node is inside the park
            break  # Stop the route here when the node is inside the park
    return route_truncated


def get_route_length (graph, route):
    # TODO: Add time to walk:
    # route_time = int(sum(ox.utils_graph.route_to_gdf(graph, route, "travel_time")["travel_time"]))

    # total_length = sum(ox.utils_graph.get_route_edge_attributes(graph, route, 'length'))
    total_length = int(sum(ox.routing.route_to_gdf(graph, route, weight="length")["length"]))
    # ox.distance.
    # ox.routing.route_to_gdf()
    # total_length = sum(ox.utils_graph.route_to_gdf(graph, route, 'length'))
    # route_gdf = ox.routing.route_to_gdf(graph, route, "length", attributes=True)
    # route2_length = int(sum(ox.utils_graph.route_to_gdf(G, route2, "length")["length"]))
    # total_length = route_gdf['length'].sum()
    return total_length

def get_parks_and_forests (shape_orginial, area_min_size, max_distance):
    # expand the shape file by the defined distance
    parks_boundry = expand_area(shape_orginial, max_distance)


    # Check for invalid geometries
    invalid_geometries = parks_boundry[~parks_boundry.is_valid]
    if not invalid_geometries.empty:
        print("Warning: The GeoDataFrame contains invalid geometries.")
    if parks_boundry.crs is None:
        parks_boundry.set_crs(epsg=4326, inplace=True)
    else:
        print(f"CRS is set to: {parks_boundry.crs}")

    # Save the new shapefile
    #     gdf_parks_boundry.to_file(outputShp)

    # Extract the boundary polygon from the GeoDataFrame
    boundary_polygon = parks_boundry.geometry.unary_union


    # Define the OSM tags to search for parks and forests
    tags = {'leisure': 'park', 'landuse': 'forest'}

    # Download parks and forests from OSM within the boundary polygon
    parks_and_forests = ox.features_from_polygon(boundary_polygon, tags)
    parks_and_forests = parks_and_forests.to_crs(epsg=3857)
    print(f"CRS parks_and_forests is set to: {parks_and_forests.crs}")

    # Step 3: Calculate the area in square meters
    parks_and_forests['area'] = parks_and_forests.geometry.area

    # Optional: Convert to square kilometers and hectares
    parks_and_forests['area_km2'] = parks_and_forests['area'] / 1_000_000
    parks_and_forests['area_ha'] = (parks_and_forests['area'] / 10_000)


    # # Step 4: Print the name and area for each shape (assuming 'Name' is the name column)
    # for index, row in parks_and_forests.iterrows():
    #     shape_name = row['name']  # Replace 'Name' with the actual column name for shape names
    #     # shape_name_en = row['name_en']
    #     shape_area = row['area_hectares']
    #     print(f"Shape: {shape_name}, Area: {shape_area} hectares")



    # Save the retrieved parks and forests to a new shapefile
    # parks_and_forests.to_file(outputParksForestsShp)

    # Filter the GeoDataFrame based on the area
    parks_and_forests_filtered = parks_and_forests[parks_and_forests['area_ha'] > area_min_size]
    return parks_and_forests_filtered


def expand_area(shapefile_in, expand_by):
    # Load the shapefile

    shapefile_out = shapefile_in
    # Reproject to EPSG:3857 if necessary (to ensure distance is in meters)
    if shapefile_out.crs.to_string() != "EPSG:3857":
        shapefile_out = shapefile_out.to_crs(epsg=3857)

    # Expand the geometries by 300 meters
    shapefile_out.geometry = shapefile_out.geometry.buffer(expand_by)
    # Ensure CRS is still valid after buffering
    shapefile_out.set_crs(epsg=3857, inplace=True)

    # Apply the function to get the UTM CRS
    # utm_crs = get_utm_crs(gdf_parks_boundry)
    utm_crs = CRS.from_string('epsg:4326')
    # Reproject the GeoDataFrame to the appropriate UTM CRS
    shapefile_out = shapefile_out.to_crs(utm_crs)


    # Check for invalid geometries
    shapefile_out['valid'] = shapefile_out.is_valid
    print(f"Number of invalid geometries: {len(shapefile_out[shapefile_out['valid'] == False])}")

    return shapefile_out



def get_entry_points_to_park (graph, gdf_park):
    # Define tags for paths, gates, and entrances
    tags = {
        "highway": ["footway", "path"],  # Footpaths
        "barrier": "gate",               # Gates
        "entrance": "yes"                # Entrances
    }

    # park_boundries = gdf_park.geometry
    # gdf_entries = ox.geometries_from_place(gdf_park, tags=tags)
    # Request geometries with the specified tags
    gdf_park = gdf_park.to_crs(epsg=4326)
    park_boundary = gdf_park.unary_union
    gdf_entries = ox.features_from_polygon(park_boundary, tags=tags)

    print(f"gdf_entries: {type(gdf_entries)}")
    print(f"gdf_park: {type(gdf_park)}")

    # Ensure both GeoDataFrames have the same CRS (Coordinate Reference System)
    # gdf_entries = gdf_entries.to_crs(gdf_park.crs)
    gdf_entries = gdf_entries.to_crs(epsg=4326)

    # Spatial join to get entry points within or intersecting the park boundary
    gdf_entries_near_park = gpd.sjoin(gdf_entries, gdf_park, how="inner", predicate="intersects")

    # Drop any duplicate columns from the join
    gdf_entries_near_park = gdf_entries_near_park.loc[:, ~gdf_entries_near_park.columns.duplicated()]

    # Get the boundary geometry (as a single merged geometry)
    boundary = gdf_park.unary_union  # This creates a single geometry of the park's boundary

    # Extract paths that intersect with the boundary
    crossing_paths = gdf_entries[gdf_entries.intersects(boundary)]

    print(f"crossing_paths: {type(crossing_paths)}")
    print(f"gdf_entries_near_park: {type(gdf_entries_near_park)}")

    # return crossing_paths
    return gdf_entries_near_park

