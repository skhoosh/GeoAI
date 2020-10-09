"""
This code helps us to check the database against our images folder to identify
images that have not yet been included in the annotations database.

These images are copied into a new folder "00 NotAnnotated"
so that we may access the images easily and annotate them accordingly.

Requirements:
- Images file path that contains all images to be included in the database
"""
import shutil, os
import psycopg2
from database import *


images_folder = "C:/Users/steff/Documents/05 GeoAI/03 AI/GeoAI/data/01 Images"
filenames = os.listdir(images_folder)


directory = "00 NotAnnotated"
path = os.path.join(images_folder, directory)

os.mkdir(path)

not_annotated_files = check_files_not_in_db(filenames)

for f in not_annotated_files:
    f = os.path.join(images_folder,f)
    shutil.copy(f, path)