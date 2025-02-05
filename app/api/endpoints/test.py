from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette import status
import os
from datetime import datetime


router = APIRouter()


@router.get("/test", status_code=status.HTTP_200_OK)
async def test():
    return "Health check successful"