# from ScriptureReference import ScriptureReference

# xhtml_dir = 'C:/Users/caleb/Downloads/SPAWTC_palabra_de_dios_para_todos_text/content/chapters'

# verses = ScriptureReference('1 cor 16:1', '1 cor 17:1', bible_filename=xhtml_dir, source_type='xhtml').verses #spa-sparvg  spa-spaRV1909

# [print (verse) for verse in verses]
# print(len(verses))




import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import os
import uuid
import time
import random

load_dotenv()
username = os.getenv('COUCHDB_USER')
password = os.getenv('COUCHDB_PASSWORD')
base_url = f'https://{username}:{password}@couchdb-n66j.onrender.com'

def check_connection():
    try:
        response = requests.get(f'{base_url}')
        response.raise_for_status()
        print("Successfully connected to CouchDB")
        print(f"Server version: {response.json()['version']}")
        
        db_response = requests.get(f'{base_url}/assets')
        db_response.raise_for_status()
        db_info = db_response.json()
        print(f"Successfully accessed 'assets' database. Doc count: {db_info['doc_count']}")
    except Exception as e:
        print(f"Error: {e}")

def check_server_status():
    try:
        response = requests.get(f'{base_url}/_up')
        response.raise_for_status()
        print("Server is up and running")
        print(f"Status: {response.json()}")
    except Exception as e:
        print(f"Error checking server status: {e}")

def test_upload():
    try:
        doc = {
            '_id': f'test_doc_{uuid.uuid4()}',
            'test': 'data',
            'timestamp': datetime.now().isoformat()
        }
        response = requests.post(f'{base_url}/assets', json=doc)
        response.raise_for_status()
        result = response.json()
        print(f"Successfully uploaded test document with id: {result['id']}")
        return result['id']
    except Exception as e:
        print(f"Failed to upload test document: {e}")
        return None

def test_retrieve(doc_id):
    if doc_id:
        try:
            response = requests.get(f'{base_url}/assets/{doc_id}')
            response.raise_for_status()
            doc = response.json()
            print(f"Successfully retrieved test document: {doc}")
        except Exception as e:
            print(f"Failed to retrieve test document: {e}")

def retrieve_existing_doc():
    try:
        # Replace 'known_doc_id' with an ID of a document you know exists in the database
        response = requests.get(f'{base_url}/assets/1')
        response.raise_for_status()
        print("Successfully retrieved existing document")
        print(f"Document: {response.json()}")
    except Exception as e:
        print(f"Error retrieving existing document: {e}")

def check_database_info():
    try:
        response = requests.get(f'{base_url}/assets')
        response.raise_for_status()
        print("Database information:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error checking database info: {e}")

def create_test_database():
    try:
        response = requests.put(f'{base_url}/test_database')
        response.raise_for_status()
        print("Successfully created test database")
        print(f"Response: {response.json()}")
        
        # Clean up by deleting the test database
        delete_response = requests.delete(f'{base_url}/test_database')
        delete_response.raise_for_status()
        print("Successfully deleted test database")
    except Exception as e:
        print(f"Error creating/deleting test database: {e}")



# Main execution
check_connection()
check_server_status()
check_database_info()
test_doc_id = test_upload()
test_retrieve(test_doc_id)
retrieve_existing_doc()
create_test_database()

# You can now use the upload_verse function in your main loop as before

