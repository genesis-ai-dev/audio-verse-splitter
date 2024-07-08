import os
import glob

def generate_low_score_report(pdt_folder, threshold, output_file):
    low_scores = []

    # Iterate through all book folders
    for book_folder in os.listdir(pdt_folder):
        book_path = os.path.join(pdt_folder, book_folder)
        if os.path.isdir(book_path):
            # Iterate through all chapter folders
            for chapter_folder in os.listdir(book_path):
                chapter_path = os.path.join(book_path, chapter_folder)
                if os.path.isdir(chapter_path):
                    # Find the txt file in the chapter folder
                    txt_files = glob.glob(os.path.join(chapter_path, '*.txt'))
                    if txt_files:
                        txt_file = txt_files[0]
                        # Read and process the txt file
                        with open(txt_file, 'r') as f:
                            for line in f:
                                verse, score = line.strip().split(': ')
                                score = int(score)
                                if score < threshold:
                                    low_scores.append(f"{verse}: {score}")

    # Write the report
    with open(output_file, 'w') as f:
        f.write(f"Verses with scores below {threshold}:\n\n")
        for item in low_scores:
            f.write(f"{item}\n")

    print(f"Report generated: {output_file}")

# Example usage
pdt_folder = "C:/Users/caleb/Bible Translation Project/audio-verse-splitter/audio/output/PDT"
threshold = 90
output_file = "low_score_report.txt"

generate_low_score_report(pdt_folder, threshold, output_file)