
import csv
layer = iface.activeLayer()  # Use the active layer, or specify by name
selected_features = layer.selectedFeatures()
# Prepare the CSV file
file_name = "selected_pano_ids_crossing"
with open(f"/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/{file_name}.txt", 'w', newline='') as file:
    # Iterate over selected features and write panoID values
    for feature in selected_features:
        line = f"panoID: {feature['panoID']} panoDate: {feature['panoDate']} longitude: {feature['longitude']} latitude: {feature['latitude']}\n"
        print(f"selected {feature['panoID']} => {line}")
        file.write(line)
print("Export completed.")