import os
from ScriptureReference import ScriptureReference
from fuzzywuzzy import fuzz
import re

def preprocess_text(text):
    return re.sub(r'\W+', ' ', text.lower()).strip()

def align_verses(transcribed_words, verses, book_name, output_folder, extension_percentage=100):
    alignment = []
    visualization_data = []
    total_chars = sum(len(verse[1]) for verse in verses)
    total_transcribed_words = len(transcribed_words)

    print(f"Total words in transcribed audio: {total_transcribed_words}")
    print(f"Total characters in verses: {total_chars}")
    print(f"Search window extension: {extension_percentage}%")

    cumulative_chars = 0
    fuzzy_ratios = []

    for verse_index, verse in enumerate(verses):
        verse_text = preprocess_text(verse[1])
        verse_char_count = len(verse_text)

        # Calculate relative position and size
        verse_start_ratio = cumulative_chars / total_chars
        verse_end_ratio = (cumulative_chars + verse_char_count) / total_chars

        # Calculate expected start and end indices
        expected_start = int(verse_start_ratio * total_transcribed_words)
        expected_end = int(verse_end_ratio * total_transcribed_words)

        # Calculate search window
        window_size = expected_end - expected_start
        extension = int(window_size * (extension_percentage / 100))
        if verse_index == 0:
            extension *= 2  # Double extension for the first verse

        start_window = max(0, expected_start - extension)
        end_window = min(total_transcribed_words, expected_end + extension)

        # Compensate if boundaries are reached
        if start_window == 0:
            end_window = min(total_transcribed_words, end_window + (expected_start - start_window))
        if end_window == total_transcribed_words:
            start_window = max(0, start_window - (end_window - expected_end))

        print(f"\nAligning Verse {verse[0]}:")
        print(f"Expected start: {expected_start}, Expected end: {expected_end}")
        print(f"Search window: {start_window} to {end_window}")

        best_ratio = 0
        best_start_index = start_window
        best_end_index = min(start_window + window_size, end_window)

        for start in range(start_window, end_window - 1):
            for end in range(start + 1, end_window):
                window = ' '.join([w['word'] for w in transcribed_words[start:end]])
                ratio = fuzz.ratio(window, verse_text)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_start_index = start
                    best_end_index = end

        if best_ratio == 0:
            print("No good match found. Using expected positions.")
            best_start_index = expected_start
            best_end_index = expected_end

        alignment.append((best_start_index, best_end_index))
        cumulative_chars += verse_char_count

        aligned_text = ' '.join([w['word'] for w in transcribed_words[best_start_index:best_end_index]])
        print(f"Best ratio: {best_ratio}")
        print(f"Aligned text: {aligned_text}")
        print(f"Actual text: {verse_text}")
        print("-" * 80)

        fuzzy_ratios.append(f"{verse[0]}: {best_ratio}")
        
        # Store visualization data
        visualization_data.append({
            'verse_ref': verse[0],
            'verse_text': verse_text,
            'start_window': start_window,
            'end_window': end_window,
            'best_start': best_start_index,
            'best_end': best_end_index,
            'transcribed_words': transcribed_words
        })

        # In the align_verses function, just before appending to visualization_data
        print(f"Debug - Verse {verse[0]}:")
        print(f"Start window: {start_window}, End window: {end_window}")
        print(f"Best start: {best_start_index}, Best end: {best_end_index}")
        print(f"Aligned text: {aligned_text}")

    book_number = ScriptureReference.get_book_number(book_name)
    numbered_book_name = f"{book_number:02d}_{book_name}"
    fuzzy_file_path = os.path.join(output_folder, f"{numbered_book_name}_fuzzy_ratios.txt")
    os.makedirs(os.path.dirname(fuzzy_file_path), exist_ok=True)
    with open(fuzzy_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fuzzy_ratios))

    visualize_alignment(visualization_data, output_folder)

    

    return alignment

def visualize_alignment(visualization_data, output_folder, context_size=20):
    visualization = []
    for data in visualization_data:
        verse_ref = data['verse_ref']
        verse_text = data['verse_text']
        start_window = data['start_window']
        end_window = data['end_window']
        best_start = data['best_start']
        best_end = data['best_end']
        transcribed_words = data['transcribed_words']

        # Get context around the aligned portion
        context_start = max(0, start_window - context_size)
        context_end = min(len(transcribed_words), end_window + context_size)
        context_words = transcribed_words[context_start:context_end]
        context = ' '.join([w['word'] for w in context_words])

        # Calculate character positions
        char_positions = [0]
        for word in context_words:
            char_positions.append(char_positions[-1] + len(word['word']) + 1)  # +1 for space

        # Calculate relative positions for visualization
        rel_start_window = char_positions[start_window - context_start] if start_window >= context_start else 0
        rel_end_window = char_positions[end_window - context_start] if end_window <= context_end else len(context)
        rel_best_start = char_positions[best_start - context_start] if best_start >= context_start else 0
        rel_best_end = char_positions[best_end - context_start] if best_end <= context_end else len(context)

        # Create visualization lines
        v_ref = f"v_ref: {verse_text}"
        start_line = ' ' * rel_start_window + 's' * (rel_end_window - rel_start_window)
        end_line = ' ' * rel_start_window + 'e' * (rel_end_window - rel_start_window)
        align_line = ' ' * rel_best_start + 's' + '-' * (rel_best_end - rel_best_start - 2) + 'e'

        # Add to visualization list
        visualization.extend([
            v_ref,
            start_line,
            end_line,
            context,
            align_line,
            ''  # Empty line for separation
        ])

    # Save visualization to file
    book_name = visualization_data[0]['verse_ref'].split('_')[0]
    book_number = ScriptureReference.get_book_number(book_name)
    numbered_book_name = f"{book_number:02d}_{book_name}"
    vis_file_path = os.path.join(output_folder, f"{numbered_book_name}_alignment_visualization.txt")
    os.makedirs(os.path.dirname(vis_file_path), exist_ok=True)
    with open(vis_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(visualization))

    print(f"Alignment visualization saved to: {vis_file_path}")


def main():
    # Parameters
    start_verse = 'gen 10:1'
    end_verse = 'gen 10:32'
    ebible = 'C:/Users/caleb/Downloads/SPAWTC_palabra_de_dios_para_todos_text/content/chapters'
    bible_type = 'xhtml'
    output_folder = 'test_output'
    extension_percentage = 300

    # Load pre-existing transcription
    with open('transcription.txt', 'r', encoding='utf-8') as f:
        transcription = f.read()

    # Convert transcription string to list of word dictionaries
    transcribed_words = [{'word': word} for word in transcription.split()]

    # Get verses using ScriptureReference
    scripture_ref = ScriptureReference(start_verse, end_verse, bible_filename=ebible, source_type=bible_type)
    verses = scripture_ref.verses

    # Run align_verses function
    book_name = verses[0][0].split('_')[0]
    alignment = align_verses(transcribed_words, verses, book_name, output_folder, extension_percentage)

    # Print final alignment
    print("\nFinal Alignment:")
    for i, (start, end) in enumerate(alignment):
        print(f"Verse {verses[i][0]}: {start} to {end}")

if __name__ == "__main__":
    main()