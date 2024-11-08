import torch
import torchvision
import torchvision.transforms.functional


from realesrgan import RealESRGANer

from PIL import Image



print("Torch version:", torch.__version__)
print("Torchvision version:", torchvision.__version__)


# Load your JPEG image with artifacts

image_path = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/images/img_0eS4RnxNZPOhv3PhKvm0CQ_240.0_0.jpg"
image = Image.open(image_path)

image_result_path = "/home/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/temp/img_0eS4RnxNZPOhv3PhKvm0CQ_240.0_0_sharper.jpg"

# Initialize Real-ESRGAN model (using pre-trained weights)

weight_path = "/home/nono/Downloads/RealESRGAN_x4plus.pth"

model = RealESRGANer(4,weight_path)  # Adjust scale as needed

# Enhance image
output_image = model.enhance(image)

# Save or display the result
output_image.save(image_result_path)
output_image.show()

