from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette import status
from fastapi import File, UploadFile
from models.asr_model import TranscriptionWrapper
from pathlib import Path
import os

router = APIRouter()

tmp_file_dir = "/tmp/audio-files"
Path(tmp_file_dir).mkdir(parents=True, exist_ok=True)

asr_model = TranscriptionWrapper("nvidia/canary-1b")

@router.post("/asr", status_code=status.HTTP_200_OK)
async def asr(audio_file: UploadFile = File(...)):
    print("audio_file: ", audio_file.filename)
    with open(os.path.join(tmp_file_dir, audio_file.filename), 'wb') as disk_file:
        file_bytes = await audio_file.read()

        disk_file.write(file_bytes)

        print(f"Received file named {audio_file.filename} containing {len(file_bytes)} bytes. ")
        transcripted_text = asr_model.transcribe(disk_file.name)

        return JSONResponse(content=transcripted_text)