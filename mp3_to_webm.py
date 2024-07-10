import os
import subprocess
from pathlib import Path

def convert_mp3_to_webm(input_dir, output_dir, start_book_number):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for root, dirs, files in os.walk(input_dir):
        # Filter out directories that start with a number followed by an underscore and are less than start_book_number
        dirs[:] = [d for d in dirs if not (d.split('_')[0].isdigit() and '_' in d and int(d.split('_')[0]) < start_book_number)]
        
        for file in files:
            if file.lower().endswith('.mp3'):
                input_path = os.path.join(root, file)
                relative_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, os.path.splitext(relative_path)[0] + '.webm')

                Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)

                # Redirect stdout and stderr to devnull
                with open(os.devnull, 'w') as devnull:
                    subprocess.run(
                        ['ffmpeg', '-i', input_path, '-c:a', 'libopus', output_path],
                        stdout=devnull,
                        stderr=devnull
                    )

                # print(f"Converted: {input_path} -> {output_path}")

# Example usage
input_directory = 'C:/Users/caleb/Bible Translation Project/audio-verse-splitter/audio/output/PDT'
output_directory = 'C:/Users/caleb/Bible Translation Project/audio-verse-splitter/audio/output/PDT_webm'
start_book_number = 24
convert_mp3_to_webm(input_directory, output_directory, start_book_number)