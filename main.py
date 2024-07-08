import os
import whisper
from pydub import AudioSegment
from ScriptureReference import ScriptureReference
from fuzzywuzzy import fuzz
import re
import time
import torch

def transcribe_audio_with_timestamps(audio_file, language):
    print("Transcribing audio with timestamps using Whisper...")
    
    # Set the device to the first CUDA device (usually your NVIDIA GPU)
    # device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    # if torch.cuda.is_available():
    #     print(f"Using GPU: {torch.cuda.get_device_name(0)}")
    # else:
    #     print("Using CPU")

    # # Load the Whisper model on the specified device
    # model = whisper.load_model("small", device=device)
    model = whisper.load_model("small")
    result = model.transcribe(audio_file, language=language, word_timestamps=True)
    
    transcribed_words = []
    for segment in result["segments"]:
        for word in segment["words"]:
            transcribed_words.append({
                "word": word["word"].strip().lower(),
                "start": int(word["start"] * 1000),
                "end": int(word["end"] * 1000)
            })
    
    print(f"Transcription complete. Total words: {len(transcribed_words)}")
    # Print full transcription as string
    print(' '.join([w['word'] for w in transcribed_words]))
    

    return transcribed_words

def preprocess_text(text):
    return re.sub(r'\W+', ' ', text.lower()).strip()


def align_verses(transcribed_words, verses, book_name, output_folder, extension_percentage=300):
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

    # visualize_alignment(visualization_data, output_folder)

    

    return alignment


def split_audio(audio_file, alignment, verses, transcribed_words, output_path='audio/output'):
    audio = AudioSegment.from_mp3(audio_file)
    total_duration = len(audio)

    for i, (start, end) in enumerate(alignment):
        start_ms = max(0, transcribed_words[start]['start'])
        
        # For the last verse, capture up to the end of the audio file, unless it exceeds 2 additional seconds
        if i == len(alignment) - 1:
            end_ms = min(total_duration, transcribed_words[min(end-1, len(transcribed_words)-1)]['end'] + 2000)  # Add up to 2 seconds
            end_ms = min(end_ms, total_duration)  # Ensure we don't exceed the total duration
        else:
            end_ms = min(total_duration, transcribed_words[min(end, len(transcribed_words)-1)]['start'])
        
        if start_ms >= end_ms or start_ms >= total_duration or end_ms <= 0:
            print(f"Warning: Invalid time range for verse {verses[i][0]}. Skipping.")
            continue

        verse_audio = audio[start_ms:end_ms]
        
        if len(verse_audio) < 100:  # If the audio segment is less than 100ms, it's probably an error
            print(f"Warning: Very short audio segment for verse {verses[i][0]}. Skipping.")
            continue

        output_filename = f"verse_{verses[i][0]}.mp3".replace(":", "_")
        output_file_path = os.path.join(output_path, output_filename)
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        verse_audio.export(output_file_path, format="mp3")
        
        verse_text = ' '.join([w['word'] for w in transcribed_words[start:min(end, len(transcribed_words))]])
        print(f"Exported {output_filename}: {verses[i][0]} ({end - start} words)")
        print(f"Transcribed text: {verse_text}")
        print(f"Start time: {start_ms}ms, End time: {end_ms}ms")
        print(f"Duration: {end_ms - start_ms}ms")
        print("-" * 80)


def process_single_file(audio_file, verses, language, output_folder):
    transcribed_words = transcribe_audio_with_timestamps(audio_file, language=language)
    if transcribed_words:
        book_name = verses[0][0].split('_')[0]  # Extract book name from the first verse reference
        alignment = align_verses(transcribed_words, verses, book_name, output_folder)
        
        print("\nFinal Alignment:")
        for i, (start, end) in enumerate(alignment):
            print(f"Verse {verses[i][0]}: {start} to {end}")
        
        split_audio(audio_file, alignment, verses, transcribed_words, output_path=output_folder)
    else:
        print(f"Transcription failed for {audio_file}. Unable to proceed with alignment and splitting.")

def process_book_folder(book_folder, verses, language, output_folder):
    book_name = os.path.basename(book_folder)
    current_chapter = None
    chapter_verses = []

    for verse in verses:
        verse_ref = verse[0].split('_')
        if len(verse_ref) < 2 or verse_ref[0] != book_name:
            continue

        try:
            chapter = int(verse_ref[1].split(':')[0])
        except (IndexError, ValueError):
            print(f"Warning: Skipping malformed verse reference: {verse[0]}")
            continue

        if chapter != current_chapter:
            if chapter_verses:
                process_chapter(book_folder, current_chapter, chapter_verses, language, output_folder)
            current_chapter = chapter
            chapter_verses = []
        chapter_verses.append(verse)

    if chapter_verses:
        process_chapter(book_folder, current_chapter, chapter_verses, language, output_folder)

def process_chapter(book_folder, chapter, verses, language, output_folder):
    audio_file = os.path.join(book_folder, f"{chapter}.mp3")
    if os.path.exists(audio_file):
        book_name = os.path.basename(book_folder)
        book_number = ScriptureReference.get_book_number(book_name)
        numbered_book_name = f"{book_number:02d}_{book_name}"
        chapter_output_folder = os.path.join(output_folder, numbered_book_name, str(chapter))
        os.makedirs(chapter_output_folder, exist_ok=True)
        process_single_file(audio_file, verses, language, chapter_output_folder)
    else:
        print(f"Audio file not found for chapter {chapter} in {book_folder}")

def process_multiple_books(audio_folder, verses, language, output_folder):
    current_book = None
    book_verses = []

    for verse in verses:
        book = verse[0].split('_')[0]
        if book != current_book:
            if book_verses:
                book_folder = os.path.join(audio_folder, current_book)
                if os.path.exists(book_folder):
                    process_book_folder(book_folder, book_verses, language, output_folder)
                else:
                    print(f"Book folder not found: {book_folder}")
            current_book = book
            book_verses = []
        book_verses.append(verse)

    if book_verses:
        book_folder = os.path.join(audio_folder, current_book)
        if os.path.exists(book_folder):
            process_book_folder(book_folder, book_verses, language, output_folder)
        else:
            print(f"Book folder not found: {book_folder}")

def main():
    #*******************PARAMETERS*******************#
    language = 'es'  # e.g., 'es' (text and audio language)
    audio_file = 'audio/esp/PDT'  # Can be a file, book folder, or folder containing book folders
    start_verse = 'gen 11:1'  # e.g., 'mat 1:1' (first verse of audio file)
    #errors at lev 5:17 (3583s) num 25
    end_verse = 'rev 22:21'  # e.g., 'jhn 21:25' (last verse of audio file)
    ebible = 'C:/Users/caleb/Downloads/SPAWTC_palabra_de_dios_para_todos_text/content/chapters'  # e.g., 'spa-spaRV1909' (uses eng versification by default)
    bible_type = 'xhtml' # 'ebible'
    audio_output_folder = 'audio/output/PDT' 
    #************************************************#



    start_time = time.time()
    try:
        scripture_ref = ScriptureReference(start_verse, end_verse, bible_filename=ebible, source_type=bible_type)
        verses = scripture_ref.verses

        if os.path.isfile(audio_file):
            # Process single file
            process_single_file(audio_file, verses, language, audio_output_folder)
        elif os.path.isdir(audio_file):
            if any(os.path.isdir(os.path.join(audio_file, d)) for d in os.listdir(audio_file)):
                # Process multiple books
                process_multiple_books(audio_file, verses, language, audio_output_folder)
            else:
                # Process single book folder
                process_book_folder(audio_file, verses, language, audio_output_folder)
        else:
            print(f"Invalid audio_file path: {audio_file}")
    except Exception as e:
        print(f"An error occurred during processing: {str(e)}")
        import traceback
        traceback.print_exc()

    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nTotal execution time: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()