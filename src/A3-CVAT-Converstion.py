import xml.etree.ElementTree as ET
import os
import numpy as np

def load_xml(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    return root

def save_prediction(pano_id, selected_points, gsvDataPrediction):
    print(f"Saving Predictions [{pano_id}]")
    path = os.path.join(gsvDataPrediction,f"predicted_{pano_id}.csv")
    with open(path, 'w', newline='') as file:
        str = f"x, y, depth, type\n"
        file.write(str)
        for p in selected_points:
            type = 0
            str = f"{p[0]}, {p[1]}, {p[2]}, {type}\n"
            file.write(str)


if __name__ == "__main__":

    gsvRoot = "../../3-30-300-Athens-Data/GSV-Data/"
    gsvPanoramaRoot = os.path.join(gsvRoot,"panoramas-final-new/")
    gsvDepthRoot = os.path.join(gsvRoot,"panoramas-depth-new/")
    gsvDataPrediction = os.path.join(gsvRoot,"prediction-data/")

    root = '../../3-30-300-Athens-Data/gsv-tree-recognition'
    xml_file = os.path.join(root, "annotations.xml")

    root_xml = load_xml(xml_file)


    for image_obj in root_xml.findall('image'):
        image_file = image_obj.attrib['name']
        image_basename = os.path.basename(image_file)
        pano_id = os.path.splitext(image_basename)[0].split('_')[-1]
        depth_data = np.load(os.path.join(gsvDepthRoot,f"panorama_{pano_id}_raw_depth_meter.npy"))
        image_width = float(image_obj.attrib['width'])
        image_height = float(image_obj.attrib['height'])
        # for child in image_obj:
        #     print(child.tag)
        # print(image_obj.tag, image_file,image_obj.text)
        # print('----', ET.tostring(image_obj))
        selected_points = []
        for points in image_obj.findall('points'):
            point_str = points.attrib['points']
            print('\n','pano:'+pano_id, 'file:', image_file)
            ps = point_str.split(';')
            for p in ps:
                x,y = map(float,p.split(','))
                print(x/image_width,y/image_height)
                raw_depth = depth_data[x, y] * 100
                selected_points.append((x, y, raw_depth))

        save_prediction(pano_id, selected_points)
