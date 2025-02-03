layer = QgsProject.instance().mapLayersByName("A300 -- Buildings")[0]
layer.startEditing()

# Extract label data from the styling
labels = {}
colours = {}
renderer = layer.renderer()

if 'park_color' not in [field.name() for field in layer.fields()]:
    layer.addAttribute(QgsField('park_color', QVariant.String))
layer.updateFields()


# Loop through the categorized renderer symbols and collect label information
if renderer.type() == "categorizedSymbol":
    categories = renderer.categories()
    for category in categories:
        
        print(f"category.value() : {type(category.value())} ===> {category.value()}")
        try:
            value = int(category.value())  # The osmid value used in styling
            colour = category.symbol().color().name() 
            label = category.label()  # The name from the styling
            labels[value] = label  # Map osmid to label
            colours[value] = colour  # Map osmid to label
            print(f"label {label}   => {value} {type(value)}   /   {colour}        => {labels[value]}")
        except:
            print('end')
# Update the 'name_el' field with the label for the same osmid
for feature in layer.getFeatures():
    park_osmid = int(feature['closest_park_osmid'])  # Assumes 'osmid' is the identifier field
#    print(f"osmid {park_osmid}  {type(park_osmid)} feature:{feature['closest_park_name']}")
    if park_osmid in labels:
        print(f" [=>  osmid {osmid} => {labels[park_osmid]}     current name::{feature['closest_park_name']}")
#        if feature['closest_park_name'] == NULL:
        feature['closest_park_name'] = labels[park_osmid]
        layer.updateFeature(feature)
 #   if osmid in colours:
#        feature['park_color'] = colours[park_osmid]
#        layer.updateFeature(feature)
# Commit changes
layer.commitChanges()