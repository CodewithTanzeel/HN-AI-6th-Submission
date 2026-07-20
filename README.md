# The Negotiator — Moving Companies MVP

Voice-agent system for the Hack-Nation × ElevenLabs challenge. Gathers moving quotes by phone, compares itemized fees, and negotiates the best deal.

## Stack

- Python 3.11+, FastAPI, SQLAlchemy (SQLite)
- Next.js 14 + React + TypeScript + Tailwind CSS frontend (8 pages, SPA flow)
- ElevenLabs-ready client wrapper (mocked/simulated counter-agents for demo)
- pytest TDD suite

## Quick start

```bash
# Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
pytest backend/tests -q
uvicorn app.main:app --app-dir backend --reload

# Frontend (in a new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Demo flow

1. `/` — create job
2. `/intake/voice` — voice transcript intake
3. `/intake/documents` — upload quote/inventory doc
4. `/intake/confirm` — confirm binding job spec
5. `/calls` — parallel calls to 3 counter-agents
6. `/quotes` — compare itemized fees
7. `/negotiate` — price-match negotiation
8. `/report` — ranked recommendation

Or run:

```bash
python scripts/run_demo.py
```

## Modules

| Module | Path |
|--------|------|
| Estimator | `backend/app/api/routes/jobs.py` |
| Caller | `backend/app/services/caller.py` |
| Closer | `backend/app/services/closer.py` |
| Vertical config | `config/verticals/moving.yaml` |

## Tests

```bash
pytest backend/tests -v --cov=backend/app
```

TDD layout: `backend/tests/unit`, `integration`, `eval`.

## Environment

See `.env.example` for `ELEVENLABS_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_PLACES_API_KEY`.

### Voice Setup (Optional)

The app supports two modes for voice intake:

**Mock Mode (default):**
- Leave `ELEVENLABS_API_KEY` empty
- Users enter transcript manually via textarea
- Works offline, no API costs

**Real Voice Mode:**
- Add your ElevenLabs API key to `.env`:
  ```bash
  ELEVENLABS_API_KEY=xi_xxxxx
  NEXT_PUBLIC_ELEVENLABS_API_KEY=xi_xxxxx
  ```
- Frontend shows ElevenLabs voice widget
- Users can speak directly to AI agent
- Falls back to mock mode if API fails
