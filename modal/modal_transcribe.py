from modal import Image, App, method, asgi_app
from fastapi import FastAPI, Request
import tempfile
import os
import io

app = App("audio-transcription")
web_app = FastAPI()

TRANSCRIPTION_MODEL = 'w2v2p' # os.getenv('TRANSCRIPTION_MODEL', 'whisper')  # Default to whisper if not set

def download_models():
    if TRANSCRIPTION_MODEL == 'whisper':
        import whisper
        whisper.load_model("small")
    else:
        from transformers import Wav2Vec2ForCTC, Wav2Vec2CTCTokenizer
        Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-xlsr-53-espeak-cv-ft")
        Wav2Vec2CTCTokenizer.from_pretrained("facebook/wav2vec2-xlsr-53-espeak-cv-ft")

image = (
    Image.debian_slim(python_version="3.10")
    .apt_install("ffmpeg")
    .pip_install("openai-whisper", "torch", "fastapi", "uvicorn", "transformers", "librosa", "soundfile", "pydub")
    .run_function(download_models)
)

@app.function(image=image, gpu="A100", timeout=600)
def transcribe_audio(audio_bytes: bytes, language: str):
    if TRANSCRIPTION_MODEL == 'whisper':
        import whisper
        import torch

        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name

        model = whisper.load_model("small", device="cuda" if torch.cuda.is_available() else "cpu")
        result = model.transcribe(temp_audio_path, language=language)
        os.remove(temp_audio_path)
        return result["text"]
    else:
        import torch
        import librosa
        import soundfile as sf
        from transformers import Wav2Vec2ForCTC, Wav2Vec2CTCTokenizer
        from pydub import AudioSegment

        # Convert audio to WAV
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            audio.export(temp_audio.name, format="wav")
            temp_audio_path = temp_audio.name

        # Load audio
        audio, sr = librosa.load(temp_audio_path, sr=16000)
        os.remove(temp_audio_path)

        model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-xlsr-53-espeak-cv-ft")
        tokenizer = Wav2Vec2CTCTokenizer.from_pretrained("facebook/wav2vec2-xlsr-53-espeak-cv-ft")

        input_values = tokenizer(audio, return_tensors="pt").input_values

        with torch.no_grad():
            logits = model(input_values).logits

        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = tokenizer.batch_decode(predicted_ids)[0]
        return transcription

@app.function()
@asgi_app()
def fastapi_app():
    return web_app

@web_app.post("/transcribe")
async def transcribe(request: Request):
    form = await request.form()
    audio = await form["audio"].read()
    language = form["language"]
    transcription = transcribe_audio.remote(audio, language)
    return {"transcription": transcription}