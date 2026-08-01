from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.gemini import improve_bug_report

router = APIRouter()


class AIRequest(BaseModel):
    description: str


@router.post("/ai/improve")
def improve(request: AIRequest):

    improved = improve_bug_report(request.description)

    return {
        "improved_text": improved
    }