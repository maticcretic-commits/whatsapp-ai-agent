# WhatsApp AI Agent

A portfolio practice project: a **WhatsApp knowledge-base agent** starter —
the "$300 fixed" gig pattern (Twilio WhatsApp webhook, document ingestion,
retrieval, human handoff).

> Demo/study project — connect a real WhatsApp Business number and a vector
> database before production use.

## How it works

- `POST /whatsapp/incoming` — Twilio webhook (`From` + `Body`), replies
  with TwiML `<Message>`.
- **Retrieval** — incoming questions are matched against `documents/` by
  keyword-overlap scoring, the zero-dependency stand-in for vector search.
  Answers cite their source file.
- **Handoff** — "human" (or no confident match) routes to the team with
  chat history noted.
- **State** — per-sender turn counting; send `reset` to start over.

## Run

```bash
pip install -r requirements.txt
python whatsapp_agent.py            # http://localhost:5000
python tests/test_whatsapp_agent.py # no API keys needed
```

Try it:

```bash
curl -X POST localhost:5000/whatsapp/incoming \
  -d "From=whatsapp:+911234567890" -d "Body=What is the refund policy?"
```

## Production upgrade path (learning roadmap)

- [ ] Swap keyword scoring for embeddings + pgvector/Supabase
- [ ] LLM re-ranking and answer synthesis over retrieved passages
- [ ] Firestore/tools for structured record lookup
- [ ] Conversation persistence (Redis/Postgres) instead of memory
