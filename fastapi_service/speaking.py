"""Speaking evaluation: Claude when ANTHROPIC_API_KEY is set, otherwise a rough heuristic."""
import json
import os
import re

import scoring

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
SYSTEM = (
    "You are an IELTS speaking examiner. You receive the question and a transcript of the "
    "candidate's answer. Score four criteria from 0 to 9 in 0.5 steps: fluency, vocabulary, "
    "grammar, pronunciation. Pronunciation cannot be judged from text, so estimate it "
    "conservatively and say so. Reply with JSON only, no markdown: "
    '{"fluency":6.0,"vocabulary":6.0,"grammar":6.0,"pronunciation":6.0,'
    '"strengths":["..."],"improvements":["..."]}'
)


def _clean(value) -> float:
    return scoring.round_band(max(0.0, min(9.0, float(value))))


def _finish(c: dict, source: str) -> dict:
    keys = ("fluency", "vocabulary", "grammar", "pronunciation")
    scores = {k: _clean(c[k]) for k in keys}
    return {
        **scores,
        "band": scoring.overall(list(scores.values())),
        "strengths": list(c.get("strengths", []))[:3],
        "improvements": list(c.get("improvements", []))[:3],
        "source": source,
    }


def heuristic(transcript: str) -> dict:
    words = re.findall(r"[A-Za-z']+", transcript.lower())
    n = len(words)
    if n < 15:
        base = {k: 3.0 for k in ("fluency", "vocabulary", "grammar", "pronunciation")}
        base["improvements"] = ["Answer is very short. Speak for the full time."]
        return _finish(base, "heuristic")
    length = min(n / 150, 1)
    variety = min((len(set(words)) / n) / 0.6, 1)
    sentences = max(1, len(re.findall(r"[.!?]", transcript)))
    sentence_len = n / sentences
    grammar = 4 + 3 * (1 if 8 <= sentence_len <= 22 else 0.5)
    fluency = 4 + 3 * length
    return _finish({
        "fluency": fluency,
        "vocabulary": 4 + 3 * variety,
        "grammar": grammar,
        "pronunciation": fluency,
        "strengths": ["You gave a developed answer."] if length > 0.6 else [],
        "improvements": ["Rough estimate from text only. Use the AI evaluator for better feedback."],
    }, "heuristic")


def evaluate(prompt: str, transcript: str) -> dict:
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            import anthropic

            client = anthropic.Anthropic()
            msg = client.messages.create(
                model=MODEL, max_tokens=600, system=SYSTEM,
                messages=[{"role": "user", "content": f"Question:\n{prompt}\n\nTranscript:\n{transcript}"}],
            )
            text = msg.content[0].text.strip()
            text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
            return _finish(json.loads(text), "claude")
        except Exception:
            pass
    return heuristic(transcript)
