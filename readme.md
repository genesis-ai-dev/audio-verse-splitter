# Bible Audio Verse Splitter

Transcribes audio Bible chapters and splits them into individual verse audio files.

## Setup

```bash
pip install openai-whisper pydub fuzzywuzzy
```

## Usage

Edit parameters in `main.py`:

```python
language = 'es' # Audio language
audio_file = 'audio/esp/MAT/1.mp3' # Can point to audio file, folder containing files, or folder containing book folders containing files
start_verse = 'mat 1:1' # First verse (of input audio file)
end_verse = 'mat 1:25' # Last verse (of input audio file)
ebible = 'spa-spaRV1909' # Bible version (must be same translation as audio)
audio_output_folder = 'audio/output' # Output directory (will automatically create folders for books/chapters if needed)
```

Run:

```bash
python main.py
```

## Process

1. Transcribes audio using Whisper
2. Aligns transcription with expected verse text
3. Splits audio file(s) into individual verse files

