from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette import status
from fastapi import File, UploadFile
from app.agents.agent_main import main
from app.services.asr_tts_invocation import call_asr_endpoint
import os
from dotenv import load_dotenv

load_dotenv("config/.env")

router = APIRouter()

ASR_ENDPOINT = os.environ["ASR_ENDPOINT"]


@router.post("/audio-to-text", status_code=status.HTTP_200_OK)
async def audio_to_text(audio_file: UploadFile = File(...)):
    print("entrou no audio_to_text endpoint")
    transcripted_text = call_asr_endpoint(ASR_ENDPOINT, audio_file.filename, audio_file.file)
    print("transcripted_text: ", transcripted_text)

    return transcripted_text