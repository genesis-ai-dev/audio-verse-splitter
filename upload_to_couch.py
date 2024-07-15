import couchdb
import base64
from datetime import datetime
from dotenv import load_dotenv
import os
import uuid
from ScriptureReference import ScriptureReference, book_codes
import time
import random
from requests.exceptions import RequestException

load_dotenv()
username = os.getenv('COUCHDB_USER')
password = os.getenv('COUCHDB_PASSWORD')

# Connect to CouchDB
couch = couchdb.Server(f'https://{username}:{password}@couchdb-n66j.onrender.com')
db = couch['assets']

def check_connection():
    try:
        version = couch.version()
        print("Successfully connected to CouchDB")
        print(f"Server version: {version}")
        print("Attempting to access the 'assets' database...")
        db_info = db.info()
        print(f"Successfully accessed 'assets' database. Doc count: {db_info['doc_count']}")
    except Exception as e:
        print(f"Error: {e}")

check_connection()

# Paths
audio_base_path = 'audio/output/PDT_webm'
xhtml_dir = 'C:/Users/caleb/Downloads/SPAWTC_palabra_de_dios_para_todos_text/content/chapters'

def load_scores():
    scores = {}
    print("Loading scores...")
    try:
        with open('normalized_low_score_report.txt', 'r') as f:
            for line in f:
                # print(f"Processing line: {line.strip()}")
                parts = line.split(': ')
                if len(parts) >= 2:
                    vref = parts[0]
                    score = float(parts[1].split()[0])
                    scores[vref] = score
                #     print(f"Added score: {vref} = {score}")
                # else:
                #     print(f"Skipped line: {line.strip()}")
    except Exception as e:
        print(f"Error loading scores: {e}")
    
    # print(f"Total scores loaded: {len(scores)}")
    return scores

# After calling load_scores()
scores = load_scores()
# print("First 5 scores:")
# for i, (vref, score) in enumerate(scores.items()):
#     print(f"{vref}: {score}")
#     if i == 4:
#         break

def upload_verse(verse_ref, verse_text, audio_path, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            audio_data = None
            if audio_path:
                with open(audio_path, 'rb') as audio_file:
                    audio_data = audio_file.read()

            unique_id = str(uuid.uuid4())
            bible_version = "PDT"
            asset_id = f"{verse_ref}-{bible_version}-audio-and-text-{unique_id}"

            book, chapter_verse = verse_ref.split('_')
            chapter, verse = chapter_verse.split(':')
            chapter_ref = f"{book} {chapter}"

            document = {
                '_id': asset_id,
                'user_id': 'user123',
                'updated_at': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
                'type': 'audio',
                'name': f'{verse_ref} Audio',
                'text': verse_text,
                'tags': [chapter_ref, verse_ref, 'bible', 'verse'],
                'language': 'spa',
            }
            score = scores.get(verse_ref, 0)
            print(f"Score for {verse_ref}: {score}")
            if score > 66.96 and audio_data:
                try:
                    encoded_audio = base64.b64encode(audio_data).decode('utf-8')
                    document['_attachments'] = {
                        'audio.webm': {
                            'content_type': 'audio/webm;codecs=opus',
                            'data': encoded_audio
                        }
                    }
                except Exception as e:
                    print(f"Error encoding audio for {verse_ref}: {e}")
                    # Continue without audio attachment if encoding fails
                    pass

            doc_id, doc_rev = db.save(document)
            print(f"Uploaded: {verse_ref}" + (" with audio" if score > 66.96 and audio_data else ""))
            return  # Success, exit the function

        except couchdb.http.ResourceConflict:
            print(f"Conflict: {verse_ref} already exists.")
            return  # This is not a retryable error, so we exit

        except (RequestException, couchdb.http.ServerError, AttributeError) as e:
            if attempt < max_retries - 1:
                delay = (base_delay * 2 ** attempt) + (random.randint(0, 1000) / 1000)
                print(f"Error uploading {verse_ref}: {e}. Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                print(f"Failed to upload {verse_ref} after {max_retries} attempts: {e}")

        except Exception as e:
            print(f"Unexpected error uploading {verse_ref}: {e}")
            return  # For unexpected errors, we don't retry
    

def main():
    verses = ScriptureReference('num 7:26', bible_filename=xhtml_dir, source_type='xhtml').verses


    for i, verse in enumerate(verses):
        verse_ref, verse_text = verse
        book, chapter_verse = verse_ref.split('_')
        chapter, verse_num = chapter_verse.split(':')
        
        book_num = str(book_codes[book]['number']).zfill(2)
        audio_file = f"verse_{book}_{chapter}_{verse_num}.webm"
        audio_path = os.path.join(audio_base_path, f"{book_num}_{book}", chapter, audio_file)

        if os.path.exists(audio_path):
            upload_verse(verse_ref, verse_text, audio_path)
        else:
            print(f"Audio file not found for {verse_ref}. Uploading text only.")
            upload_verse(verse_ref, verse_text, None)  # Pass None for audio_path

        if i == 2:  # After the first 3 verses have been uploaded
            print("First 3 verses uploaded. Continue? (y/n)")
            if input().lower() != 'y':
                print("Upload stopped.")
                return

        if (i + 1) % 1000 == 0:  # Pause every 1000 uploads
            print(f"Uploaded {i + 1} documents. Pausing for 10 seconds...")
            time.sleep(10)

        time.sleep(0.1)  # Small delay to prevent overwhelming the server

if __name__ == "__main__":
    main()