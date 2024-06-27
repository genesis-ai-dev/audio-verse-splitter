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
audio_file = 'audio/esp/MAT/1.mp3' # Input audio file
start_verse = 'mat 1:1' # First verse
end_verse = 'mat 1:25' # Last verse
ebible = 'spa-spaRV1909' # Bible version
audio_output_folder = 'audio/output' # Output directory
```

Run:

```bash
python main.py
```

## Process

1. Transcribes audio using Whisper
2. Aligns transcription with expected verse text
3. Splits audio into individual verse files

