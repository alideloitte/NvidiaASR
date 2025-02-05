from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import FileResponse
from starlette import status
import os
from models.tts_model import SpeechWrapper
from pathlib import Path
import soundfile as sf


router = APIRouter()


class TextRequest(BaseModel):
    text: str


tmp_file_dir = "/tmp/audio-files"
Path(tmp_file_dir).mkdir(parents=True, exist_ok=True)

tts_model = SpeechWrapper()

@router.post("/tts", response_class = FileResponse)
async def tts(request: TextRequest):
    request = TextRequest(**request.model_dump())

    audio = tts_model.infer(request.text)

    # Write file to disk. This simulates some business logic that results in a file sotred on disk
    with open(os.path.join(tmp_file_dir, "audio.wav"), "wb") as disk_file:
        #file_bytes = await file.read()
        print(disk_file)
        sf.write(disk_file, audio, 22050)

        print(f"Received file named audio.wav.")

        return FileResponse(disk_file.name, media_type="audio/wave")
