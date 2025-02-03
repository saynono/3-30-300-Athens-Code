layer = QgsProject.instance().mapLayersByName("A30 -- Simple")[0]
layer.startEditing()

cnt_total = 0
cnt_okay = 0
green_average = 0.0
distance_average = 0.0
# Update the 'name_el' field with the label for the same osmid
for feature in layer.getFeatures():
    distance_average += float(feature['closest_park_distance'])
    green_coverage = float(feature['green_coverage'])  # Assumes 'osmid' is the identifier field
#    print(f"green_coverage {green_coverage}   {type(green_coverage)}")
    average += green_coverage
    if green_average >= .3:
        cnt_okay += 1
    cnt_total += 1
    
green_average /= cnt_total
distance_average /= cnt_total
print(f"cnt_okay : {cnt_okay}    cnt_total = {cnt_total} => green_average = {green_average}    distance_average = {distance_average}")