#!/usr/bin/env python3
"""
Test script for webhook integration.
Tests the ngrok webhook endpoints and validates the setup.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.clients.elevenlabs import ElevenLabsClient
from app.models.job_spec import JobSpec


def test_webhook_endpoints():
    """Test that webhook endpoints are accessible."""
    import requests
    
    # Get ngrok URL from environment
    ngrok_url = os.getenv("NGROK_URL", "http://127.0.0.1:8000")
    
    print("=" * 60)
    print("Testing Webhook Endpoints")
    print("=" * 60)
    
    # Test health endpoint
    try:
        response = requests.get(f"{ngrok_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Health check passed: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test ngrok-url endpoint
    try:
        response = requests.get(f"{ngrok_url}/api/webhook/ngrok-url", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ngrok URL endpoint: {data}")
        else:
            print(f"❌ Ngrok URL endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Ngrok URL endpoint error: {e}")
    
    # Test webhook endpoint
    try:
        response = requests.post(
            f"{ngrok_url}/api/webhook/elevenlabs",
            json={"type": "test", "conversation_id": "test-123"},
            timeout=5
        )
        if response.status_code == 200:
            print(f"✅ Webhook endpoint test passed: {response.json()}")
        else:
            print(f"❌ Webhook endpoint test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Webhook endpoint error: {e}")


def test_elevenlabs_client():
    """Test ElevenLabs client with webhook support."""
    print("\n" + "=" * 60)
    print("Testing ElevenLabs Client")
    print("=" * 60)
    
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    
    if not api_key:
        print("⚠️  No ELEVENLABS_API_KEY set - testing mock mode only")
        client = ElevenLabsClient()
    elif not api_key.startswith("xi_"):
        print("⚠️  Invalid API key format (should start with 'xi_') - testing mock mode")
        client = ElevenLabsClient()
    else:
        client = ElevenLabsClient(api_key)
    
    # Test session creation
    session = asyncio.run(client.start_intake_session("test-job-123"))
    print(f"✅ Session created: {json.dumps(session, indent=2)}")
    
    # Test counterparty session
    counterparty_session = asyncio.run(
        client.start_counterparty_session(
            job_id="test-job-123",
            vendor_id="carolina_haulers",
            vendor_name="Carolina Haulers",
            negotiation_style="tough_negotiator"
        )
    )
    print(f"✅ Counterparty session: {json.dumps(counterparty_session, indent=2)}")


def main():
    print("=" * 60)
    print("The Negotiator - Webhook Integration Test")
    print("=" * 60)
    
    # Check if backend is running
    print("\n📋 Prerequisites:")
    print("1. Backend should be running: uvicorn app.main:app --app-dir backend --reload")
    print("2. Ngrok should be running: python scripts/run_ngrok.py")
    print()
    
    test_webhook_endpoints()
    test_elevenlabs_client()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()