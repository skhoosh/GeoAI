"""This file contains functions that work on the PostgreSQL Database
Broadly, the code:
1) Creates the main tables that store images, categories and annotations
2) Creates temporary tables that can be inserted into the main table
3) Checks if the database contains a particular image
4) Extracts information out of the database in coco format"""

import os
import psycopg2

from dotenv import load_dotenv

load_dotenv()

connection = psycopg2.connect(os.environ["DATABASE_URL"])

""" 
SQL Statements
-------------- Create Main Tables ------------ 
"""
CREATE_MAIN_IMAGES_TABLE = """CREATE TABLE IF NOT EXISTS images(
    id SERIAL PRIMARY KEY,
    width INTEGER,
    height INTEGER,  
    file_name TEXT UNIQUE,  
    license INTEGER, 
    date_captured TEXT
    );"""
CREATE_MAIN_CATEGORIES_TABLE = """CREATE TABLE IF NOT EXISTS categories(
    supercategory TEXT, 
    id SERIAL PRIMARY KEY, 
    name TEXT
    );"""
CREATE_MAIN_ANNOTATIONS_TABLE = """CREATE TABLE IF NOT EXISTS annotations(
    segmentation TEXT,
    area INTEGER,
    bbox TEXT,
    iscrowd INTEGER, 
    id SERIAL PRIMARY KEY, 
    image_id INTEGER, 
    category_id INTEGER,
    FOREIGN KEY(image_id) REFERENCES images(id) ON UPDATE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id)
    );"""

INSERT_IMAGES = "INSERT INTO images VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT (file_name) DO NOTHING;"
INSERT_CATEGORIES = "INSERT INTO categories VALUES(%s,%s,%s);"
INSERT_ANNOTATIONS = """INSERT INTO annotations (segmentation, area, bbox, iscrowd, id, image_id, category_id)
    SELECT %s,%s,%s,%s,%s,%s,%s
    WHERE EXISTS (SELECT id
     FROM images
     WHERE id =%s);
"""

# ------------ Create temp tables ------------
CREATE_TEMP_IMAGES_TABLE = """CREATE TABLE IF NOT EXISTS temp_images(
    id SERIAL PRIMARY KEY,
    width INTEGER,
    height INTEGER, 
    file_name TEXT UNIQUE,  
    license INTEGER, 
    date_captured TEXT
    );"""
CREATE_TEMP_CATEGORIES_TABLE = """CREATE TABLE IF NOT EXISTS temp_categories(
    supercategory TEXT, 
    id SERIAL PRIMARY KEY, 
    name TEXT
    );"""
CREATE_TEMP_ANNOTATIONS_TABLE = """CREATE TABLE IF NOT EXISTS temp_annotations(
    segmentation TEXT,
    area INTEGER,
    bbox TEXT,
    iscrowd INTEGER, 
    id SERIAL, 
    image_id INTEGER, 
    category_id INTEGER,
    FOREIGN KEY(image_id) REFERENCES temp_images(id) ON UPDATE CASCADE,
    FOREIGN KEY (category_id) REFERENCES temp_categories(id)
    );"""

INSERT_IMAGES_TEMP = "INSERT INTO temp_images VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT (file_name) DO NOTHING;"
INSERT_CATEGORIES_TEMP = "INSERT INTO temp_categories VALUES(%s,%s,%s);"
INSERT_ANNOTATIONS_TEMP = """INSERT INTO temp_annotations (segmentation, area, bbox, iscrowd, id, image_id, category_id)
    SELECT %s,%s,%s,%s,%s,%s,%s
    WHERE EXISTS (SELECT id
     FROM temp_images
     WHERE id =%s);
"""

# re-order primary keys of temp files to continue off main file
SET_TEMP_IMAGES_SERIES = """SELECT setval(pg_get_serial_sequence('temp_images', 'id'),
                                    (SELECT max(id) FROM images));"""
UPDATE_TEMP_IMAGES_ID = "UPDATE temp_images SET id=nextval(pg_get_serial_sequence('temp_images', 'id'));"

SET_TEMP_ANNOTATIONS_SERIES = """SELECT setval(pg_get_serial_sequence('temp_annotations', 'id'),
                                    (SELECT max(id) FROM annotations));"""
UPDATE_TEMP_ANNOTATIONS_ID = "UPDATE temp_annotations SET id=nextval(pg_get_serial_sequence('temp_annotations', 'id'));"

# Insert temp table into main tables
UPDATE_IMAGES = "INSERT INTO images SELECT * FROM temp_images ON CONFLICT (file_name) DO NOTHING"
UPDATE_CATEGORIES = "INSERT INTO categories SELECT supercategory, id, name FROM temp_categories ON CONFLICT (id) DO NOTHING"
UPDATE_ANNOTATIONS = """INSERT INTO annotations SELECT * FROM temp_annotations
                        WHERE EXISTS (SELECT id 
                        FROM images
                        WHERE id = image_id);"""

# Drop temp tables
DROP_TEMP_TABLES = "DROP TABLE IF EXISTS temp_images, temp_categories, temp_annotations;"

# --------------- Checking for non-annotated images -----------------
CREATE_FILE_LIST = "CREATE TABLE IF NOT EXISTS filenames (filename TEXT);"
INSERT_FILENAMES = "INSERT INTO filenames VALUES(%s);"

COMPARE_FILENAMES = """SELECT * FROM filenames WHERE filename 
                        NOT IN (SELECT file_name FROM images);"""

DROP_FILENAMES_TABLE = "DROP TABLE IF EXISTS filenames;"


# Functions:
# --------------- MAIN TABLES ---------------------------------
def create_main_tables():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_MAIN_IMAGES_TABLE)
            cursor.execute(CREATE_MAIN_CATEGORIES_TABLE)
            cursor.execute(CREATE_MAIN_ANNOTATIONS_TABLE)


# -- add data to main tables --
def add_images(image_id, width, height, file_name, image_license, date_captured):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(INSERT_IMAGES, (image_id, width, height, file_name, image_license, date_captured))


def add_categories(supercategory, category_id, name):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(INSERT_CATEGORIES, (supercategory, category_id, name))


def add_annotations(segmentation, area, bbox, iscrowd, annotation_id, image_id, category_id):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(INSERT_ANNOTATIONS, (segmentation, area, bbox, iscrowd, annotation_id, image_id, category_id, image_id))


def add_image_data(data):
    for image in data['images']:
        image_id = image['id']
        width = image['width']
        height = image['height']
        file_name = image['file_name']
        image_license = image['license']
        date_captured = image['date_captured']
        add_images(image_id, width, height, file_name, image_license, date_captured)


def add_category_data(data):
    for category in data['categories']:
        supercategory = category['supercategory']
        category_id = category['id']
        name = category['name']
        add_categories(supercategory, category_id, name)


def add_annotation_data(data):
    for annotation in data['annotations']:
        segmentation = f"'{annotation['segmentation']}'"
        area = annotation['area']
        bbox = f"'{annotation['bbox']}'"
        iscrowd = annotation['iscrowd']
        annotation_id = annotation['id']
        image_id = annotation['image_id']
        category_id = annotation['category_id']
        add_annotations(segmentation, area, bbox, iscrowd, annotation_id, image_id, category_id)


# --------------- TEMP TABLES ---------------------------------
def create_temp_tables():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_TEMP_IMAGES_TABLE)
            cursor.execute(CREATE_TEMP_CATEGORIES_TABLE)
            cursor.execute(CREATE_TEMP_ANNOTATIONS_TABLE)


# -- add data to temp tables --
def add_images_temp(image_id, width, height, file_name, image_license, date_captured):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(INSERT_IMAGES_TEMP, (image_id, width, height, file_name, image_license, date_captured))


def add_categories_temp(supercategory, category_id, name):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(INSERT_CATEGORIES_TEMP, (supercategory, category_id, name))


def add_annotations_temp(segmentation, area, bbox, iscrowd, annotation_id, image_id, category_id):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(INSERT_ANNOTATIONS_TEMP, (segmentation, area, bbox, iscrowd, annotation_id, image_id, category_id, image_id))


def add_image_data_temp(data):
    for image in data['images']:
        image_id = image['id']
        width = image['width']
        height = image['height']
        file_name = image['file_name']
        image_license = image['license']
        date_captured = image['date_captured']
        add_images_temp(image_id, width, height, file_name, image_license, date_captured)


def add_category_data_temp(data):
    for category in data['categories']:
        supercategory = category['supercategory']
        category_id = category['id']
        name = category['name']
        add_categories_temp(supercategory, category_id, name)


def add_annotations_data_temp(data):
    for annotation in data['annotations']:
        segmentation = f"'{annotation['segmentation']}'"
        area = annotation['area']
        bbox = f"'{annotation['bbox']}'"
        iscrowd = annotation['iscrowd']
        annotation_id = annotation['id']
        image_id = annotation['image_id']
        category_id = annotation['category_id']
        add_annotations_temp(segmentation, area, bbox, iscrowd, annotation_id, image_id, category_id)


# -- reorder temp images and annotations id in preparation for adding to main table --
def reorder_id():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SET_TEMP_IMAGES_SERIES)
            cursor.execute(UPDATE_TEMP_IMAGES_ID)
            cursor.execute(SET_TEMP_ANNOTATIONS_SERIES)
            cursor.execute(UPDATE_TEMP_ANNOTATIONS_ID)


# -- update main tables --
def update_images():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(UPDATE_IMAGES)


def update_categories():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(UPDATE_CATEGORIES)


def update_annotations():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(UPDATE_ANNOTATIONS)


# -- delete temp tables --
def delete_temp_tables():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(DROP_TEMP_TABLES)


# --------------- CHECK FOR NON-ANNOTATED FILES ---------------------------------
def check_files_not_in_db(filenames):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_FILE_LIST)
            for f in filenames:
                cursor.execute(INSERT_FILENAMES, (f,))
            cursor.execute(COMPARE_FILENAMES)
            not_annotated_files = [i[0] for i in cursor.fetchall()]
            cursor.execute(DROP_FILENAMES_TABLE)
        return not_annotated_files




