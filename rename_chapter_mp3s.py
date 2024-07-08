import os
import shutil
import re
from ScriptureReference import book_codes

def get_book_code(book_number, book_name_spanish):
    for code, data in book_codes.items():
        if data['number'] == book_number:
            return code
    return None

def rename_and_copy_files(source_dir, dest_dir):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    pattern = r'([AB])(\d{2})__(\d{3})_([^_]+)______([A-Z0-9]+)\.mp3'
    for filename in os.listdir(source_dir):
        if filename.endswith('.mp3'):
            match = re.match(pattern, filename)
            if match:
                testament = match.group(1)
                book_number = int(match.group(2))
                chapter = int(match.group(3))
                book_name_spanish = match.group(4)

                if testament == 'B':
                    book_number += 39  # Adjust for New Testament books

                book_code = get_book_code(book_number, book_name_spanish)
                if book_code:
                    new_dir = os.path.join(dest_dir, book_code)
                    if not os.path.exists(new_dir):
                        os.makedirs(new_dir)

                    new_filename = f"{chapter}.mp3"
                    source_path = os.path.join(source_dir, filename)
                    dest_path = os.path.join(new_dir, new_filename)

                    shutil.copy2(source_path, dest_path)
                    print(f"Copied {filename} to {dest_path}")
            else:
                print(f"Skipped {filename} - doesn't match expected format")


# Usage
source_directory = 'C:/Users/caleb/Downloads/SPNPDTO1DA_palabra_de_dios_para_todos_ot/Spanish_spa_PDT_OT_Non-Drama'
destination_directory = 'C:/Users/caleb/Bible Translation Project/audio-verse-splitter/audio/esp/PDT'
rename_and_copy_files(source_directory, destination_directory)

# 'C:/Users/caleb/Downloads/SPNPDTO1DA_palabra_de_dios_para_todos_ot/Spanish_spa_PDT_OT_Non-Drama'
# 'C:/Users/caleb/Downloads/SPNERVN1DA_palabra_de_dios_para_todos_nt/Spanish_spa_ERV_NT_Non-Drama'