from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsProject, QgsFeature
from qgis.gui import QgsMapToolIdentifyFeature
import cv2
import os

# Create an action (button) to add to the toolbar
action = QAction("Display Panorama", iface.mainWindow())


# Define the function that will run when the button is clicked
def on_button_click():
    # Set up the identify tool to listen for feature clicks

    layer = iface.activeLayer()  # Use the active layer, or specify by name
    selected_features = layer.selectedFeatures()
    for feature in selected_features:
        pano_id = "0ccEvvnXuOZhboM8CdnFGA"
        pano_id = feature['panoID']
        image_path = f"/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/GSV-Data/panoramas-final-new/panorama_{pano_id}.jpg"
        image = cv2.imread(image_path)
        cv2.imshow(f"Pano Image for ID {pano_id}", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

# Connect the action to the on_button_click function
action.triggered.connect(on_button_click)

# Add the button to the QGIS toolbar
iface.addToolBarIcon(action)
