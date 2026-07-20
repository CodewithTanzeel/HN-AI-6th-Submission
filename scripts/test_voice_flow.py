#!/usr/bin/env python3
"""
Voice Flow Testing Script
Tests the complete voice-based application flow
"""

import asyncio
import httpx
import time
from pathlib import Path

API_BASE = "http://127.0.0.1:8000"

async def test_voice_flow():
    """Test the complete voice-based flow."""
    print("=" * 60)
    print("Voice Flow Testing")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Step 1: Create Job
        print("\n[1/8] Creating job...")
        res = await client.post(f"{API_BASE}/api/jobs")
        if res.status_code != 200:
            print(f"Failed to create job: {res.text}")
            return
        job = res.json()
        job_id = job["id"]
        print(f"Job created: {job_id}")
        
        # Step 2: Voice Intake
        print("\n[2/8] Testing voice intake...")
        voice_transcript = "Moving from Rock Hill, SC to Charlotte, NC, 45 miles, 2 bedroom apartment, move date is 2024-08-15, no special items"
        res = await client.post(
            f"{API_BASE}/api/jobs/{job_id}/voice",
            json={"transcript": voice_transcript}
        )
        if res.status_code != 200:
            print(f"Failed voice intake: {res.text}")
            return
        print("Voice intake successful")
        
        # Step 3: Get Spec
        print("\n[3/8] Getting job spec...")
        res = await client.get(f"{API_BASE}/api/jobs/{job_id}/spec")
        if res.status_code != 200:
            print(f"Failed to get spec: {res.text}")
            return
        spec = res.json()
        print(f"Spec loaded: {spec['spec']['origin']} -> {spec['spec']['destination']}")
        
        # Step 4: Confirm
        print("\n[4/8] Confirming job spec...")
        res = await client.post(f"{API_BASE}/api/jobs/{job_id}/confirm", json={})
        if res.status_code != 200:
            print(f"Failed to confirm: {res.text}")
            return
        print("Job confirmed")
        
        # Step 5: Start Calls
        print("\n[5/8] Starting calls to moving companies...")
        res = await client.post(f"{API_BASE}/api/jobs/{job_id}/calls")
        if res.status_code != 200:
            print(f"Failed to start calls: {res.text}")
            return
        calls_data = res.json()
        print(f"Received {len(calls_data['quotes'])} quotes")
        
        # Step 6: Negotiation
        print("\n[6/8] Running negotiation...")
        res = await client.post(f"{API_BASE}/api/jobs/{job_id}/negotiate")
        if res.status_code != 200:
            print(f"Failed negotiation: {res.text}")
            return
        neg_data = res.json()
        changed = sum(1 for n in neg_data['negotiations'] if n['changed'])
        print(f"Negotiation complete: {changed} prices reduced")
        
        # Step 7: Report
        print("\n[7/8] Getting final report...")
        res = await client.get(f"{API_BASE}/api/jobs/{job_id}/report")
        if res.status_code != 200:
            print(f"Failed to get report: {res.text}")
            return
        report = res.json()
        if report['ranked_quotes']:
            top = report['ranked_quotes'][0]
            print(f"Top recommendation: {top['vendor_name']} - ${top['negotiated_total']}")
        
        # Step 8: Voice Session
        print("\n[8/8] Testing voice session endpoint...")
        res = await client.get(f"{API_BASE}/api/jobs/{job_id}/voice/session")
        if res.status_code != 200:
            print(f"Failed to get voice session: {res.text}")
            return
        session = res.json()
        print(f"Voice session created: {session['session_id']}")
        
    print("\n" + "=" * 60)
    print("All tests passed! Voice flow is working correctly.")
    print("=" * 60)
    print(f"\nTo test the UI, run:")
    print(f"1. uvicorn app.main:app --app-dir backend --reload")
    print(f"2. cd frontend && npm run dev")
    print(f"3. Open http://localhost:3000")
    print(f"4. Use job_id: {job_id}")

if __name__ == "__main__":
    asyncio.run(test_voice_flow())