import numpy as np
import cv2
import utils

from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.utils.download_util import load_file_from_url

from realesrgan import RealESRGANer
from realesrgan.archs.srvgg_arch import SRVGGNetCompact


#
# TODO: basicr might need some amendments:
#   import in basicr/data/degredations.py needs to be like this:
#   from torchvision.transforms._functional_tensor import rgb_to_grayscale
#
#

def improve_image(image_set,scale=1):
    gpu_id = 0
    netscale = 4
    outscale = scale
    denoise_strength = 0.5
    model_name = "RealESRGAN_x4plus"
    model_path = "/home/nono/Documents/workspaces/ai/Real-ESRGAN/weights/RealESRGAN_x4plus.pth"
    dni_weight = [denoise_strength, 1 - denoise_strength]
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
    upsampler = RealESRGANer(
        scale=netscale,
        model_path=model_path,
        dni_weight=dni_weight,
        model=model,
        tile=0,
        tile_pad=10,
        pre_pad=0,
        half=True,
        gpu_id=gpu_id)

    image_set_res = []
    for img in image_set:
        try:
            img_res, _ = upsampler.enhance(img, outscale=outscale)
            image_set_res.append(img_res)
        except RuntimeError as error:
            print('Error', error)
            print('If you encounter CUDA out of memory, try to set --tile with a smaller number.')


    return image_set_res

def stitch_and_improve(image_set):
    image_set = improve_image(image_set)
    image_set = warp_images(image_set)
    return image_set

def warp_images(image_set):
    result = []
    for img in image_set:
        h, w = img.shape[:2]
        focal_length = w / (2.0 * np.tan(np.deg2rad(60) / 2.0))
        K = np.array([[focal_length,0,w/2],[0,focal_length,h/2],[0,0,1]]) # mock intrinsics
        img_cyl = utils.cylindricalWarp(img, K)

        # Check if the image has an alpha channel
        if img_cyl.shape[2] == 4:
            # Remove the alpha channel by keeping only the first three channels (BGR)
            x, y, w, h = cv2.boundingRect(img_cyl[..., 3])
            w -= 1
            img_cyl = img_cyl[y:y+h, x:x+w, :]
            img_cyl = img_cyl[:, :, :3]

        result.append(img_cyl)

    return result

def create_panorama(image_set):

    image_set = improve_image(image_set,4)
    image_set = warp_images(image_set)

    result = np.hstack(image_set)
    h, w = result.shape[:2]
    scale = 2400/w
    result.resize()
    h = int(h * scale)
    result = cv2.resize(result, (2400, h))

    top_crop = (h - 400) // 2
    bottom_crop = top_crop + 400
    result = result[top_crop:bottom_crop, :]

    result_final = np.zeros((400, 2400, 3), dtype=np.uint8)
    result_final[0:400, 0:2400] = result


    return result_final

