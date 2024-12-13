from ultralytics import YOLO
import cv2

# Load a COCO-pretrained YOLO11n model
path_yolo = "/home/nono/Documents/workspaces/ai/models/yolo11m-seg.pt"
# model = YOLO("yolov8x-oiv7.pt")
# model = YOLO(path_yolo)
model = YOLO("yolo11m.pt")


pano_id = "0u0osFBRo18zmXVeUQ7O_w"
path = f"/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/GSV-Data/panoramas-final-new/panorama_{pano_id}.jpg"

# path = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/GSV-Data/panodata-cache/img_0HSGoUR2xrfZUDzE3su-IA_180.0_0.jpg"
# path ="/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/GSV-Data/panodata-cache-new/__img_6r45PkaRKNOVguhuPv_aQQ_180.0_0.jpg"
# Run inference with bboxes prompt
results = model(path)

img = results[0].plot()
cv2.imshow("Depth Image", img)
cv2.waitKey(0)
cv2.destroyAllWindows()