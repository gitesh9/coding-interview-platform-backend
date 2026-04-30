import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI
from .prompts import (
    INTERVIEW_SYSTEM_PROMPT,
    INTERVIEW_QUESTION_PROMPT,
    FOLLOW_UP_PROMPT,
    HINT_SYSTEM_PROMPT,
    HINT_PROMPT,
)

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ─── Request schemas ──────────────────────────────────────────────────────────

class AiMessage(BaseModel):
    role: str  # 'interviewer' | 'user'
    content: str


class InterviewQuestionRequest(BaseModel):
    problemContext: str
    conversationHistory: List[AiMessage] = []


class RespondToAnswerRequest(BaseModel):
    userAnswer: str
    problemContext: str
    conversationHistory: List[AiMessage] = []


class HintRequest(BaseModel):
    code: str
    problemDescription: str
    language: str


# ─── Helper ───────────────────────────────────────────────────────────────────

def _format_history(messages: List[AiMessage]) -> str:
    if not messages:
        return "(no conversation yet)"
    lines = []
    for msg in messages:
        label = "Interviewer" if msg.role == "interviewer" else "Candidate"
        lines.append(f"{label}: {msg.content}")
    return "\n".join(lines)


def _chat(system: str, user: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=300,
        temperature=0.7,
    )
    return response.choices[0].message.content or ""


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/interview/question")
def get_interview_question(req: InterviewQuestionRequest):
    prompt = INTERVIEW_QUESTION_PROMPT.format(problem_context=req.problemContext)
    response = _chat(INTERVIEW_SYSTEM_PROMPT, prompt)
    return {"response": response}


@app.post("/interview/respond")
def respond_to_answer(req: RespondToAnswerRequest):
    history_text = _format_history(req.conversationHistory)
    prompt = FOLLOW_UP_PROMPT.format(
        problem_context=req.problemContext,
        conversation_history=history_text,
        user_answer=req.userAnswer,
    )
    response = _chat(INTERVIEW_SYSTEM_PROMPT, prompt)
    return {"response": response}


@app.post("/hint")
def get_hint(req: HintRequest):
    prompt = HINT_PROMPT.format(
        problem_description=req.problemDescription,
        language=req.language,
        code=req.code,
    )
    response = _chat(HINT_SYSTEM_PROMPT, prompt)
    return {"response": response}