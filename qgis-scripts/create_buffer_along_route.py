from qgis.core import (
    QgsProject, 
    QgsVectorLayer, 
    QgsProcessingFeatureSourceDefinition,
    QgsProcessing,
    QgsApplication
)

import os

# Load LineString layer and OSM footway layer
layer_walk = "Walk-Activists-01"
line_layer = QgsProject.instance().mapLayersByName(f"{layer_walk}")[0]

for feature in line_layer.getFeatures():
    print(f"===> {feature.geometry()}")
    if not feature.geometry().isGeosValid():
        print(f"Invalid geometry detected: Feature ID {feature.id()}")
        
print(f" path okay: {os.path.exists(buffer_output)}")


osm_layer = QgsProject.instance().mapLayersByName("Kypseli-All-Graph-Edges — edges")[0]
print("\n\n", osm_layer)
# Buffer the LineString (optional)
buffer_output = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Code/temp/buffer.gpkg"
layer = processing.run("native:buffer", {
    'INPUT': line_layer,
    'DISTANCE': 0.01,  # Buffer distance in meters
    'SEGMENTS': 5,
    'DISSOLVE': False,
    'OUTPUT': 'memory:'
})

# Select walking paths intersecting the LineString
selected_output = f"/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Code/temp/{layer_walk}_buffer.gpkg"
processing.run("qgis:selectbylocation", {
    'INPUT': osm_layer,
    'PREDICATE': [0],  # Intersects
    'INTERSECT': selected_output,
    'METHOD': 0  # Replace selection
})

# Save the selected walking paths
processing.run("native:saveselectedfeatures", {
    'INPUT': osm_layer,
    'OUTPUT': selected_output
})

print(f"Walking path saved to {selected_output}")
