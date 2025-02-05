from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from endpoints import asr, tts

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(asr.router)
app.include_router(tts.router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
