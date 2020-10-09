import os
import psycopg2
import json

from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

connection = psycopg2.connect(os.environ["DATABASE_URL"])

# SQL sequence
SELECT_IMAGES = "SELECT * FROM images;"
SELECT_ANNOTATIONS = "SELECT * FROM annotations;"
SELECT_CATEGORIES = "SELECT * FROM categories;"

images_columns = ('id', 'width', 'height', 'file_name', 'license', 'date_captured')
annotations_columns = ('segmentation', 'area', 'bbox', 'iscrowd', 'id', 'image_id', 'category_id')
categories_columns = ('supercategory', 'id', 'name')

images = []
annotations = []
categories = []

with connection:
    with connection.cursor() as cursor:
        cursor.execute(SELECT_IMAGES)
        for row in cursor.fetchall():
            images.append(dict(zip(images_columns, row)))

        cursor.execute(SELECT_ANNOTATIONS)
        for row in cursor.fetchall():
            annotations.append(dict(zip(annotations_columns, row)))

        cursor.execute(SELECT_CATEGORIES)
        for row in cursor.fetchall():
            categories.append(dict(zip(categories_columns, row)))


for i in annotations:
    segmentations = i['segmentation'].strip("'[]")
    segmentation_list = segmentations.split(",")
    i['segmentation'] = [[int(x) for x in segmentation_list]]

    bbox = i['bbox'].strip("'[]")
    bbox_list = bbox.split(",")
    i['bbox'] = [int(y) for y in bbox_list]



description = "Description" #input("Description: ")
current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

coco_file = {
    "info": {
            "year": "2020",
            "version": "1.0",
            "description": description,
            "contributor": "",
            "url": "url here",
            "date_created": current_datetime
        },
    "images": images,
    "annotations": annotations,
    "categories": categories
}


with open("newfile.json", 'w') as f:
    json.dump(coco_file, f, indent=2)
