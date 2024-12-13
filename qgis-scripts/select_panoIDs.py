from qgis.core import QgsProject

# Specify the layer name
layer_name = "__Kypseli-All-GSV-Tree-Points-CROSSING-Lines — locations"
layer_name = "__Kypseli-All-GSV-Tree-Points-CROSSING-Trees — locations"
layer_name = "selected-trees"
#pano_id_value = "your_pano_id_value"  # Replace with your target panoID
layer = iface.activeLayer()  # Use the active layer, or specify by name
selected_features = layer.selectedFeatures()
pano_id = -1
pano_ids = []
for feature in selected_features:
    pano_id = feature['panoID']
    pano_ids.append(pano_id)


print(f"pano_id:{pano_id}   => {pano_ids}")
# Get the layer from the project
layer = QgsProject.instance().mapLayersByName(layer_name)[0]

if layer:
    
    pano_ids_str = ", ".join([f"'{pano_id}'" for pano_id in pano_ids]) 
    
    # Build the query expression
    expression = f'"panoID" IN ({pano_ids_str})'  # Adjust the field name and value as needed
    
    # Select features that match the expression
    layer.selectByExpression(expression)
    
    # Print the selected feature IDs (optional)
    selected_features = layer.selectedFeatures()
    print(f"Selected features: {[feature.id() for feature in selected_features]}")
else:
    print(f"Layer '{layer_name}' not found.")