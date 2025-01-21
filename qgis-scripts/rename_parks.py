layer = QgsProject.instance().mapLayersByName("AXXX - Parks")[0]
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
        value = category.value()  # The osmid value used in styling
        colour = category.symbol().color().name() 
        label = category.label()  # The name from the styling
        labels[value] = label  # Map osmid to label
        colours[value] = colour  # Map osmid to label
        print(f"label {label}   => {value}    /   {colour}")


# Update the 'name_el' field with the label for the same osmid
for feature in layer.getFeatures():
    osmid = feature['osmid']  # Assumes 'osmid' is the identifier field
    print(f" =>osmid {osmid}   feature:{feature['name:el']}")
    if osmid in labels:
#        print(f"  osmid {osmid} => {labels[osmid]}     ES:{feature['name:es']}")
        feature['name:el'] = labels[osmid]
        if feature['name'] == NULL:
            feature['name'] = labels[osmid]
        layer.updateFeature(feature)
    if osmid in colours:
        feature['park_color'] = colours[osmid]
        layer.updateFeature(feature)

# Commit changes
layer.commitChanges()
