import os
import secrets
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

import scoring
import speaking

API_KEY = os.getenv("SCORING_API_KEY", "dev-key")


def auth(x_api_key: str = Header(default="")):
    if not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")


app = FastAPI(title="IELTS Mock Scoring API")


class ObjectiveIn(BaseModel):
    section: Literal["reading", "listening"]
    correct: int = Field(ge=0)
    total: int = Field(gt=0)


class OverallIn(BaseModel):
    bands: list[float] = Field(min_length=1, max_length=4)


class SpeakingIn(BaseModel):
    prompt: str
    transcript: str = Field(max_length=8000)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/score/objective", dependencies=[Depends(auth)])
def score_objective(data: ObjectiveIn):
    if data.correct > data.total:
        raise HTTPException(422, "correct cannot exceed total")
    raw40 = scoring.to_raw40(data.correct, data.total)
    band = scoring.raw_to_band(data.section, raw40)
    return {"raw40": raw40, "band": band, "cefr": scoring.band_to_cefr(band)}


@app.post("/score/overall", dependencies=[Depends(auth)])
def score_overall(data: OverallIn):
    value = scoring.overall(data.bands)
    return {"overall": value, "cefr": scoring.band_to_cefr(value)}


@app.post("/speaking/evaluate", dependencies=[Depends(auth)])
def evaluate_speaking(data: SpeakingIn):
    result = speaking.evaluate(data.prompt, data.transcript)
    result["cefr"] = scoring.band_to_cefr(result["band"])
    return result
