"""
This code shows how we can add data to our existing database.
Requirements:
- coco annotations file to be used for update
"""
import json
from database import *

create_temp_tables()

# change the file name/file path to the annotations file we are using as update
with open('via_project_30Sep2020_11h56m_coco.json') as json_file:
    data = json.load(json_file)

# add data from file to temp tables
add_image_data_temp(data)
add_category_data_temp(data)
add_annotations_data_temp(data)

# reorder temp images id to start with max id in main images table
reorder_id()

# update data in main table
update_images()
update_categories()
update_annotations()

# Delete temp tables
delete_temp_tables()