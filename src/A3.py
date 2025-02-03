import utils
import cv2
import threading
from queue import Queue
import time

import directories
import A3_StitchImprove
import A3_create_GSV_points
import A3_collect_streetview_metadata

# A thread-safe queue to store the most recent processed image
image_queue = Queue(maxsize=1)

# Function to process images in the background
# Function to display the most recent image
def display_latest_image():
    while True:
        # Check if there's a new processed image in the queue
        if not image_queue.empty():
            latest_image = image_queue.get()

            # Display the latest processed image
            cv2.imshow("Latest Processed Image", latest_image)
            cv2.waitKey(1)

        # Short delay to avoid tight looping
        time.sleep(0.1)

def create_all_panoramas(metadata_df):
    global GSVCache, GSVPanoramaFolder
    # Load images and check if they are valid
    num_entries = metadata_df.shape[0]
    for index, row in metadata_df.iterrows():
        pano_id = row['panoID']
        # print(f"{row['panoID']}")
        # utils.print_df_results(row)
        # if index >= 2:
        #     break

        stitched_image = None
        panorama_path = os.path.join(GSVPanoramaFolder,f"panorama_{pano_id}.jpg")
        loaded_all_images = True
        if not os.path.exists(panorama_path):
            print(f"----- Panorama [{pano_id}]  |  {index} / {num_entries} [{((index/num_entries)*100):.2f}%]  Processing -----")
            # pano_id = "img_0A1aUxQvyr_KqmaokVoqvQ"
            image_paths = [f"img_{pano_id}_0.0_0.jpg",f"img_{pano_id}_60.0_0.jpg", f"img_{pano_id}_120.0_0.jpg",f"img_{pano_id}_180.0_0.jpg",f"img_{pano_id}_240.0_0.jpg",f"img_{pano_id}_300.0_0.jpg"]
            images = []
            for path in image_paths:
                img_path = os.path.join(GSVCache,path)
                if not os.path.exists(img_path):
                    loaded_all_images = False
                    print(f"Image file not found {img_path}")
                    continue
                img = cv2.imread(img_path)
                images.append(img)
            if not loaded_all_images:
                print(f"Couldn't load images of {pano_id}")
                continue
            stitched_image = A3_StitchImprove.create_panorama(images)
            cv2.imwrite(panorama_path,stitched_image)
        else:
            # print(f"Panorama exists: {panorama_path}")
            print(f"----- Panorama [{pano_id}]  |  {index} / {num_entries} [{((index/num_entries)*100):.2f}%]  Exists -----")
            stitched_image = cv2.imread(panorama_path)

        if loaded_all_images:
            # Put the processed image in the queue
            if image_queue.full():
                image_queue.get()
            image_queue.put(stitched_image)

    cv2.destroyAllWindows()
    exit(0)


def create_gsv_street_points():

    import os,os.path

    # root = '/Users/nono/Documents/workspaces/GIS/3-30-300-Athens-data/maps/Kypseli-All/'

    root_map = directories.MAP_DIR

    in_shape = directories.MAP_SHAPE_FILE
    outshpStreetNetwork = os.path.join(root_map,'Kypseli-Center-Streets')
    outshpPoints = os.path.join(root_map,'Kypseli-Center-Streets-10m.shp')
    mini_dist = 10 #the minimum distance between two generated points in meter
    A3_create_GSV_points.save_street_network(in_shape, outshpStreetNetwork)
    shpStreetNetwork = os.path.join(root_map,'Kypseli-Center-Streets/edges.shp')
    A3_create_GSV_points.create_points(shpStreetNetwork, outshpPoints, mini_dist)

def collect_streetview_metadata():
    # root = './spatial-data/Kypseli-All/'
    # root = '/Users/nono/Documents/workspaces/GIS/3-30-300-Athens-data/maps/Kypseli-All/'
    root_map = directories.MAP_DIR
    # inputShp = os.path.join(root, 'Kypseli-All.shp')
    inputShp = os.path.join(root_map, 'Kypseli-Center-Streets-10m.shp')

    key_file = './keys.txt'
    keylist = utils.get_keys(key_file)
    api_key = keylist[0]

    # api_key = os.environ["GOOGLE_MAPS_API_KEY"]


    # inputShp = '/Users/nono/Documents/workspaces/GIS/3-30-300-Athens/maps/Kypseli-All/Kypseli-All-Outlines.shp'
    outputTxt = os.path.join(root, 'metadata/')

    A3_collect_streetview_metadata.GSVpanoMetadataCollector(inputShp,1000, api_key, outputTxt)



if __name__ == "__main__":

    import os, os.path


    print("Starting...")

    # # pathRoot = "/home/nono/Documents/workspaces/cpp/darknet/Training/Athens-3-30-300-Panorama-Grey/"
    # pathRoot = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/"
    # # pathNames		= os.path.join(pathRoot,"Athens-3-30-300-Panorama-Grey.names")
    # # pathImage		= os.path.join(pathRoot,"panorama-final-depth/img_0w4VcFFiFSGZWk022DL-zg_panorama.png")
    # # pathResults		= os.path.join(pathRoot,"panorama-final-results/")
    #
    # pathPanoramas        = os.path.join(pathRoot,"GSV-Data/panoramas")
    #
    # pathMetaData         = os.path.join(pathRoot,"maps/Kypseli-All/metadata")

    root = directories.DATA_DIR
    print("ROOT: ", root)

    GSVCache = os.path.join(root, './GSV-Data/panodata-cache')
    GSVPanoramaFolder = os.path.join(root, './GSV-Data/panoramas-final-new')
    # GSVMetadata = os.path.join(root, 'maps/Kypseli-All/metadata/')
    GSVMetadata = os.path.join(root, 'selected_pano_ids.txt')
    # GSVMetadata = directories.GSV_DIR_METADATA

    if not os.path.exists(directories.MAP_SHAPE_FILE):
        print(f"MAP Shape file not found {directories.MAP_SHAPE_FILE} ")
        exit(0)

    if not os.path.exists(GSVCache):
        os.makedirs(GSVCache)
    if not os.path.exists(GSVPanoramaFolder):
        os.makedirs(GSVPanoramaFolder)

    # create_gsv_street_points()

    collect_streetview_metadata()

    metadata_df = utils.load_all_csvs(GSVMetadata)

    processing_thread = threading.Thread(target=create_all_panoramas, args=(metadata_df,))
    processing_thread.start()

    # Start the display in the main thread
    display_latest_image()








