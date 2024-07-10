import os
import glob
import math
from ScriptureReference import ScriptureReference

def normalize_score(original_score, reference_length):
    if original_score == 100:
        return 100.0
    
    # Adjust the base score based on length
    length_factor = 1 - (math.log(1 + reference_length) / 10)
    base_score = original_score * length_factor
    
    # Scale the score to ensure it remains between 0 and 100
    normalized_score = (base_score / 90) * 100
    
    return min(normalized_score, 99.99)  # Cap at 99.99 to distinguish from perfect 100

def generate_normalized_score_report(pdt_folder, threshold, output_file, xhtml_dir):
    all_scores = []
    scripture_ref = ScriptureReference('gen 1:1', 'rev 22:21', bible_filename=xhtml_dir, source_type='xhtml')
    verses_dict = {verse[0]: verse[1] for verse in scripture_ref.verses}

    # Iterate through all book folders
    for book_folder in os.listdir(pdt_folder):
        book_path = os.path.join(pdt_folder, book_folder)
        if os.path.isdir(book_path):
            # Iterate through all chapter folders
            for chapter_folder in os.listdir(book_path):
                chapter_path = os.path.join(book_path, chapter_folder)
                if os.path.isdir(chapter_path):
                    # Find the txt file in the chapter folder
                    txt_files = glob.glob(os.path.join(chapter_path, '*_fuzzy_ratios.txt'))
                    if txt_files:
                        txt_file = txt_files[0]
                        # Read and process the txt file
                        with open(txt_file, 'r') as f:
                            for line in f:
                                verse, score = line.strip().split(': ')
                                score = int(score)
                                verse_text = verses_dict.get(verse, "")
                                verse_length = len(verse_text.split())
                                normalized_score = normalize_score(score, verse_length)
                                all_scores.append((verse, normalized_score, score, verse_length))

    # Sort all scores and write the report
    all_scores.sort(key=lambda x: x[1])  # Sort by normalized score
    with open(output_file, 'w') as f:
        f.write(f"All verses with normalized scores:\n\n")
        for verse, norm_score, orig_score, length in all_scores:
            f.write(f"{verse}: {norm_score:.2f} (original: {orig_score}, length: {length})\n")

    print(f"Normalized score report generated: {output_file}")

# Example usage
pdt_folder = "C:/Users/caleb/Bible Translation Project/audio-verse-splitter/audio/output/PDT"
threshold = 80  # Adjust this threshold for normalized scores
output_file = "normalized_low_score_report.txt"
xhtml_dir = 'C:/Users/caleb/Downloads/SPAWTC_palabra_de_dios_para_todos_text/content/chapters'

generate_normalized_score_report(pdt_folder, threshold, output_file, xhtml_dir)