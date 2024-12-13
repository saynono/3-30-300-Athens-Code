from qgis.core import QgsProject

layer = iface.activeLayer()  # Use the active layer, or specify by name

if layer:
    # Get the selected features
    selected_features = layer.selectedFeatures()

    # Check if any features are selected
    if selected_features:
        print(f"Number of selected features: {len(selected_features)}")
        
        # List all selected features with their attributes
        for feature in selected_features:
            print(f"Feature ID: {feature.id()}")
            print(f"Attributes: {feature.attributes()}")
            print(f"Geometry: {feature.geometry().asWkt()}")
            
        print("\n========================================\n")
        print(f" Selected Features Counted: {len(selected_features)}.")
    else:
        print("No features are selected.")
        
        
else:
    print(f"Layer '{layer_name}' not found.")
