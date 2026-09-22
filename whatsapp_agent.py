#!/usr/bin/env python3
"""
WhatsApp AI Agent — portfolio practice project.

Starter for the "WhatsApp AI knowledge agent" gig pattern:
Twilio WhatsApp webhook + knowledge-base retrieval + human handoff.

How it works (Flask, stdlib + flask only):
  * POST /whatsapp/incoming — Twilio webhook; expects form fields
    From (sender id) and Body (message text). Replies with TwiML.
  * Per-sender conversation state in memory (resets on "reset").
  * Retrieval: keyword-overlap scoring over documents/*.txt|*.md —
    the same idea as a vector DB, simplified so the demo runs with
    zero API keys. README explains the pgvector upgrade path.
  * Says "human" (or low confidence) -> human handoff message.

Usage:
    pip install -r requirements.txt
    python whatsapp_agent.py          # http://localhost:5000
    python tests/test_whatsapp_agent.py

Point a Twilio WhatsApp number's webhook at /whatsapp/incoming.
"""

import re
from collections import Counter
from pathlib import Path

from flask import Flask, request, Response

BASE = Path(__file__).resolve().parent
DOCS_DIR = BASE / "documents"

# TODO(learn): replace keyword scoring with embeddings + pgvector and
# compare answer relevance on 10 sample questions.

STOPWORDS = set("""a an the and or of to in is are was were be on for with as at by
from that this it its we you your our they their he she his her not no yes do does
did can could will would should what when where which who how why i me my""".split())


def tokenize(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower())
            if w not in STOPWORDS]


def load_passages():
    """Split each doc into ~3-sentence passages with their source file."""
    passages = []
    for path in sorted(DOCS_DIR.glob("*")):
        if path.suffix.lower() not in (".txt", ".md") or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        for i in range(0, len(sentences), 3):
            chunk = " ".join(sentences[i:i + 3])
            if chunk:
                passages.append({"source": path.name, "text": chunk})
    return passages


def retrieve(question, passages, top_k=2):
    """Rank passages by keyword overlap with the question."""
    q_terms = Counter(tokenize(question))
    scored = []
    for p in passages:
        p_terms = Counter(tokenize(p["text"]))
        score = sum(min(q_terms[t], p_terms[t]) for t in q_terms)
        scored.append((score, p))
    scored.sort(key=lambda s: s[0], reverse=True)
    return [p for score, p in scored[:top_k] if score > 0]


def twiml_reply(message):
    safe = (message.replace("&", "&amp;").replace("<", "&lt;")
                   .replace(">", "&gt;"))
    return (f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<Response><Message>{safe}</Message></Response>')


class Agent:
    def __init__(self):
        self.passages = load_passages()
        self.state = {}  # sender -> {"turns": int}

    def handle(self, sender, body):
        body = (body or "").strip()
        st = self.state.setdefault(sender, {"turns": 0})
        st["turns"] += 1

        if body.lower() == "reset":
            self.state[sender] = {"turns": 0}
            return "Conversation reset. Ask me anything about our services."

        if "human" in body.lower():
            return ("Connecting you to a team member — they'll reply here "
                    "shortly. Your chat history is saved for them.")

        hits = retrieve(body, self.passages)
        if not hits:
            return ("I couldn't find that in our knowledge base. Type 'human' "
                    "to reach the team, or rephrase your question.")
        best = hits[0]
        extra = f" (+{len(hits)-1} more)" if len(hits) > 1 else ""
        return f"{best['text']}\n\n(Source: {best['source']}{extra})"


agent = Agent()
app = Flask(__name__)


@app.post("/whatsapp/incoming")
def whatsapp_incoming():
    sender = request.form.get("From", "unknown")
    body = request.form.get("Body", "")
    return Response(twiml_reply(agent.handle(sender, body)),
                    mimetype="text/xml")


if __name__ == "__main__":
    app.run(port=5000, debug=True)
