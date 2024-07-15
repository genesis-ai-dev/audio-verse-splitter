import couchdb
import requests
import os
from dotenv import load_dotenv

load_dotenv()
username = os.getenv('COUCHDB_USER')
password = os.getenv('COUCHDB_PASSWORD')
modal_url = os.getenv('MODAL_URL')
couch = couchdb.Server(f'https://{username}:{password}@couchdb-n66j.onrender.com')
db = couch['assets']

modal_url = f"https://{modal_url}.modal.run/transcribe"  # Replace with your actual Modal URL

def fetch_audio_from_couchdb(doc_id):
    try:
        doc = db[doc_id]
        attachment = doc.get('_attachments', {}).get('audio.webm')
        if attachment:
            audio_data = db.get_attachment(doc_id, 'audio.webm')
            return audio_data.read()
        else:
            print(f"No audio attachment found in document {doc_id}.")
    except couchdb.http.ResourceNotFound:
        print(f"Document with ID {doc_id} not found.")
    except Exception as e:
        print(f"An error occurred while fetching the document: {e}")
    return None

def transcribe_audio(audio_data, language):
    files = {'audio': ('audio.webm', audio_data, 'audio/webm')}
    data = {'language': language}
    response = requests.post(modal_url, files=files, data=data)
    response.raise_for_status()
    return response.json()["transcription"]

def main():
    doc_id = "ZEP_3:9-PDT-audio-and-text-fe7847dc-8612-4809-8cc6-1132a4e64f2b"  # Example document ID
    language = "es"  # Example language

    audio_data = fetch_audio_from_couchdb(doc_id)
    if audio_data:
        transcription = transcribe_audio(audio_data, language)
        print(f"Transcription: {transcription}")
    else:
        print("No audio attachment found or an error occurred.")

if __name__ == "__main__":
    main()