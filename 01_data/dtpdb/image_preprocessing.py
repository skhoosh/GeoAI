""" This function uses the Pillow libary to check the image size and compare it
with the coco file prepared in the VGG Image Annotator (VIA). As the outputs from
VIA are sometimes wrong, this script corrects the image sizes noted in the
coco annotations file.

Usage:
correct_image_size(folder_path, coco_file)
Inputs -
folder_path: folder storing all images as a string
coco_file: name of coco annotations file as a string
output_file (optional): output file with filepath
defaults to folder_path with updated_{coco_file} as name
Output -
updated coco annotations file with corrected image sizes
"""
import glob
import os

import json

from PIL import Image
from PIL import ExifTags


def actual_size(image):
    orientation = image._getexif().get(274)
    method = {
        2: Image.FLIP_LEFT_RIGHT,
        3: Image.ROTATE_180,
        4: Image.FLIP_TOP_BOTTOM,
        5: Image.TRANSPOSE,
        6: Image.ROTATE_270,
        7: Image.TRANSVERSE,
        8: Image.ROTATE_90
    }.get(orientation)

    if method is not None:
        image = image.transpose(method=method)
    width, height = image.size
    return width, height


def correct_image_size(folder_path, coco_file, output_file=f'updated_'):
    exceptions = []

    folder_path = folder_path + "\\"
    with open(coco_file) as file:
        data = json.load(file)

    for i in range(len(data["images"])):
        file_name = data["images"][i]["file_name"]
        coco_width = data["images"][i]["width"]
        coco_height = data["images"][i]["height"]

        file = os.path.join(folder_path, file_name)
        #print(file)
        try:
            im = Image.open(file)
            width, height = actual_size(im)

            if coco_width != width:
                data["images"][i]["width"] = width
                print(f"Changed width for {file_name}")

            if coco_height != height:
                data["images"][i]["height"] = height
                print(f"Changed height for {file_name}")
        except:
            exceptions.append(file)
            #print(f"exception raised: {file}\n")

    print(len(exceptions))

    with open(output_file, 'w') as outfile:
        json.dump(data, outfile)