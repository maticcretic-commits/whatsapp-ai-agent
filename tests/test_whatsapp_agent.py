"""Offline tests for the WhatsApp agent (no API keys needed)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from whatsapp_agent import Agent, tokenize, retrieve, twiml_reply, app


def test_tokenize_drops_stopwords():
    tokens = tokenize("What is the refund policy?")
    assert "refund" in tokens and "policy" in tokens
    assert "what" not in tokens and "the" not in tokens


def test_retrieve_finds_refund_passage():
    agent = Agent()
    hits = retrieve("What is your refund policy?", agent.passages)
    assert hits, "expected at least one hit"
    assert "30-day money-back" in hits[0]["text"]


def test_retrieve_no_match_empty():
    agent = Agent()
    assert retrieve("quantum banana firmware", agent.passages) == []


def test_agent_answers_from_kb():
    agent = Agent()
    reply = agent.handle("user1", "How much does the Business plan cost?")
    assert "$29" in reply and "Source:" in reply


def test_agent_human_handoff():
    agent = Agent()
    reply = agent.handle("user2", "I want to talk to a human please")
    assert "team member" in reply


def test_agent_reset():
    agent = Agent()
    agent.handle("user3", "hello")
    assert agent.handle("user3", "reset").startswith("Conversation reset")


def test_twiml_escapes_xml():
    xml = twiml_reply("a < b & c")
    assert "&lt;" in xml and "&amp;" in xml
    assert "<Message>" in xml


def test_webhook_returns_twiml():
    client = app.test_client()
    resp = client.post("/whatsapp/incoming",
                       data={"From": "whatsapp:+911234567890",
                             "Body": "What is the refund policy?"})
    assert resp.status_code == 200
    assert b"30-day money-back" in resp.data


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_"):
            fn()
            print(f"PASS {name}")
    print("All tests passed.")
