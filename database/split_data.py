import os
import psycopg2
import json
import numpy as np

from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

connection = psycopg2.connect(os.environ["DATABASE_URL"])

# SQL sequence
SELECT_IMAGES = """SELECT DISTINCT images.*
FROM images
JOIN annotations 
ON images.id = annotations.image_id
WHERE category_id IN %s
ORDER BY images.id;"""
SELECT_ANNOTATIONS = "SELECT * FROM annotations WHERE category_id IN %s;"
SELECT_CATEGORIES = "SELECT * FROM categories WHERE id IN %s;"
SHOW_CATEGORIES = "SELECT id, name FROM categories;"

images_columns = ('id', 'width', 'height', 'file_name', 'license', 'date_captured')
annotations_columns = ('segmentation', 'area', 'bbox', 'iscrowd', 'id', 'image_id', 'category_id')
categories_columns = ('supercategory', 'id', 'name')


def split_train_test_val(image_list, test_ratio=0.2, val_ratio=0.2):
    shuffled_indices = np.random.permutation(len(image_list))
    test_end_index = int(len(image_list) * test_ratio)
    train_start_index = test_end_index + int(len(image_list) * val_ratio)

    test_indices = shuffled_indices[:test_end_index]
    val_indices = shuffled_indices[test_end_index:train_start_index]
    train_indices = shuffled_indices[train_start_index:]

    test_data = [image_list[i] for i in test_indices]
    val_data = [image_list[i] for i in val_indices]
    train_data = [image_list[i] for i in train_indices]

    return test_data, val_data, train_data

cat_id = (1,2,3,4)

images = []
annotations = []
categories = []

with connection:
    with connection.cursor() as cursor:
        cursor.execute(SELECT_IMAGES, (cat_id,))
        for row in cursor.fetchall():
            images.append(dict(zip(images_columns, row)))

        cursor.execute(SELECT_ANNOTATIONS, (cat_id,))
        for row in cursor.fetchall():
            annotations.append(dict(zip(annotations_columns, row)))

        cursor.execute(SELECT_CATEGORIES, (cat_id,))
        for row in cursor.fetchall():
            categories.append(dict(zip(categories_columns, row)))

test_images, val_images, train_images = split_train_test_val(images)

for i in annotations:
        segmentations = i['segmentation'].strip("'[]")
        segmentation_list = segmentations.split(",")
        i['segmentation'] = [[int(x) for x in segmentation_list]]

        bbox = i['bbox'].strip("'[]")
        bbox_list = bbox.split(",")
        i['bbox'] = [int(y) for y in bbox_list]

train_annotations = []
test_annotations = []
val_annotations = []

train_image_id = [train_images[i]['id'] for i in range(len(train_images))]
test_image_id = [test_images[i]['id'] for i in range(len(test_images))]
val_image_id = [val_images[i]['id'] for i in range(len(val_images))]

for i in range(len(annotations)):
    if annotations[i]['id'] in train_image_id:
        train_annotations.append(annotations[i])
    elif annotations[i]['id'] in test_image_id:
        test_annotations.append(annotations[i])
    elif annotations[i]['id'] in val_image_id:
        val_annotations.append(annotations[i])

description = "Description"  # input("Description: ")
current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

train_file = {
    "info": {
        "year": "2020",
        "version": "1.0",
        "description": "training annotation file",
        "contributor": "",
        "url": "url here",
        "date_created": current_datetime
    },
    "images": train_images,
    "annotations": train_annotations,
    "categories": categories
}

with open("train.json", 'w') as f:
    json.dump(train_file, f, indent=2)

test_file = {
    "info": {
        "year": "2020",
        "version": "1.0",
        "description": "test annotation file",
        "contributor": "",
        "url": "url here",
        "date_created": current_datetime
    },
    "images": test_images,
    "annotations": test_annotations,
    "categories": categories
}

with open("test.json", 'w') as f:
    json.dump(test_file, f, indent=2)


val_file = {
    "info": {
        "year": "2020",
        "version": "1.0",
        "description": "validation annotation file",
        "contributor": "",
        "url": "url here",
        "date_created": current_datetime
    },
    "images": val_images,
    "annotations": val_annotations,
    "categories": categories
}

with open("val.json", 'w') as f:
    json.dump(val_file, f, indent=2)





"""
def db_train_test_val_split(*cat_id, output_file="newfile"):
    images = []
    annotations = []
    categories = []

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_IMAGES, (cat_id,))
            for row in cursor.fetchall():
                images.append(dict(zip(images_columns, row)))

            cursor.execute(SELECT_ANNOTATIONS, (cat_id,))
            for row in cursor.fetchall():
                annotations.append(dict(zip(annotations_columns, row)))

            cursor.execute(SELECT_CATEGORIES, (cat_id,))
            for row in cursor.fetchall():
                categories.append(dict(zip(categories_columns, row)))
        
        split_train_test_val(images)

"""







"""
images = []
annotations = []
categories = []

cat_id = (1,2,3)
test_ratio = 0.2
val_ratio = 0.2

# append images to list from database
with connection:
    with connection.cursor() as cursor:
        cursor.execute(SELECT_IMAGES, (cat_id,))
        for row in cursor.fetchall():
            images.append(dict(zip(images_columns, row)))


shuffled_indices = np.random.permutation(len(images))
test_end_index = int(len(images) * test_ratio)
train_start_index = test_end_index + int(len(images) * val_ratio)

test_indices = shuffled_indices[:test_end_index]
val_indices = shuffled_indices[test_end_index:train_start_index]
train_indices = shuffled_indices[train_start_index:]


#Returns a list of
test_data = [images[i] for i in test_indices]
val_data = [images[i] for i in val_indices]
train_data = [images[i] for i in train_indices]


def db_train_test_val_split(*cat_id, output_file="newfile"):
    images = []
    annotations = []
    categories = []

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_IMAGES, (cat_id,))
            for row in cursor.fetchall():
                images.append(dict(zip(images_columns, row)))

    split_train_test_val(images)

    print(images)
"""

# with open(f"{output_file}.json", 'w') as f:
#     json.dump(coco_file, f, indent=2)


# db_to_coco(4,5, output_file="test_4and5")
#db_train_test_val_split(1, 2, 3)

"""
# show_categories()
def db_to_coco(*cat_id, output_file="newfile"):
    images = []
    annotations = []
    categories = []

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_IMAGES, (cat_id,))
            for row in cursor.fetchall():
                images.append(dict(zip(images_columns, row)))

            cursor.execute(SELECT_ANNOTATIONS, (cat_id,))
            for row in cursor.fetchall():
                annotations.append(dict(zip(annotations_columns, row)))

            cursor.execute(SELECT_CATEGORIES, (cat_id,))
            for row in cursor.fetchall():
                categories.append(dict(zip(categories_columns, row)))

    for i in annotations:
        segmentations = i['segmentation'].strip("'[]")
        segmentation_list = segmentations.split(",")
        i['segmentation'] = [[int(x) for x in segmentation_list]]

        bbox = i['bbox'].strip("'[]")
        bbox_list = bbox.split(",")
        i['bbox'] = [int(y) for y in bbox_list]

    description = "Description"  # input("Description: ")
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

    with open(f"{output_file}.json", 'w') as f:
        json.dump(coco_file, f, indent=2)
        
def split_train_test_val(image_list, test_ratio=0.2, val_ratio=0.2):

"""


