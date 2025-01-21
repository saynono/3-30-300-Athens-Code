from collections import Counter
from qgis.core import QgsProject

# Load the layer
layerBuildings = QgsProject.instance().mapLayersByName("A300 -- Buildings")[0]
layerParks = QgsProject.instance().mapLayersByName("A300 - Parks & Forests")[0]

# Count buildings by park_osmid
building_counts = Counter()
building_counts_total = Counter()
buildings_total = 0

area_count = Counter()
area_total = 0

for feature in layerBuildings.getFeatures():
    park_osmid = int(feature['closest_park_osmid'])
    building_counts[park_osmid] += 1
    buildings_total += 1


# Step 2: Add a new field to the ParksLayer
layerParks.startEditing()
if 'buildings' not in [field.name() for field in layerParks.fields()]:
    layerParks.addAttribute(QgsField('buildings', QVariant.Int))
layerParks.updateFields()

if 'buildings_same_park' not in [field.name() for field in layerParks.fields()]:
    layerParks.addAttribute(QgsField('buildings_same_park', QVariant.Int))
layerParks.updateFields()

if 'buildings_percentage' not in [field.name() for field in layerParks.fields()]:
    layerParks.addAttribute(QgsField('buildings_percentage', QVariant.Double))
layerParks.updateFields()

if 'area_percentage' not in [field.name() for field in layerParks.fields()]:
    layerParks.addAttribute(QgsField('area_percentage', QVariant.Double))
layerParks.updateFields()

if 'area_ha_total' not in [field.name() for field in layerParks.fields()]:
    layerParks.addAttribute(QgsField('area_ha_total', QVariant.Double))
layerParks.updateFields()

print("--------------")
# Step 3: Update the 'buildings' field in ParksLayer
for feature in layerParks.getFeatures():
    park_osmid = feature['osmid_park']
    park_name = feature['name:el']
    count = building_counts.get(park_osmid, 0)
    feature['buildings'] = count
    layerParks.updateFeature(feature)
    building_counts_total[park_name] += count
    area_count[park_name] += feature['area_ha']
    area_total += feature['area_ha']
#    print(f"PARK osmid {park_name} [{park_osmid}]: {count} buildings    total+{building_counts_total[park_name]}")

for feature in layerParks.getFeatures():
    park_name = feature['name:el']
    count = building_counts_total.get(park_name, 0)
    area_ha_total = area_count.get(park_name,0)
    feature['buildings_same_park'] = count
    feature['buildings_percentage'] = (count/buildings_total)*100
    feature['area_ha_total'] = area_ha_total
    feature['area_percentage'] = area_ha_total/area_total*100
    
    layerParks.updateFeature(feature)
    print(f"PARK {park_name}: {count} buildings    total+{building_counts_total[park_name]}     area:{feature['area_ha_total']}")



for park, count in building_counts_total.items():
    print(f"park_osmid {park}: {count} buildings   {building_counts_total.get(park, 0)}")


# Step 4: Save the changes
layerParks.commitChanges()



