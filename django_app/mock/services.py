"""Client for the FastAPI scoring service. Every call returns None on failure."""
import requests
from django.conf import settings


def _post(path, payload, timeout):
    try:
        response = requests.post(
            f"{settings.SCORING_API_URL}{path}",
            json=payload,
            headers={"X-API-Key": settings.SCORING_API_KEY},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return None


def score_objective(section, correct, total):
    return _post("/score/objective", {"section": section, "correct": correct, "total": total},
                 settings.SCORING_API_TIMEOUT)


def score_overall(bands):
    return _post("/score/overall", {"bands": [float(b) for b in bands]}, settings.SCORING_API_TIMEOUT)


def evaluate_speaking(prompt, transcript):
    return _post("/speaking/evaluate", {"prompt": prompt, "transcript": transcript},
                 settings.SPEAKING_API_TIMEOUT)
