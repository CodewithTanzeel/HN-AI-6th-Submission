# ElevenLabs Voice Agent Setup - Beginner's Guide

This guide walks you through setting up ElevenLabs voice agents step-by-step, even if you've never used ElevenLabs before.

## What is ElevenLabs?

ElevenLabs is a voice AI platform that lets you:
- Create AI voice agents that can talk
- Convert text to speech with realistic voices
- Build conversational AI applications
- Make phone calls with AI voices

## Step 1: Create Your ElevenLabs Account

1. **Go to the website:** Open your browser and go to https://elevenlabs.io

2. **Sign up:** Click "Sign Up" and create an account using:
   - Your email address
   - A password
   - Or use Google/GitHub login

3. **Verify email:** Check your email and click the verification link

## Step 2: Get Your API Key

1. **Log in** to ElevenLabs at https://elevenlabs.io/app/speech-synthesis

2. **Click your profile picture** in the top-right corner

3. **Select "Settings"** or "Profile" from the dropdown menu

4. **Find "API Keys"** in the left sidebar

5. **Copy your API key** - it looks like: `sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - (Note: Your key format may vary - both `sk_` and `xi_` formats work)

## Step 3: Add API Key to Your Project

### For the Backend (Python/FastAPI):

1. **Open the `.env` file** in your project (it's in the main folder)

2. **Find this line:**
   ```
   ELEVENLABS_API_KEY=
   ```

3. **Add your key after the equals sign:**
   ```
   ELEVENLABS_API_KEY=sk_your_actual_key_here
   ```

### For the Frontend (Next.js):

1. **Open `frontend/.env.local`** in your project

2. **Find this line:**
   ```
   NEXT_PUBLIC_ELEVENLABS_API_KEY=
   ```

3. **Add your key:**
   ```
   NEXT_PUBLIC_ELEVENLABS_API_KEY=sk_your_actual_key_here
   ```

## Step 4: Add Your OpenAI API Key

The voice agent needs OpenAI to understand and respond to questions.

1. **Go to:** https://platform.openai.com

2. **Sign in** or create an account

3. **Go to API Keys:** https://platform.openai.com/api-keys

4. **Create a new key** or copy an existing one (starts with `sk_`)

5. **Add to `.env` file:**
   ```
   OPENAI_API_KEY=sk_your_openai_key_here
   ```

## Step 5: Create Your First Voice Agent

### What is a "Voice Agent"?

A voice agent is an AI that can have a conversation with someone using voice. Think of it as a chatbot that talks!

### Creating the "Moving Estimator" Agent:

1. **Go to:** https://elevenlabs.io/app/conversational-ai

2. **Click the blue "Create Agent" button**

3. **Name your agent:** Type `Moving Estimator` in the name field

4. **Set the prompt (what the agent says):**

   Copy and paste this into the "Agent Prompt" box:
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
   ```

5. **Configure the AI brain (LLM):**
   - **LLM Provider:** Select "OpenAI"
   - **Model:** Select "gpt-4o" (or "gpt-4-turbo" if 4o isn't available)
   - **Temperature:** Set to 0.7
   - **Max Tokens:** Set to 1000

6. **Choose a voice:**
   - Click "Voice" settings
   - Pick a clear, professional voice like "Rachel" or "Domestic"
   - Keep default settings (Stability: 0.5, Clarity: 0.75)

7. **Click "Save" or "Create"**

## Step 6: Test Your Setup

### Test 1: Validate API Keys

Open a terminal in your project folder and run:
```bash
python scripts/validate_api_key.py
```

You should see:
```
Validating ElevenLabs key...
API key is valid for ElevenLabs!
   Subscription: free
```

### Test 2: Start the Application

1. **Start the backend:**
   ```bash
   uvicorn app.main:app --app-dir backend --reload
   ```

2. **In a new terminal, start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open your browser** to: http://localhost:3000

4. **Click "Get Started"** to create a job

5. **Go to the voice page:** http://localhost:3000/intake/voice?job_id=YOUR_JOB_ID

6. **You should see:** Either a voice widget or a text area to type

## Step 7: Understanding the Flow

The Negotiator works in 8 steps:

1. **/** - Create a new moving job
2. **/intake/voice** - Talk to the AI to describe your move
3. **/intake/documents** - Upload moving quotes (optional)
4. **/intake/confirm** - Confirm your move details
5. **/calls** - AI calls moving companies (simulated)
6. **/quotes** - Compare prices from different movers
7. **/negotiate** - AI negotiates better prices
8. **/report** - See the best deal recommendation

## Common Beginner Questions

### Q: Do I need to pay for ElevenLabs?
A: No! The free tier includes enough credits to test the application.

### Q: What if I don't have an OpenAI key?
A: The app will still work, but the voice agent won't be as smart. You can type text instead of speaking.

### Q: Why is the voice widget not showing?
A: Make sure:
   - Your API key is in both `.env` and `frontend/.env.local`
   - You restarted the frontend after adding the key
   - The key starts with `sk_` or `xi_`

### Q: Can I use my own moving company phone numbers?
A: Yes! Edit `config/verticals/moving.yaml` to add your own companies.

## Quick Reference

| File | What to Add |
|------|-------------|
| `.env` | `ELEVENLABS_API_KEY=your_key` |
| `.env` | `OPENAI_API_KEY=your_key` |
| `frontend/.env.local` | `NEXT_PUBLIC_ELEVENLABS_API_KEY=your_key` |

## Need Help?

- **ElevenLabs Docs:** https://elevenlabs.io/docs
- **Project README:** See `README.md` in your project
- **Run the demo:** `python scripts/run_demo.py`