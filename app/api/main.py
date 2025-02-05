from fastapi import FastAPI
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import audio_to_text, chatbot, test

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audio_to_text.router)
app.include_router(chatbot.router)
app.include_router(test.router)

handler = Mangum(app)