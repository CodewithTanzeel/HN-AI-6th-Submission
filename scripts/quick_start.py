#!/usr/bin/env python3
"""
Quick start script for The Negotiator with ngrok.
This script helps you get started quickly with the full setup.
"""

import os
import subprocess
import sys
from pathlib import Path


def print_banner():
    print("=" * 60)
    print("The Negotiator - Quick Start with Ngrok")
    print("=" * 60)


def check_prerequisites():
    """Check if all prerequisites are installed."""
    print("\n📋 Checking prerequisites...")
    
    # Check Python
    print(f"✅ Python: {sys.version.split()[0]}")
    
    # Check ngrok
    try:
        result = subprocess.run(["ngrok", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ngrok: {result.stdout.strip()}")
        else:
            print("❌ Ngrok not found. Install from: https://ngrok.com/download")
            return False
    except FileNotFoundError:
        print("❌ Ngrok not installed. Install from: https://ngrok.com/download")
        return False
    
    # Check pip packages
    try:
        import httpx
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
        print(f"✅ HTTPX: {httpx.__version__}")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True


def show_instructions():
    """Show setup instructions."""
    print("\n" + "=" * 60)
    print("Setup Instructions")
    print("=" * 60)
    
    print("""
1. 🔧 Configure your API keys in .env:
   - ELEVENLABS_API_KEY=xi_your_key_here (NOT sk_...)
   - OPENAI_API_KEY=sk_your_key_here

2. 🚀 Start the backend (Terminal 1):
   uvicorn app.main:app --app-dir backend --reload

3. 🌐 Start ngrok (Terminal 2):
   python scripts/run_ngrok.py

4. 🧪 Test the integration (Terminal 3):
   python scripts/test_webhook.py

5. 🎙️ Configure ElevenLabs agents:
   - Main Agent: Neogitatera
   - Counterparties: Carolina Haulers, Budget Move Express, Premium Relocation Co
   - Webhook URL: https://<ngrok-url>/api/webhook/elevenlabs

6. 🌍 Access the app:
   https://<ngrok-url>/intake/voice?job_id=test-123
""")


def main():
    print_banner()
    
    if not check_prerequisites():
        print("\n❌ Please fix the issues above before continuing.")
        return
    
    show_instructions()
    
    print("\n" + "=" * 60)
    print("Quick Actions")
    print("=" * 60)
    
    print("""
To start everything:

Terminal 1 (Backend):
  uvicorn app.main:app --app-dir backend --reload

Terminal 2 (Ngrok):
  python scripts/run_ngrok.py

Terminal 3 (Test):
  python scripts/test_webhook.py
""")


if __name__ == "__main__":
    main()