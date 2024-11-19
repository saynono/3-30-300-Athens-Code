
from ultralytics import SAM
from ultralytics import FastSAM
import cv2

# Load a model
# model = SAM("sam2.1_b.pt")
model = SAM("sam2.1_l.pt")
# model = FastSAM("FastSAM-s.pt")

# Display model information (optional)
model.info()

pano_id = "0u0osFBRo18zmXVeUQ7O_w"
path = f"/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/GSV-Data/panoramas-final-new/panorama_{pano_id}.jpg"
# path = f"/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/GSV-Data/panoramas-depth-new/panorama_{pano_id}_depth.png"
# path = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/GSV-Data/panodata-cache/img_0HSGoUR2xrfZUDzE3su-IA_180.0_0.jpg"
# path ="/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/GSV-Data/panodata-cache-new/__img_6r45PkaRKNOVguhuPv_aQQ_180.0_0.jpg"
# Run inference with bboxes prompt
points = [120, 212]
labels = [1]
points = [[418, 260],[120, 212],[1946, 300],[1712, 314],[1694, 286],[2312, 271]]
labels = [1,2,3,4,5,6]
results = model(path, points=points)

img = results[0].plot()
cv2.imshow("Depth Image", img)
cv2.waitKey(0) & 0xff
cv2.destroyAllWindows()
# results[0].show()
# results[0].waitKey(0)
# print(f"Result: {type(results[0])}")

# 418, 260, 384.99324321746826, 0
# 120, 212, 1055.970287322998, 0
# 1946, 300, 967.0415878295898, 0
# 1712, 314, 862.7044677734375, 0
# 1694, 286, 721.9791889190674, 0
# 2312, 271, 874.174976348877, 0