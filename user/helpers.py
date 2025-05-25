from datetime import datetime
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import threading
import requests
from cloudinary.uploader import upload
from wuzzuf.queue import send_to_queue

load_dotenv()

client = MongoClient(os.getenv('MONGO_URI'))
db = client['job_db']
jobs_collection=db["jobs"]
rag_names_collection = db["rag_names"]
rag_collection=db["Rag"]
user_collection=db["user_cv_db"]


def extract_dob_from_national_id(nat_id):
    if len(nat_id) < 7 or not nat_id.isdigit():
        return None
    
    century_digit = nat_id[0]
    year = int(nat_id[1:3])
    month = int(nat_id[3:5])
    day = int(nat_id[5:7])

    if century_digit == '2':
        year += 1900
    elif century_digit == '3':
        year += 2000
    else:
        return None  # Invalid century

    try:
        return datetime(year, month, day).date()
    except ValueError:
        return None  # Invalid date

def update_company_mongo(company, old_company):
    print("company updated in mongo", company)
    jobs_collection.update_many(
        {"company": old_company.id},
        {
            "$set": {
                "company_name": company["name"] if 'name' in company else old_company.name,
                "company_logo": company["img"] if company["img"] else None
            }
        },
    )

def update_jobseeker_mongo(data, user):
    print("user updated in mongo", user)
    user_collection.update_one(
        {"user_id": user.id},
        {
            "$set": {
                "name": data["name"] or user.name,
                "seniority": data["seniority"] if data["seniority"] else None
            }
        },
    )

def send_rag(file, chunk_size=500, chunk_overlap=50):
    files = {"pdf": file}
    try:
        uploaded_file = upload(file, resource_type="raw")
        data = {
            "name": uploaded_file["original_filename"],
            "url": uploaded_file["secure_url"],
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap
        }
        print("data", data)
        # send_to_queue("job_queue", "post", "rag", data)
        requests.post(
            f"{os.getenv('FASTAPI_URL')}/rag",
            json=data
        )

    except Exception as e:
        print(f"Failed to send rag : {e}")
