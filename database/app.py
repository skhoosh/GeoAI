"""
This code creates new main tables and adds data from
a coco json file accordingly to the database.

Requirements:
- coco json file to be used as main annotations file
"""
import json
from database import *

create_main_tables()

with open('coco_test_file.json') as json_file:
    data = json.load(json_file)

add_image_data(data)
add_category_data(data)
add_annotation_data(data)

