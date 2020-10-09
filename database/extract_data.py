import os
import psycopg2

from dotenv import load_dotenv

load_dotenv()

connection = psycopg2.connect(os.environ["DATABASE_URL"])

""" 
SQL Queries 
"""

SHOW_CATEGORIES = "SELECT id, name FROM categories;"
SELECT_ANNOTATIONS = "SELECT * FROM annotations WHERE category_id IN %s;"


categories = []


def show_categories():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SHOW_CATEGORIES)
            for row in cursor.fetchall():
                print(f"{row[0]}: {row[1]}")


show_categories()


def select_annotations(*cat_id):
    #cat_list = [f"category_id={str(i)}" for i in cat_id]
    #for i in range(len(cat_list)):
    #    cat_str = " OR ".join(cat_list)
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_ANNOTATIONS, (cat_id,))
            return cursor.fetchone()


print(select_annotations(5))

