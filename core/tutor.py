import json
import os
from typing import Any

from dotenv import load_dotenv
from PyQt6.QtCore import QThread, pyqtSignal

load_dotenv()

SYSTEM_PROMPT = """Ești un profesor de engleză prietenos pentru vorbitori de română. Numele tău este Alex.

REGULI:
1. Conversezi ÎNTOTDEAUNA în engleză cu utilizatorul
2. Dacă utilizatorul scrie în română, răspunzi în engleză și îl încurajezi să continue în engleză
3. Analizezi fiecare mesaj pentru greșeli gramaticale, vocabular și sintaxă
4. Ești mereu încurajator și pozitiv

Returnează MEREU un JSON valid cu această structură:
{
  "reply": "răspunsul tău în engleză",
  "feedback": {
    "positive": "ce a făcut bine (în română, max 2 propoziții)",
    "correction": "corecție dacă există greșeli (în română) sau null",
    "tip": "sfat util de gramatică/vocabular (în română)"
  },
  "level": "beginner|elementary|intermediate|upper-intermediate|advanced",
  "newWords": ["word1", "word2"],
  "goals": ["obiectiv1", "obiectiv2", "obiectiv3"]
}"""


def _parse_response(raw: str) -> dict[str, Any]:
    """Parse JSON from AI response; fall back to raw text reply on failure."""
    raw = raw.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "reply": raw,
            "feedback": {"positive": "", "correction": None, "tip": ""},
            "level": "beginner",
            "newWords": [],
            "goals": [],
        }


class TutorWorker(QThread):
    """Background thread that calls the Anthropic API and emits results."""

    response_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, history: list[dict], parent=None):
        super().__init__(parent)
        self._history = history

    def run(self) -> None:
        try:
            import anthropic  # imported here to allow offline startup

            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            if not api_key or api_key.startswith("sk-ant-your"):
                self.error_occurred.emit(
                    "⚠️  No valid ANTHROPIC_API_KEY found. Please set it in your .env file."
                )
                return

            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=self._history,
            )
            raw = message.content[0].text
            parsed = _parse_response(raw)
            self.response_ready.emit(parsed)
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"⚠️  API error: {exc}")
