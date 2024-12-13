# Define the specific panoID value you are searching for
target_pano_id = "Dr-EZ9xWZKcx5jzWfX7kQQ"  # Replace with the actual panoID value you're looking for

# Get the active layer
layer = iface.activeLayer()

# Check if the layer is valid
if layer:
    # Use a filter expression to search for the specific panoID
    expression = f'"panoID" = \'{target_pano_id}\''  # Adjust field name and value as necessary
    request = QgsFeatureRequest().setFilterExpression(expression)
    layer.selectByExpression(expression)
    # Search for the feature
    found_features = layer.getFeatures(request)
    for feature in found_features:
        # Print or work with the found feature
        print("Feature found:")
        print("panoID:", feature["panoID"])
        print("Attributes:", feature.attributes())
else:
    print("No active layer selected.")