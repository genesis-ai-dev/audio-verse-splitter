import couchdb
from dotenv import load_dotenv
import os
from ScriptureReference import ScriptureReference

load_dotenv()
username = os.getenv('COUCHDB_USER')
password = os.getenv('COUCHDB_PASSWORD')

# Connect to CouchDB
couch = couchdb.Server(f'https://{username}:{password}@couchdb-n66j.onrender.com')
db = couch['assets']
xhtml_dir = 'C:/Users/caleb/Downloads/SPAWTC_palabra_de_dios_para_todos_text/content/chapters'

def get_all_verses():
    verses = ScriptureReference('gen 1:1', 'rev 22:21', bible_filename=xhtml_dir, source_type='xhtml').verses
    # Print first 5 verses
    [print(verse) for verse in verses[:5]]
    return [verse[0] for verse in verses]

def get_uploaded_verses():
    uploaded_verses = set()
    for i, doc_id in enumerate(db, start=1):
        doc = db[doc_id]
        verse_ref = doc.get('_id', '').split('-')[0]
        uploaded_verses.add(verse_ref)
        print(f"\rProcessing record {i}", end='', flush=True)
    print()  # Move to the next line after the loop completes
    # Print first 5 uploaded verses
    print("First 5 uploaded verses:")
    return uploaded_verses

def find_missing_verses():
    all_verses = set(get_all_verses())
    uploaded_verses = get_uploaded_verses()
    missing_verses = all_verses - uploaded_verses
    return missing_verses

if __name__ == "__main__":
    missing_verses = find_missing_verses()
    print(f"Missing verses count: {len(missing_verses)}")
    for verse in sorted(missing_verses):
        print(verse)