# The Negotiator - Complete Beginner's Guide

A step-by-step manual to run the voice-agent system for the Hack-Nation × ElevenLabs hackathon.

---

## 🎯 What This Project Does

**Problem:** Moving quotes vary 5.6x for identical work ($1,158 to $6,506). People don't have time to shop around.

**Solution:** An AI voice agent that:

1. **Gathers** your move details (voice or documents)
2. **Calls** 3 moving companies in parallel
3. **Negotiates** better prices using competing bids
4. **Recommends** the best deal with evidence

---

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- **ElevenLabs API Key** (MANDATORY - required for voice agent functionality, get from <https://elevenlabs.io>)
- **OpenAI API Key** (MANDATORY - required for LLM processing, get from <https://platform.openai.com>)

---

## 🚀 Quick Start

### Step 2: Backend Setup

```bash
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# Install Python dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env
```

### Step 3: Frontend Setup

```bash
cd frontend
npm install
```

### Step 4: Run the Application

```bash
# Terminal 1 - Backend (from project root)
uvicorn app.main:app --app-dir backend --reload

# Terminal 2 - Frontend (from project root)
cd frontend
npm run dev
```

### Step 5: Open in Browser

- Frontend: <http://localhost:3000>
- Backend API: <http://localhost:8000>

---

## 🛠️ Detailed Setup

### Step 1: Environment Variables

**Create `.env` in project root (MANDATORY):**

```env
# ElevenLabs API Key - REQUIRED
ELEVENLABS_API_KEY=xi_your_actual_key_here

# OpenAI API Key - REQUIRED
OPENAI_API_KEY=sk_your_key_here

# Database
DATABASE_URL=sqlite+aiosqlite:///./negotiator.db

# Config
VERTICAL=moving
CONFIG_PATH=config/verticals/moving.yaml
```

**Create `frontend/.env.local`:**

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_ELEVENLABS_API_KEY=xi_your_actual_key_here
```

### Step 2: Install Dependencies

**Backend requirements (`requirements.txt`):**

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.9.0
pydantic-settings>=2.6.0
pyyaml>=6.0.2
httpx>=0.27.0
python-multipart>=0.0.12
jinja2>=3.1.4
sqlalchemy>=2.0.36
aiosqlite>=0.20.0
pytest>=8.3.0
pytest-asyncio>=0.24.0
pytest-cov>=6.0.0
```

**Frontend dependencies (`package.json`):**

- next@14.2.0
- react@18.2.0
- tailwindcss@3.4.0
- typescript@5.0.0

---

## 🎮 How to Use

### Step 1: Create a Job

1. Open <http://localhost:3000>
2. Click "Create New Job" button
3. You'll be redirected to the voice intake page

### Step 2: Voice Intake

1. Speak into the microphone using the ElevenLabs voice widget
2. The AI will ask for your move details (origin, destination, date, bedrooms, stairs)

### Step 3: Document Intake (Optional)

1. Upload a quote or inventory document
2. The system extracts move details automatically

### Step 4: Confirm Spec

1. Review the merged job specification
2. Click "Confirm" to proceed

### Step 5: Run Calls

1. Click "Start Calls"
2. The AI calls 3 moving companies (simulated via counterparty agents)
3. View quotes with itemized fees

### Step 6: Negotiate

1. Click "Start Negotiation"
2. The AI uses the best quote as leverage
3. Other companies reduce their prices

### Step 7: View Report

1. See ranked recommendations
2. Read negotiation evidence
3. Check for red flags

---

## 🏗️ Project Architecture

### Backend Structure

```
backend/app/
├── main.py              # FastAPI app entry point
├── api/routes/
│   ├── jobs.py          # Job CRUD + voice + calls + negotiation
│   ├── pages.py         # Server-side HTML templates
│   └── reports.py       # Final report endpoint
├── clients/
│   └── elevenlabs.py    # ElevenLabs API wrapper
├── config/
│   ├── loader.py        # Load YAML config
│   └── settings.py      # Environment variables
├── db/
│   ├── models.py        # JobRecord model
│   └── session.py       # Database session
├── middleware/
│   ├── rate_limit.py    # Request limiting
│   └── cache.py         # Response caching
├── models/
│   └── job_spec.py      # Pydantic models
└── services/
    ├── caller.py        # Parallel quote gathering
    ├── closer.py        # Negotiation & ranking
    ├── quote_builder.py # Quote generation
    ├── document_intake.py # Document parsing
    └── call_list.py     # Counterparty management
```

### Frontend Structure

```
frontend/
├── app/
│   ├── page.tsx         # Home page
│   ├── calls/page.tsx   # Calls page
│   ├── negotiate/page.tsx # Negotiation page
│   ├── quotes/page.tsx  # Quotes comparison
│   ├── report/page.tsx  # Final report
│   ├── components/      # ProgressStepper, VoiceButton, VoiceFeedback
│   ├── hooks/
│   │   └── useVoiceControl.ts # Speech recognition hook
│   └── intake/
│       ├── voice/page.tsx # Voice intake
│       ├── documents/page.tsx # Document upload
│       └── confirm/page.tsx # Confirmation page
├── templates/           # Jinja2 HTML templates
└── package.json
```

---

## 📖 Key Code Snippets

### JobSpec Model (`backend/app/models/job_spec.py`)

```python
class JobSpec(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    distance_miles: Optional[float] = Field(default=None, ge=0)
    move_date: Optional[date] = None
    home: Optional[HomeDetails] = None
    inventory: list[InventoryItem] = Field(default_factory=list)
    services: ServiceOptions = Field(default_factory=ServiceOptions)
    confirmed_by_user: bool = False
    confirmed_at: Optional[datetime] = None

    @classmethod
    def merge(cls, primary: "JobSpec", secondary: "JobSpec") -> "JobSpec":
        data = primary.model_dump()
        secondary_data = secondary.model_dump(exclude_none=True)
        for key, value in secondary_data.items():
            if key in {"inventory", "services"}:
                continue
            if value is None:
                continue
            current = data.get(key)
            if current in (None, "", [], {}):
                data[key] = value
        merged_inventory = {item["item"].lower(): item for item in data.get("inventory", [])}
        for item in secondary.inventory:
            merged_inventory[item.item.lower()] = item.model_dump()
        data["inventory"] = list(merged_inventory.values())
        return cls.model_validate(data)
```

### Quote Model (`backend/app/models/job_spec.py`)

```python
class Quote(BaseModel):
    vendor_id: str
    vendor_name: str
    negotiation_style: str
    line_items: list[QuoteLineItem] = Field(default_factory=list)
    total: float = Field(ge=0)
    binding: bool = False
    valid_until: Optional[date] = None
    outcome: QuoteOutcome = QuoteOutcome.QUOTED
    transcript_url: Optional[str] = None
    recording_url: Optional[str] = None
    red_flag: Optional[str] = None
```

### Caller Service (`backend/app/services/caller.py`)

```python
class CallerService:
    def __init__(self, config: VerticalConfig):
        self.config = config
        self.call_list = CallListService(config)
        self.quote_builder = QuoteBuilder(config)

    async def _call_counterparty(self, counterparty, spec: JobSpec) -> Quote:
        await asyncio.sleep(0.1)  # Simulate call latency
        if counterparty.negotiation_style == "stonewaller":
            return Quote(vendor_id=counterparty.id, vendor_name=counterparty.name,
                        negotiation_style=counterparty.negotiation_style, outcome=QuoteOutcome.CALLBACK)
        return self.quote_builder.build_quote(counterparty, spec)

    async def gather_quotes(self, spec: JobSpec) -> list[Quote]:
        counterparties = self.call_list.get_counterparties()
        tasks = [self._call_counterparty(cp, spec) for cp in counterparties]
        return list(await asyncio.gather(*tasks))
```

### Quote Builder (`backend/app/services/quote_builder.py`)

```python
class QuoteBuilder:
    def estimate_market_price(self, spec: JobSpec) -> float:
        benchmarks = self.config.benchmarks
        bedrooms = spec.home.bedrooms if spec.home else 2
        miles = spec.distance_miles or 45
        return round(benchmarks.base_fee + (benchmarks.price_per_mile * miles) + 
                     (benchmarks.price_per_bedroom * bedrooms), 2)

    def build_quote(self, counterparty: CounterpartyConfig, spec: JobSpec) -> Quote:
        market = self.estimate_market_price(spec)
        base = round(market * counterparty.base_multiplier, 2)
        line_items = [QuoteLineItem(fee_type="base", description="Base moving rate", amount=base)]
        if spec.home and spec.home.stairs > 0 and counterparty.negotiation_style != "hidden_fees_lowballer":
            line_items.append(QuoteLineItem(fee_type="stairs", 
                description=f"Stair carry ({spec.home.stairs} flights)", amount=round(35 * spec.home.stairs, 2)))
        for fee in counterparty.hidden_fees:
            line_items.append(QuoteLineItem(fee_type=fee["fee_type"], description=fee["description"], amount=fee["amount"]))
        for fee in counterparty.upsell_fees:
            line_items.append(QuoteLineItem(fee_type=fee["fee_type"], description=fee["description"], amount=fee["amount"]))
        return Quote(vendor_id=counterparty.id, vendor_name=counterparty.name,
                    negotiation_style=counterparty.negotiation_style, line_items=line_items,
                    total=round(sum(item.amount for item in line_items), 2),
                    binding=counterparty.negotiation_style == "tough_negotiator")
```

### ElevenLabs Client (`backend/app/clients/elevenlabs.py`)

```python
class ElevenLabsClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")
        self.base_url = "https://api.elevenlabs.io/v1"
        self.use_real_api = bool(self.api_key)

    async def start_intake_session(self, job_id: str) -> dict:
        if not self.use_real_api:
            return self._mock_start_session(job_id)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/convai/agents",
                    headers={"xi-api-key": self.api_key},
                    json={"name": "Moving Estimator", "conversation_config": {...}})
                if response.status_code == 200:
                    return {"session_id": f"session_{job_id}", "widget_url": "..."}
        except Exception:
            pass
        return self._mock_start_session(job_id)

    def _mock_parse_transcript(self, transcript: str) -> JobSpec:
        parser = DocumentIntakeService()
        return parser.parse_text_content(transcript)
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest backend/tests -v --cov=backend/app
```

### Test Categories

| Command | What it tests |
|---------|---------------|
| `pytest backend/tests/unit/test_job_spec.py -v` | JobSpec model validation |
| `pytest backend/tests/unit/test_caller_closer.py -v` | Quote building & negotiation |
| `pytest backend/tests/unit/test_elevenlabs.py -v` | Voice client |
| `pytest backend/tests/integration/test_full_flow.py -v` | Full end-to-end flow |

### Run Demo Script

```bash
# Requires backend running on port 8000
python scripts/run_demo.py
```

---

## 🎙️ Voice Agent Setup (MANDATORY)

### Step 1: Get ElevenLabs API Key

1. Go to <https://elevenlabs.io>
2. Sign up / Log in with email or Google
3. Click your profile → Settings → API Keys
4. Copy your API key (format: `xi_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

**Note: This API key is MANDATORY - without it the voice agent will not function.**

### Step 2: Configure Environment

**Add to `.env` (REQUIRED):**

```env
ELEVENLABS_API_KEY=xi_your_actual_key_here
```

**Add to `frontend/.env.local`:**

```env
NEXT_PUBLIC_ELEVENLABS_API_KEY=xi_your_actual_key_here
```

### Step 3: Create Voice Agents in ElevenLabs Dashboard

Go to: <https://elevenlabs.io/app/conversational-ai>

#### Agent 1: Moving Estimator (Intake Agent)

**Configuration:**

- **Name:** `Moving Estimator`
- **Prompt:**

```
You are a professional moving estimator assistant. Your goal is to gather all necessary information for a moving quote.

Required Information to Collect:
1. Origin address (city, state)
2. Destination address (city, state)
3. Move date
4. Home size (bedrooms)
5. Inventory details (large items like piano, pool table)
6. Distance in miles
7. Stairs or special access requirements

Conversation Flow:
- Greet the user professionally
- Ask one question at a time
- Confirm each answer before moving to the next
- Be friendly and helpful
```

- **LLM Model:** gpt-4o
- **Temperature:** 0.7

#### Agent 2: Carolina Haulers (Tough Negotiator)

**Configuration:**

- **Name:** `Carolina Haulers`
- **Prompt:**

```
You are a tough but fair moving company representative. You:
- Start with a competitive but firm price
- Are willing to negotiate but don't budge easily
- Ask detailed questions about the move
- Mention your experience and reliability
- Offer small concessions when pushed
- Provide itemized quotes with binding options
```

- **Negotiation Style:** `tough_negotiator`
- **Base Multiplier:** 1.05

#### Agent 3: Budget Move Express (Hidden Fees Lowballer)

**Configuration:**

- **Name:** `Budget Move Express`
- **Prompt:**

```
You are a budget moving company that gives low initial quotes but:
- Add hidden fees for stairs, long carries, etc.
- Seem helpful but have many add-ons
- Quote low to get the customer interested
- Reveal additional fees after initial agreement
- Are difficult to negotiate with once committed
```

- **Negotiation Style:** `hidden_fees_lowballer`
- **Base Multiplier:** 0.72
- **Hidden Fees:** Add $275 for stairs, $150 for long carry

#### Agent 4: Premium Relocation Co (Hard Sell Upseller)

**Configuration:**

- **Name:** `Premium Relocation Co`
- **Prompt:**

```
You are a premium moving company that:
- Starts with higher quotes ($1,150+ base)
- Pushes additional services (packing, insurance, storage)
- Emphasizes quality and professionalism
- Offers package deals
- Is willing to negotiate on base price but not on upsells
```

- **Negotiation Style:** `hard_sell_upseller`
- **Base Multiplier:** 1.15

### Step 4: Test Voice Integration

```bash
python scripts/validate_api_key.py
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend won't start | Check Python version, run `pip install -r requirements.txt` |
| Frontend won't start | Run `npm install` in frontend folder |
| Tests fail | Make sure virtual environment is activated |
| Voice widget missing | Add `NEXT_PUBLIC_ELEVENLABS_API_KEY` to `frontend/.env.local` |
| CORS errors | Backend allows localhost:3000 by default |
| Database errors | Delete `negotiator.db` to reset |

---

## 📋 Success Checklist

- [ ] Backend runs on <http://localhost:8000>
- [ ] Frontend runs on <http://localhost:3000>
- [ ] Can create job at `/`
- [ ] Voice transcript submits successfully
- [ ] Quotes are gathered from 3 companies
- [ ] Negotiation reduces prices
- [ ] Report shows ranked recommendations

---

## 🆘 Quick Reference

```bash
# Start backend
uvicorn app.main:app --app-dir backend --reload

# Start frontend
cd frontend && npm run dev

# Run tests
pytest backend/tests -v --cov=backend/app

# Run demo
python scripts/run_demo.py
```

---

## 📞 The 3 Negotiation Styles

| Company | Style | Behavior |
|---------|-------|----------|
| Carolina Haulers | Tough Negotiator | Fair price, willing to negotiate |
| Budget Move Express | Hidden Fees Lowballer | Low quote, adds surprise fees |
| Premium Relocation Co | Hard Sell Upseller | High price, pushes extra services |

---

This guide covers everything you need to run and understand The Negotiator. The project is already built - just follow the steps to run it!
