from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette import status
import os
from fastapi import File, UploadFile
from datetime import datetime
from app.agents.agent_main import main
import openai
import logging
import time
import base64
from dotenv import load_dotenv

from app.services.asr_tts_invocation import call_tts_endpoint
from app.utils.text_treatment import find_and_replace_acronyms, remove_angle_brackets_and_content, punctuate_text

load_dotenv("config/.env")

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

TTS_ENDPOINT = os.environ["TTS_ENDPOINT"]

class RequestModel(BaseModel):
    user_input: str
    state: dict
    history: list[dict]
    audio_output: str


@router.post("/chatbot", status_code=status.HTTP_200_OK)
async def chatbot(request: RequestModel):
    start = time.time()
    request = RequestModel(**request.model_dump())

    logger.warning("\n\n\n***USER QUERY RECEIVED***\n")
    logger.warning(f"""USER: {request.user_input}""")

    try:
        if request.audio_output == "false":
            response = main(request.user_input, request.state, request.history)
            response["audio_response"] = ""
        else:
            response = main(request.user_input, request.state, request.history)
            treated_text = find_and_replace_acronyms(response.get("output_to_user"))
            treated_text = remove_angle_brackets_and_content(treated_text)
            treated_text = punctuate_text(treated_text)
            print("treated_text: ", treated_text)
            audio_bin = call_tts_endpoint(TTS_ENDPOINT, treated_text)
            audio_data = base64.b64encode(audio_bin).decode('utf-8')
            response["audio_response"] = audio_data
            
    except openai.BadRequestError as e:
        logger.exception(f"OpenAI BAD REQUEST error {e.status_code}: {e.response}")
        return {
            "history": request.history,
            "output_to_user": "Not valid. Please reformulate your input.",
            "state": request.state,
            "audio_response": ""
        }
    except AttributeError as e:
        logger.exception(f"Unknown error occurred: AttributeError {e}")
        logger.error("Unknown error occurred: AttributeError ", exc_info=e)
        return {
            "history": request.history,
            "output_to_user": "An error occurred. Please reformulate your request.",
            "state": request.state,
            "audio_response": ""
        }
    except Exception as e:
        logger.exception(f"Unknown error occurred: {e}")
        logger.error("Unknown error occurred: ", exc_info=e)
        return {
            "history": request.history,
            "output_to_user": "An error occurred. Please try again.",
            "state": request.state,
            "audio_response": ""
        }

    logger.warning("\n\n\n***RESPONSE***\n")

    logger.warning(f"""\nHISTORY: {response.get("history")}""")
    logger.warning(f"""\nSTATE: {response.get("state")}""")
    logger.warning(f"""\nAI: {response.get("output_to_user")}""")

    logger.warning(f"\n*** Time: {time.time()-start}***\n")

    return JSONResponse(content=response)
