import pandas as pd
import sqlite3
import os
import logging
import tracemalloc
from dotenv import load_dotenv
load_dotenv()

tracemalloc.start()
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s : %(message)s')
logger= logging.getLogger()

# Path to local yelp datasets. 
# Data Source: https://www.yelp.com/dataset

tip_path= 'data\yelp_academic_dataset_tip.json'
user_path= 'data\yelp_academic_dataset_user.json'
checkin_path = 'data\yelp_academic_dataset_checkin.json'
business_path = 'data\yelp_academic_dataset_business.json'
review_path = 'data\yelp_academic_dataset_review.json'

def apply_migration_script(db_path, script_path):
    with sqlite3.connect(db_path) as conn:
        with open(script_path, 'r') as f:
            script = f.read()
        conn.executescript(script)
        conn.commit()

db_path = os.getenv('db_path')
script_path = 'db_migrations\create_table._0001up.sql'
logger.info('Creating the Database schema')
apply_migration_script(db_path, script_path)

# Read the json file into pandas dataframe to load into the database. 

logger.info('Read JSON data into Pandas Dataframe')
df = pd.read_json(tip_path, lines=True, engine= 'pyarrow')
df = df.rename(columns={
    "user_id": "user_id",
    "business_id": "business_id",
    "text": "review_text",
    "date": "review_date",
    "compliment_count": "compliment_count"
})

# Create the database schema using sql migration script. 

conn = sqlite3.connect(db_path)
logger.info('Loading the data into DB')
df.to_sql('tips', con=conn, if_exists='append', index=False)
for chunk in pd.read_json(user_path, lines=True, chunksize=10000):
    chunk.to_sql('users', con=conn, if_exists='append', index=False)

current, peak = tracemalloc.get_traced_memory()
logger.info(f'Data insert successful. Current memory usage: {round(current / 10**6, 2)}MB; Peak was: {round(peak / 10**6, 2)}MB')