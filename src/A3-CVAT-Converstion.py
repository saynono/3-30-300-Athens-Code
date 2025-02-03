import xml.etree.ElementTree as ET
import os
import numpy as np
from torch.onnx.symbolic_opset9 import clamp
import math

def load_xml(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    return root

def save_prediction(pano_id, selected_points, gsvDataPrediction):

    if len(selected_points) == 0:
        return

    path = os.path.join(gsvDataPrediction,f"predicted_{pano_id}.csv")
    if os.path.exists(path):
        with open(path, 'r') as file:
            line_count = sum(1 for line in file)
            # print(f"potentially skip file: {path}, line count: {line_count} vs {len(selected_points)}")
            if len(selected_points) == line_count-1:
                # print("yes, skipping.")
                return

    print(f"|___Saving Predictions [{pano_id}]")
    with open(path, 'w', newline='') as file:
        str = f"x, y, depth, type\n"
        file.write(str)
        for p in selected_points:
            type = 0
            str = f"{p[0]}, {p[1]}, {p[2]}, {type}\n"
            file.write(str)


if __name__ == "__main__":

    gsvRoot = "../../3-30-300-Athens-Data/GSV-Data/"
    gsvRoot = os.path.abspath(gsvRoot)
    gsvPanoramaRoot = os.path.join(gsvRoot,"panoramas-final-new/")
    gsvDepthRoot = os.path.join(gsvRoot,"panoramas-depth-new/")
    gsvDataPrediction = os.path.join(gsvRoot,"prediction-data/")

    root = '../../3-30-300-Athens-Data/gsv-tree-recognition'
    root = os.path.abspath(root)
    xml_file = os.path.join(root, "annotations-cvat-athens-330300-250203.xml")

    xml_file = os.path.abspath(xml_file)
    print(xml_file)
    root_xml = load_xml(xml_file)


    for image_obj in root_xml.findall('image'):
        image_file = image_obj.attrib['name']
        image_basename = os.path.basename(image_file)
        pano_id = os.path.splitext(image_basename)[0].split('_', 1)[-1]
        depth_data = np.load(os.path.join(gsvDepthRoot,f"panorama_{pano_id}_raw_depth_meter.npy"))
        image_width = int(image_obj.attrib['width'])
        image_height = int(image_obj.attrib['height'])
        # for child in image_obj:
        #     print(child.tag)
        # print(image_obj.tag, image_file,image_obj.text)
        # print('----', ET.tostring(image_obj))
        selected_points = []
        for points in image_obj.findall('points'):
            point_str = points.attrib['points']
            # print('\n','pano:'+pano_id, 'file:', image_file)
            ps = point_str.split(';')
            for p in ps:
                x,y = map(float,p.split(','))
                x = min(round(x),image_width-1)
                y = min(round(y),image_height-1)
                raw_depth = depth_data[y, x] * 100
                selected_points.append((x, y, raw_depth))

        print('pano_id',pano_id,'os.path.splitext(image_basename)[0]',os.path.splitext(image_basename)[0],"   Points:",len(selected_points))
        save_prediction(pano_id, selected_points, gsvDataPrediction)
