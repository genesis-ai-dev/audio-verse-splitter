from modal import Image, App, method, asgi_app
from fastapi import FastAPI, Request
import tempfile
import os

app = App("whisper-transcription")
web_app = FastAPI()

def download_whisper_model():
    import whisper
    whisper.load_model("small")

image = (
    Image.debian_slim(python_version="3.10")
    .apt_install("ffmpeg")
    .pip_install("openai-whisper", "torch", "fastapi", "uvicorn")
    .run_function(download_whisper_model)
)

@app.function(image=image, gpu="A100", timeout=600)
def transcribe_audio(audio_bytes: bytes, language: str):
    import whisper
    import torch

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name

    model = whisper.load_model("small", device="cuda" if torch.cuda.is_available() else "cpu")
    result = model.transcribe(temp_audio_path, language=language)
    os.remove(temp_audio_path)
    return result["text"]

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