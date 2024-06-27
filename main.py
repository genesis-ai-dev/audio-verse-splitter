import os
import whisper
from pydub import AudioSegment
from ScriptureReference import ScriptureReference
from fuzzywuzzy import fuzz
import re
import time


def transcribe_audio_with_timestamps(audio_file, language):
    print("Transcribing audio with timestamps using Whisper...")
    model = whisper.load_model("base")
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
    return transcribed_words

def preprocess_text(text):
    return re.sub(r'\W+', ' ', text.lower()).strip()

def align_verses(transcribed_words, verses):
    alignment = []
    total_words = sum(len(verse[1].split()) for verse in verses)
    total_duration = transcribed_words[-1]['end'] - transcribed_words[0]['start']
    avg_time_per_word = total_duration / total_words

    cumulative_words = 0
    for i, verse in enumerate(verses):
        verse_text = preprocess_text(verse[1])
        verse_words = verse_text.split()
        verse_word_count = len(verse_words)

        # Calculate expected start and end times
        expected_start = (cumulative_words / total_words) * total_duration
        expected_end = ((cumulative_words + verse_word_count) / total_words) * total_duration

        # Define search window
        window_size = verse_word_count * avg_time_per_word * 2  # Double the expected size for flexibility
        start_window = max(0, int((expected_start - window_size) / avg_time_per_word))
        end_window = min(len(transcribed_words), int((expected_end + window_size) / avg_time_per_word))

        print(f"\nAligning Verse {verse[0]}:")
        print(f"Expected start: {expected_start:.2f}ms, Expected end: {expected_end:.2f}ms")
        print(f"Search window: {start_window} to {end_window}")

        best_start_ratio = 0
        best_end_ratio = 0
        best_start_index = start_window
        best_end_index = min(start_window + verse_word_count, end_window)

        # Slide window to find best start
        for i in range(start_window, end_window - verse_word_count + 1):
            window = ' '.join([w['word'] for w in transcribed_words[i:i+verse_word_count]])
            ratio = fuzz.partial_ratio(window, verse_text)
            if ratio > best_start_ratio:
                best_start_ratio = ratio
                best_start_index = i

        # Slide end of window to find best end
        min_end = best_start_index + verse_word_count // 2
        max_end = min(best_start_index + int(verse_word_count * 1.5), end_window)
        for j in range(min_end, max_end):
            window = ' '.join([w['word'] for w in transcribed_words[best_start_index:j]])
            ratio = fuzz.ratio(window, verse_text)
            if ratio > best_end_ratio:
                best_end_ratio = ratio
                best_end_index = j

        if best_start_ratio == 0 or best_end_ratio == 0:
            # Fallback: use the expected start and end
            best_start_index = max(0, min(int(expected_start / avg_time_per_word), len(transcribed_words) - 1))
            best_end_index = max(best_start_index + 1, min(int(expected_end / avg_time_per_word), len(transcribed_words)))
            print("No good match found. Using expected positions.")

        alignment.append((best_start_index, best_end_index))
        cumulative_words += verse_word_count

        aligned_text = ' '.join([w['word'] for w in transcribed_words[best_start_index:best_end_index]])
        print(f"Best start ratio: {best_start_ratio}, Best end ratio: {best_end_ratio}")
        print(f"Aligned text: {aligned_text}")
        print(f"Actual text: {verse_text}")
        print("-" * 80)

    return alignment

def split_audio(audio_file, alignment, verses, transcribed_words, output_path='audio/output'):
    audio = AudioSegment.from_mp3(audio_file)
    total_duration = len(audio)

    for i, (start, end) in enumerate(alignment):
        start_ms = max(0, transcribed_words[start]['start'])
        
        # For the last verse, capture up to the end of the audio file, unless it exceeds 2 additional seconds
        if i == len(alignment) - 1:
            end_ms = min(total_duration, transcribed_words[end-1]['end'] + 2000)  # Add up to 2 seconds
            end_ms = min(end_ms, total_duration)  # Ensure we don't exceed the total duration
        else:
            end_ms = min(total_duration, transcribed_words[end]['start'])
        
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
        
        verse_text = ' '.join([w['word'] for w in transcribed_words[start:end]])
        print(f"Exported {output_filename}: {verses[i][0]} ({end - start} words)")
        print(f"Transcribed text: {verse_text}")
        print(f"Start time: {start_ms}ms, End time: {end_ms}ms")
        print(f"Duration: {end_ms - start_ms}ms")
        print("-" * 80)


def process_single_file(audio_file, verses, language, output_folder):
    transcribed_words = transcribe_audio_with_timestamps(audio_file, language=language)
    if transcribed_words:
        alignment = align_verses(transcribed_words, verses)
        
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
        if verse_ref[0] != book_name:
            continue

        chapter = int(verse_ref[1].split(':')[0])
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
    audio_file = 'audio/esp'  # Can be a file, book folder, or folder containing book folders
    start_verse = 'nam 1:1'  # e.g., 'mat 1:1' (first verse of audio file)
    end_verse = 'zep 3:20'  # e.g., 'jhn 21:25' (last verse of audio file)
    ebible = 'spa-spaRV1909'  # e.g., 'spa-spaRV1909' (uses eng versification by default)
    audio_output_folder = 'audio/output' 
    #************************************************#

    start_time = time.time()
    try:
        scripture_ref = ScriptureReference(start_verse, end_verse, bible_filename=ebible)
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