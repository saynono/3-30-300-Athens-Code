# The following film has been modified from its original version. It has been formatted to fit this screen.

# This program is used in the first step of the Treepedia project to get points along street 
# network to feed into GSV python scripts for metadata generation.
# Copyright(C) Ian Seiferling, Xiaojiang Li, Marwa Abdulhai, Senseable City Lab, MIT 
# First version July 21 2017

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import os
import fiona
import pyproj
from functools import partial
from fiona.crs import from_epsg
from shapely.ops import transform
from shapely.geometry import shape, mapping
from tqdm import tqdm
import osmnx as ox
import geopandas as gpd


from directories import STREET_NETWORKS, POINT_GRIDS, format_folder_name


# now run the python file: create_points.py, the input shapefile has to be in projection of WGS84, 4326
def create_points(inshp, outshp, mini_dist):
    
    '''
    This function will parse throigh the street network of provided city and
    clean all highways and create points every mini_dist meters (or as specified) along
    the linestrings
    Required modules: Fiona and Shapely

    parameters:
        inshp: the input linear shapefile, must be in WGS84 projection, ESPG: 4326
        output: the result point feature class
        mini_dist: the minimum distance between two created point

    last modified by Xiaojiang Li, MIT Senseable City Lab
    
    '''    
    count = 0
    s = {'trunk_link','tertiary','motorway','motorway_link','steps', None, ' ','pedestrian','primary', 'primary_link','footway','tertiary_link', 'trunk','secondary','secondary_link','tertiary_link','bridleway','service'}
    # somehow some streets in our case are marked as tertiary, primary (big ones) and service (dead ends). So I am removing them from this list.
    s = {'trunk_link','motorway','motorway_link','steps', None, ' ', 'primary_link','tertiary_link', 'trunk','secondary','secondary_link','tertiary_link','bridleway'}

    # the temporaray file of the cleaned data
    root = os.path.dirname(inshp)
    basename = 'clean_' + os.path.basename(inshp)
    temp_cleanedStreetmap = os.path.join(root,basename)
    
    # if the tempfile exist then delete it
    if os.path.exists(temp_cleanedStreetmap):
        fiona.remove(temp_cleanedStreetmap, 'ESRI Shapefile')
    
    # clean the original street maps by removing highways, if it the street map not from Open street data, users'd better to clean the data themselve
    with fiona.open(inshp) as source, fiona.open(temp_cleanedStreetmap, 'w', driver=source.driver, crs=source.crs,schema=source.schema) as dest:
        
        for feat in source:
            try:
                i = feat['properties']['highway'] # for the OSM street data
                if i in s:
                    continue
            except:
                # if the street map is not osm, do nothing. You'd better to clean the street map, if you don't want to map the GVI for highways
                key = dest.schema['properties'].keys()[0] # get the field of the input shapefile and duplicate the input feature
                i = feat['properties'][key]
                if i in s:
                    continue
            
            dest.write(feat)

    schema = {
        'geometry': 'Point',
        'properties': {'id': 'int'},
    }

    # Create points along the streets
    with fiona.drivers():
        #with fiona.open(outshp, 'w', 'ESRI Shapefile', crs=source.crs, schema) as output:
        with fiona.open(outshp, 'w', crs = from_epsg(4326), driver = 'ESRI Shapefile', schema = schema) as output:
            for line in tqdm(fiona.open(temp_cleanedStreetmap)):
                first = shape(line['geometry'])
                
                length = first.length
                
                try:
                    # convert degree to meter, in order to split by distance in meter
                    project = partial(pyproj.transform,pyproj.Proj(init='EPSG:4326'),pyproj.Proj(init='EPSG:3857')) #3857 is psudo WGS84 the unit is meter
                    
                    line2 = transform(project, first)
                    linestr = list(line2.coords)
                    dist = mini_dist #set
                    for distance in range(0,int(line2.length), dist):
                        point = line2.interpolate(distance)
                        
                        # convert the local projection back the the WGS84 and write to the output shp
                        project2 = partial(pyproj.transform,pyproj.Proj(init='EPSG:3857'),pyproj.Proj(init='EPSG:4326'))
                        point = transform(project2, point)
                        output.write({'geometry':mapping(point),'properties': {'id':1}})
                except:
                    print ("You should make sure the input shapefile is WGS84")
                    return
                    
    print("Process Complete")
    # delete the temprary cleaned shapefile
    fiona.remove(temp_cleanedStreetmap, 'ESRI Shapefile')


def save_street_network(inshp, outshp):
    # shapefile_path = "path/to/your/shapefile.shp"
    shape_gdf = gpd.read_file(inshp)

    # Ensure the shapefile is in the correct CRS (projected coordinate system)
    shape_gdf = shape_gdf.to_crs(epsg=4326)

    # Get the first geometry (polygon) from the shapefile (if there are multiple polygons, iterate as needed)
    polygon = shape_gdf.geometry[0]

    # Download the street network inside the polygon
    G = ox.graph_from_polygon(polygon, network_type='all')

    # Optionally, plot the street network
    ox.plot_graph(G)

    # Save the street network to a shapefile (if desired)
    ox.save_graph_shapefile(G, outshp)




# Note: make sure the input linear featureclass (shapefile) is in WGS 84 or ESPG: 4326
if __name__ == "__main__":

    import os,os.path

    root = '/Users/nono/Documents/workspaces/GIS/3-30-300-Athens-data/maps/Kypseli-All/'

    inshp = os.path.join(root,'Kypseli-All.shp')
    outshpStreetNetwork = os.path.join(root,'Kypseli-Center-Streets')
    outshpPoints = os.path.join(root,'Kypseli-Center-Streets-10m.shp')
    mini_dist = 10 #the minimum distance between two generated points in meter
    save_street_network(inshp, outshpStreetNetwork)
    shpStreetNetwork = os.path.join(root,'Kypseli-Center-Streets/edges.shp')
    create_points(shpStreetNetwork, outshpPoints, mini_dist)




