# ==========================
# Imports
# ==========================


import os
from datetime import datetime
import pandas as pd
from bson import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv

# ==========================
# Load Environment Variables
# ==========================

load_dotenv()

# ==========================
# Connect to MongoDB
# ==========================

def connect_database():

    mongo_uri = os.getenv("MONGO_URI")

    client = MongoClient(mongo_uri)

    database = client["ForstaDatum"]

    return database


# ==========================
# Save Dataset
# ==========================

def save_dataset(filename, dataframe):

    database = connect_database()

    collection = database["datasets"]

    file_type = filename.split(".")[-1].lower()

    dataframe = dataframe.replace({pd.NaT: None})

    file_type = filename.split(".")[-1].lower()

    document = {
        "filename": filename,
        "file_type": file_type,
        "upload_time": datetime.now(),
        "rows": dataframe.shape[0],
        "columns": dataframe.shape[1],
        "data": dataframe.to_dict(orient="records")
    }

    # Check if dataset already exists
    existing = collection.find_one(
        {"filename": filename}
    )

    # Save or update dataset
    collection.replace_one(
        {"filename": filename},
        document,
        upsert=True
    )

    if existing:
        return "updated"

    return "saved"


# ==========================
# Get Saved Datasets
# ==========================

def get_saved_datasets():

    database = connect_database()

    collection = database["datasets"]

    datasets = collection.find(
        {},
        {
            "_id": 1,
            "filename": 1,
            "file_type": 1,
            "rows": 1,
            "columns": 1,
            "upload_time": 1
        }
    ).sort("upload_time", -1)

    return list(datasets)


# ==========================
# Load Saved Dataset
# ==========================

def load_saved_dataset(dataset_id):

    database = connect_database()

    collection = database["datasets"]

    document = collection.find_one(
        {
            "_id": ObjectId(dataset_id)
        }
    )

    if document is None:
        return None

    return pd.DataFrame(document["data"])


# ==========================
# Delete Dataset
# ==========================

def delete_dataset(dataset_id):

    database = connect_database()

    collection = database["datasets"]

    collection.delete_one(
        {
            "_id": ObjectId(dataset_id)
        }
    )