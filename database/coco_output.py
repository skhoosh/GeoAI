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


# Functions runs through all categories available in the database and prints out a list
def show_categories():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SHOW_CATEGORIES)
            for row in cursor.fetchall():
                print(f"{row[0]}: {row[1]}")


# Function formats input images, annotations and categories list into proper coco file format to be written to a json file
def save_as_coco(images, annotations, categories, filepath="", filename="coco_output,json", description="description"):
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

    file = os.path.join(filepath, filename)

    with open(file, "w") as f:
        json.dump(coco_file, f, indent=2)


# Function takes in category ids and outputs a coco formatted file with chosen ids
# Can be stored as a copy/snapshot of the database
def db_to_coco(*cat_id, filepath="", filename="main_file.json"):
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

    save_as_coco(images, annotations, categories, filepath=filepath, filename=filename)


# Split image list dataset into train, test and validation annotation files
def image_train_test_val(image_list, test_ratio=0.2, val_ratio=0.2):
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


# split annotations data into training, test and validation json files
def db_train_test_val_split(*cat_id, test_ratio=0.2, val_ratio=0.2, filepath="", file_suffix="_01"):
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

    test_images, val_images, train_images = image_train_test_val(images, test_ratio, val_ratio)

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

    save_as_coco(train_images, train_annotations, categories, filepath=filepath, filename=f"train_{file_suffix}.json")
    save_as_coco(test_images, test_annotations, categories, filepath=filepath, filename=f"test_{file_suffix}.json")
    save_as_coco(val_images, val_annotations, categories, filepath=filepath, filename=f"val_{file_suffix}.json")


# db_train_test_val_split(1,2,3,4,5,test_ratio=0.3, val_ratio=0.2, filepath="split")







   # with open(f"{output_file}.json", 'w') as f:
   #     json.dump(coco_file, f, indent=2)


#db_to_coco(4,5, filename="00_aslkdfjael")
