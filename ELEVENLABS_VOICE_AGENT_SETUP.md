# ElevenLabs Voice Agent Integration Guide

This guide will help you set up ElevenLabs voice agents for proper voice integration in The Negotiator project, enabling real-time voice calls and AI-powered negotiation.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Getting Your ElevenLabs API Key](#getting-your-elevenlabs-api-key)
3. [Environment Configuration](#environment-configuration)
4. [Understanding the Current Implementation](#understanding-the-current-implementation)
5. [Setting Up Voice Agents in ElevenLabs Dashboard](#setting-up-voice-agents-in-elevenlabs-dashboard)
6. [Configuring Agent Personas](#configuring-agent-personas)
7. [Frontend Integration](#frontend-integration)
8. [Testing the Integration](#testing-the-integration)
9. [Voice Agent for Outbound Calls](#voice-agent-for-outbound-calls)
10. [Troubleshooting](#troubleshooting)

---

## Types of Agents You Need to Create

For The Negotiator project, you need to set up **2 types of agents** in your ElevenLabs dashboard:

### 1. Primary Agent: Moving Estimator (for intake)

This is the main agent that interacts with users to gather moving details.

**Location:** https://elevenlabs.io/app/conversational-ai

**Configuration:**
- **Name:** `Moving Estimator`
- **Purpose:** Voice intake for collecting move details
- **Prompt:** See Step 3 above

### 2. Counterparty Agents (for outbound calls)

These agents simulate moving companies that you call to get quotes. The project already has 3 pre-configured negotiation styles in `config/verticals/moving.yaml`:

| Agent Name | Phone | Negotiation Style |
|------------|-------|-----------------|
| Carolina Haulers | +18005550101 | Tough Negotiator |
| Budget Move Express | +18005550102 | Hidden Fees Lowballer |
| Premium Relocation Co | +18005550103 | Hard Sell Upseller |

**Note:** The current implementation uses simulated calls (see `scripts/seed_counter_agents.py`). For real voice calls, you would need to:
1. Create these agents in ElevenLabs
2. Configure Twilio for phone calls
3. Set up webhook endpoints in your FastAPI app

---
```

## Prerequisites

- ElevenLabs account (sign up at https://elevenlabs.io)
- OpenAI API key (you already have this)
- Python 3.11+ with the project dependencies installed
- Node.js 18+ for the frontend

---

## Getting Your ElevenLabs API Key

1. **Sign in to ElevenLabs**
   - Go to https://elevenlabs.io/app/speech-synthesis
   - Create an account or log in

2. **Navigate to API Settings**
   - Click on your profile icon in the top right
   - Select "Profile" or "Settings"
   - Go to the "API Keys" section

3. **Create/Find Your API Key**
   - Copy your existing API key or create a new one
   - The key format is: `xi_xxxxxxxxxxxxxxxxxxxxxxxxxxxx` (NOT `sk_...` which is for OpenAI)

4. **Enable Required Features**
   - Ensure you have access to:
     - **Conversational AI** (for voice agents)
     - **Text-to-Speech** (for voice synthesis)
     - **Speech-to-Text** (for voice recognition)

---

## Environment Configuration

### Backend Configuration (.env)

Update your `.env` file in the project root:

```bash
# .env
ELEVENLABS_API_KEY=xi_your_actual_api_key_here
OPENAI_API_KEY=sk_your_openai_key_here
GOOGLE_PLACES_API_KEY=optional_google_places_key
DATABASE_URL=sqlite+aiosqlite:///./negotiator.db
VERTICAL=moving
CONFIG_PATH=config/verticals/moving.yaml
```

### Frontend Configuration (.env.local)

Update your `frontend/.env.local` file:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_ELEVENLABS_API_KEY=xi_your_actual_api_key_here
```

**Important:** The `NEXT_PUBLIC_` prefix is required for frontend access.

---

## Understanding the Current Implementation

### Backend Client (`backend/app/clients/elevenlabs.py`)

The project already has an ElevenLabs client wrapper that:

- **Creates voice sessions** via `/convai/agents` endpoint
- **Parses voice transcripts** into structured job specifications
- **Falls back to mock mode** when no API key is provided
- **Uses GPT-4o** as the LLM for the agent

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/jobs/{job_id}/voice/session` | GET | Get widget URL for voice agent |
| `/api/jobs/{job_id}/voice` | POST | Submit voice transcript for parsing |
| `/api/jobs/{job_id}/calls` | POST | Start outbound calls to moving companies |

### Current Agent Configuration

The default agent is configured as a "Moving Estimator" with this prompt:

```
You are a helpful moving estimator. Gather details about the move: 
origin, destination, distance, home size, and special items.
```

---

## Setting Up Voice Agents in ElevenLabs Dashboard

### Step 1: Create a New Agent

1. Go to https://elevenlabs.io/app/conversational-ai
2. Click **"Create Agent"**
3. Choose **"Start from scratch"**

### Step 2: Configure Agent Basics

**Agent Name:** `Moving Estimator`

**Agent Type:** Conversational AI Agent

### Step 3: Set Up the Prompt

In the **Agent Prompt** section, use this configuration:

```
You are a professional moving estimator assistant. Your goal is to gather all necessary information for a moving quote.

Required Information to Collect:
1. Origin address (city, state)
2. Destination address (city, state)
3. Move date
4. Home size (bedrooms, bathrooms)
5. Inventory details (large items, special items)
6. Distance in miles
7. Stairs or special access requirements

Conversation Flow:
- Greet the user professionally
- Ask one question at a time
- Confirm each answer before moving to the next
- Be friendly and helpful
- If the user provides multiple details at once, acknowledge each one

Example Response:
"Thank you! I have your origin as Rock Hill, SC and destination as Charlotte, NC. 
How many bedrooms is your current home, and do you have any large items like 
piano or pool table to move?"
```

### Step 4: Configure LLM Settings

- **LLM Provider:** OpenAI
- **Model:** gpt-4o (or gpt-4-turbo)
- **Temperature:** 0.7
- **Max Tokens:** 1000

### Step 5: Voice Settings

- **Voice:** Choose a professional, clear voice (e.g., "Rachel" or "Domestic")
- **Stability:** 0.5
- **Clarity:** 0.75
- **Style Exaggeration:** 0.0

### Step 6: Get Agent ID

After creating, copy the **Agent ID** - you'll need it for the widget integration.

---

## Configuring Agent Personas

The project uses different negotiation styles for counterparty agents. Here are the configurations:

### 1. Tough Negotiator (Carolina Haulers)

**Prompt:**
```
You are a tough but fair moving company representative. You:
- Start with a competitive but firm price
- Are willing to negotiate but don't budge easily
- Ask detailed questions about the move
- Mention your experience and reliability
- Offer small concessions when pushed
```

### 2. Hidden Fees Lowballer (Budget Move Express)

**Prompt:**
```
You are a budget moving company that gives low initial quotes but:
- Add hidden fees for stairs, long carries, etc.
- Seem helpful but have many add-ons
- Quote low to get the customer interested
- Reveal additional fees after initial agreement
- Are difficult to negotiate with once committed
```

### 3. Hard Sell Upseller (Premium Relocation Co)

**Prompt:**
```
You are a premium moving company that:
- Starts with higher quotes
- Pushes additional services (packing, insurance, storage)
- Emphasizes quality and professionalism
- Offers package deals
- Is willing to negotiate on base price but not on upsells
```

---

## Frontend Integration

### Current Implementation

The frontend at `frontend/app/intake/voice/page.tsx` already supports:

1. **Voice Widget Mode** (when API key is set)
2. **Manual Transcript Mode** (fallback)

### Adding ElevenLabs Widget

To enable the full voice widget, add this to your frontend:

```tsx
// In frontend/app/intake/voice/page.tsx
// The widget is already implemented via iframe:
// src={session.widget_url}

// For direct widget integration, you can also use:
<script src="https://elevenlabs.io/convai/widget.js"></script>
```

### Widget Configuration Options

```javascript
// Optional: Customize the widget appearance
const widgetConfig = {
  agentId: "your_agent_id",
  backgroundColor: "#ffffff",
  textColor: "#000000",
  borderRadius: "8px",
  width: "100%",
  height: "400px"
};
```

---

## Testing the Integration

### 1. Test Mock Mode (No API Key)

```bash
# Clear the API key
echo "ELEVENLABS_API_KEY=" > .env

# Run tests
pytest backend/tests/unit/test_elevenlabs.py -v
```

### 2. Test Real API Mode

```bash
# Add your API key
echo "ELEVENLABS_API_KEY=xi_your_key_here" > .env

# Run tests
pytest backend/tests/unit/test_elevenlabs.py -v
```

### 3. Manual Testing

1. **Start the backend:**
   ```bash
   uvicorn app.main:app --app-dir backend --reload
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Navigate to:** http://localhost:3000/intake/voice?job_id=test-job-123

4. **Test scenarios:**
   - With API key: Voice widget should appear
   - Without API key: Textarea for manual transcript

---

## Voice Agent for Outbound Calls

### Understanding the Call Flow

The project uses `CallerService` to simulate calls to moving companies. For real voice calls:

### Option 1: Using ElevenLabs Conversational API

```python
# In backend/app/services/caller.py
# The caller service can be extended to use real voice calls:

async def make_voice_call(self, phone_number: str, script: str):
    """Make a real voice call using ElevenLabs"""
    # Use ElevenLabs Twilio integration or ConvAI API
    # to place calls to moving companies
    pass
```

### Option 2: Using ElevenLabs + Twilio

1. **Set up Twilio account**
2. **Configure webhook endpoint** in your FastAPI app
3. **Use ElevenLabs TTS** for the agent's voice responses

### Call Script Template

```
Hello, this is an AI assistant calling on behalf of a customer 
who needs moving services. I can provide all the details you need 
for an accurate quote.

The move is from {origin} to {destination}, approximately 
{distance} miles on {move_date}. It's a {bedrooms} bedroom home 
with {inventory} items.

Are you available for this move, and what would be your quote?
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Widget not loading** | Check `NEXT_PUBLIC_ELEVENLABS_API_KEY` is set in frontend/.env.local |
| **API key invalid** | Ensure key starts with `xi_`, not `sk_` |
| **CORS errors** | Verify backend CORS allows localhost:3000 |
| **Session not created** | Check backend logs for API errors |
| **Voice not working** | Ensure microphone permissions are granted |

### Debug Mode

Enable debug logging:

```python
# Add to backend/app/clients/elevenlabs.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### API Key Validation

```bash
# Test your API key
curl -X GET https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: xi_your_api_key_here"
```

### Rate Limits

- Free tier: 10,000 characters/month
- Paid tier: Higher limits based on plan
- Implement caching in `.env`: `CACHE_TTL=300`

---

## Next Steps

1. **Add your ElevenLabs API key** to both `.env` and `frontend/.env.local`
2. **Add your OpenAI API key** to `.env`
3. **Create agents** in ElevenLabs dashboard with the prompts above
4. **Test the voice intake** at `/intake/voice`
5. **Run the full demo:** `python scripts/run_demo.py`

---

## Additional Resources

- [ElevenLabs API Docs](https://elevenlabs.io/docs/api)
- [Conversational AI Docs](https://elevenlabs.io/docs/conversational-ai)
- [Voice Widget Integration](https://elevenlabs.io/docs/widget)

---

## Quick Setup Checklist

- [ ] Get ElevenLabs API key (format: `xi_...`)
- [ ] Add `ELEVENLABS_API_KEY` to `.env`
- [ ] Add `NEXT_PUBLIC_ELEVENLABS_API_KEY` to `frontend/.env.local`
- [ ] Add `OPENAI_API_KEY` to `.env`
- [ ] Create "Moving Estimator" agent in ElevenLabs dashboard
- [ ] Test voice widget at `/intake/voice`
- [ ] Verify transcript parsing works correctly
- [ ] Run full demo flow