import os
from pydub import AudioSegment
import speech_recognition as sr
# from dtaidistance import dtw
import difflib
import numpy as np
from ScriptureReference import ScriptureReference
import re
import speech_recognition as sr
from fuzzywuzzy import fuzz

def transcribe_audio(audio_file):
    print("Transcribing audio...")
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_mp3(audio_file)
    
    # Split audio into 30-second chunks for better transcription
    chunk_length_ms = 30000
    chunks = [audio[i:i+chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    
    transcribed_text = []
    for i, chunk in enumerate(chunks):
        chunk.export("temp_chunk.wav", format="wav")
        with sr.AudioFile("temp_chunk.wav") as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data) # , language="es-ES"
                transcribed_text.append(text)
                print(f"Chunk {i+1}: {text}")
            except sr.UnknownValueError:
                print(f"Chunk {i+1}: Could not understand audio")
            except sr.RequestError as e:
                print(f"Chunk {i+1}: Could not request results; {e}")
    
    os.remove("temp_chunk.wav")
    return " ".join(transcribed_text)

def preprocess_text(text):
    return re.sub(r'\W+', ' ', text.lower()).strip()

def align_verses(transcribed_text, verses):
    transcribed_words = transcribed_text.lower().split()
    alignment = []
    start_index = 0

    for verse in verses:
        verse_text = preprocess_text(verse[1])
        verse_words = verse_text.split()
        best_ratio = 0
        best_index = start_index
        window_size = len(verse_words) * 2  # Increase window size for better matching

        for i in range(start_index, min(len(transcribed_words) - len(verse_words) + 1, start_index + window_size)):
            window = ' '.join(transcribed_words[i:i+len(verse_words)])
            ratio = fuzz.ratio(window, verse_text)
            if ratio > best_ratio:
                best_ratio = ratio
                best_index = i

        end_index = min(best_index + len(verse_words), len(transcribed_words))
        alignment.append((best_index, end_index))
        start_index = end_index

    return alignment

def split_audio(audio_file, alignment, verses, transcribed_text, offset_ms=1000):
    audio = AudioSegment.from_mp3(audio_file)
    transcribed_words = transcribed_text.lower().split()
    total_duration = len(audio)
    total_words = len(transcribed_words)
    ms_per_word = total_duration / total_words

    for i, (start, end) in enumerate(alignment):
        start_ms = int(start * ms_per_word)
        end_ms = int(end * ms_per_word)
        
        # Apply the offset
        start_ms = max(0, start_ms + offset_ms)
        end_ms = min(total_duration, end_ms + offset_ms)
        
        # Add a small buffer to the start and end times
        # start_ms = max(0, start_ms - 500)  # 500ms buffer at the start
        end_ms = min(total_duration, end_ms + 500)  # 500ms buffer at the end
        
        verse_audio = audio[start_ms:end_ms]
        output_filename = f"verse_{i+1}.mp3"
        verse_audio.export(f'audio/output/{output_filename}', format="mp3")
        
        # Print the transcribed text for this verse
        verse_text = ' '.join(transcribed_words[start:end])
        print(f"Exported {output_filename}: {verses[i][0]} ({end - start} words)")
        print(f"Transcribed text: {verse_text}")
        print(f"Start time: {start_ms}ms, End time: {end_ms}ms")
        print("-" * 80)  # Separator for readability

def main():
    audio_file = "audio/eng/bible_090_asv_64kb.mp3" #"audio/esp/MAT/1.mp3"
    transcribed_text = transcribe_audio(audio_file)
    verses = ScriptureReference('mal 1:1', 'mal 4:6', bible_filename='eng-eng-asv').verses # spa-spaRV1909
    alignment = align_verses(transcribed_text, verses)
    split_audio(audio_file, alignment, verses, transcribed_text, offset_ms=0)  # Adjust the offset as needed

if __name__ == "__main__":
    main()