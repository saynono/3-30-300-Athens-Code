
import geopandas as gpd
import osmnx as ox
import osmnx.distance
import networkx as nx
from shapely.geometry import Point, LineString, MultiLineString
from shapely.ops import nearest_points
from shapely.ops import split
from shapely.strtree import STRtree
from scipy.spatial import KDTree

import osm_utils

def redo_road_map(G):
    # Create a list of all edges as LineStrings for nearest point calculations
    edge_lines = []
    for u, v, data in G.edges(data=True):
        point_u = Point((G.nodes[u]['x'], G.nodes[u]['y']))
        point_v = Point((G.nodes[v]['x'], G.nodes[v]['y']))
        edge_line = LineString([point_u, point_v])
        edge_lines.append(edge_line)



    road_multiline = MultiLineString(edge_lines)
    return road_multiline

def add_building_nodes_to_graph(G,buildings):
    # Extract node coordinates for KDTree
#    node_coords = [(data['x'], data['y']) for node, data in G.nodes(data=True)]
#    node_kdtree = KDTree(node_coords)

    total = len(buildings.count(1))
    for idx, building in buildings.iterrows():

        # road_multiline = redo_road_map()

        print(f"\n#{idx} / {total}    {(idx/total*100):.2f}%")
        building_geom = building.geometry

        # Skip invalid or empty geometries
        if building_geom.is_empty or not building_geom.is_valid:
            continue

        # Get the representative point (centroid)
        building_point = building_geom.representative_point()

        # nearest_edge = ox.distance.nearest_edges(G, building_point.x, building_point.y)
        u, v, key = ox.distance.nearest_edges(G, building_point.x, building_point.y, return_dist=False)
        # nearest_edge = LineString([(G.nodes[u]['x'], G.nodes[u]['y']), (G.nodes[v]['x'], G.nodes[v]['y'])])
        # edge_data = G[u][v]
        edge_data = G.get_edge_data(u,v)[0]
        print(edge_data)
        print(f"edge_data : {edge_data}")
        if 'geometry' in edge_data:
            is_two_point = False
            geom = edge_data['geometry']
        else:
            is_two_point = True
            geom = LineString([(G.nodes[u]['x'], G.nodes[u]['y']), (G.nodes[v]['x'], G.nodes[v]['y'])])
        # length_org = edge_data['length']
        # print(f"The nearest edge is between nodes {u} and {v}    => {length_org}")
        nearest_point_on_edge = geom.interpolate(geom.project(building_point))
        print(f"Nearest point on the edge: {nearest_point_on_edge}")

        print(f"U : {G.nodes[u]}      V : {G.nodes[v]}     ")

        # print(f"PU: {PU}    d1: {d_u}")
        # print(f"PV: {PV}    d2: {d_v}")
        # print(f"d_: {d_u+d_v}   vs   {length_org}")

        if is_two_point or True:
            PU = Point(G.nodes[u]['x'],G.nodes[u]['y'])
            PV = Point(G.nodes[v]['x'],G.nodes[v]['y'])
            l_u = nearest_point_on_edge.distance(PU)
            l_v = nearest_point_on_edge.distance(PV)
            split_u = LineString( [PU, Point(nearest_point_on_edge)] )
            split_v = LineString( [Point(nearest_point_on_edge), PV] )
        else:
            splitted = split(geom, nearest_point_on_edge)
            print(f"geom : {geom}   \n\n {nearest_point_on_edge}")
            print(f"splitted : {splitted.geoms}   \n\n {splitted}")
            if len(splitted.geoms)<=1:
                print(f"--- not splitted ---")
                continue
            # Add an edge between the new node and the nearest existing node
            # split_result = [geom for geom in split_result.geoms if isinstance(geom, LineString)]
            split_u = splitted.geoms[0]
            split_v = splitted.geoms[1]
            l_u = split_u.length
            l_v = split_v.length
            print(f"split_lines : {split_u}     {split_v}")

        G.remove_edge(u, v, key)

        # Add the new node to the graph
        new_node_id = max(G.nodes) + 1
        G.add_node(new_node_id, x=nearest_point_on_edge.x, y=nearest_point_on_edge.y)

        # Find the nearest existing node to connect
        # dist, idx = node_kdtree.query((nearest_point_on_edge.x, nearest_point_on_edge.y))
        # nearest_node = list(G.nodes())[idx]

        edge_attrs_u = {k: v for k, v in edge_data.items() if k != 'geometry'}
        edge_attrs_u['length'] = l_u
        edge_attrs_v = edge_attrs_u.copy()
        edge_attrs_v['length'] = l_v
        G.add_edge(new_node_id, u, geometry=split_u, attr=edge_attrs_u, length=l_u)
        G.add_edge(new_node_id, v,  geometry=split_v, attr=edge_attrs_v, length=l_v)

    return G

if __name__ == "__main__":
    import os, os.path

    root = '../../3-30-300-Athens-Data/maps/Kypseli-All/'
    shape_file = "Kypseli-All.shp"



    root_generated = os.path.join(root, "generated/")
    root_generated = os.path.abspath(root_generated)
    shape_file_name = os.path.splitext(os.path.basename(shape_file))[0]
    shape_file_residential_buildings_org = shape_file_name+"-Residential-Buildings-org.gpkg"
    graph_file = shape_file_name+"-Graph-Walking.graphml"
    graph_file_new = shape_file_name+"-Graph-Walking-extended.graphml"

    outputResidentialBuildingsOrgShp = os.path.join(root_generated, shape_file_residential_buildings_org)
    outputGraphWalking = os.path.join(root_generated, graph_file)
    outputGraphWalkingExtended = os.path.join(root_generated, graph_file_new)
    outputGraphWalkingExtendedUndirected = os.path.join(root_generated, shape_file_name+"-Graph-Walking-undirected.graphml")



    if os.path.exists(outputResidentialBuildingsOrgShp):
        buildings_gdf = gpd.read_file(outputResidentialBuildingsOrgShp)
    else:
        print("Exit Buildings -> ", outputResidentialBuildingsOrgShp)
        exit(0)


    if os.path.exists(outputGraphWalking):
        # graph = nx.read_gml(outputGraphWalking)
        G = ox.load_graphml(outputGraphWalking)
    else:
        print("Exit Graph")
        print("Exit Graph -> ", outputGraphWalking)
        exit(0)


    generate = False
    if generate:
        G_new = add_building_nodes_to_graph(G, buildings_gdf)
        ox.save_graphml(G_new, outputGraphWalkingExtended)
    else:
        G_new = ox.load_graphml(outputGraphWalkingExtended)
        # Check if the 'length' attribute exists in all edges
        G_new = osm_utils.test_graph(G_new)
        ox.save_graphml(G_new, outputGraphWalkingExtendedUndirected)


    import matplotlib.pyplot as plt
    # Plot the graph
    fig, ax = ox.plot_graph(G_new, node_size=5)
