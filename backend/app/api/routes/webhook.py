"""
Webhook endpoints for ElevenLabs Conversational AI integration.
These endpoints receive real-time callbacks from ElevenLabs agents.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import JobRecord
from app.db.session import get_session
from app.models.job_spec import Quote, QuoteOutcome

router = APIRouter()


class ElevenLabsWebhookPayload(BaseModel):
    """Payload structure from ElevenLabs webhook."""
    type: str  # "conversation_initiated", "conversation_completed", "call_ended"
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    transcript: Optional[str] = None
    call_duration: Optional[float] = None
    metadata: Optional[dict] = None


class CallResultPayload(BaseModel):
    """Payload for call results from counterparty agents."""
    job_id: str
    vendor_id: str
    vendor_name: str
    transcript: str
    quote_total: float
    line_items: list[dict] = []
    outcome: str = "completed"


@router.post("/elevenlabs")
async def elevenlabs_webhook(
    payload: ElevenLabsWebhookPayload,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Receive webhook callbacks from ElevenLabs agents.
    
    This endpoint handles:
    - Conversation initiated events
    - Conversation completed events
    - Call ended events with transcripts
    """
    # Log the webhook event
    print(f"📞 ElevenLabs webhook received: {payload.type}")
    
    if payload.type == "conversation_completed" and payload.transcript:
        # Process completed conversation transcript
        # This would be used for real-time call results
        return {"status": "processed", "type": payload.type}
    
    return {"status": "received", "type": payload.type}


@router.post("/call-result")
async def call_result_webhook(
    payload: CallResultPayload,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Receive call results from counterparty agents.
    
    This endpoint is called by ElevenLabs when a counterparty agent
    (Carolina Haulers, Budget Move Express, etc.) completes a call.
    """
    # Get the job
    job = await session.get(JobRecord, payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get existing quotes or create new list
    existing_quotes = job.get_json_field("quotes_json") or []
    
    # Create new quote from call result
    new_quote = Quote(
        vendor_id=payload.vendor_id,
        vendor_name=payload.vendor_name,
        negotiation_style="real_voice",
        line_items=[
            {"fee_type": item.get("fee_type", "service"), "description": item.get("description", ""), "amount": item.get("amount", 0)}
            for item in payload.line_items
        ],
        total=payload.quote_total,
        outcome=QuoteOutcome.COMPLETED,
        transcript_url=f"/api/webhook/transcript/{payload.job_id}/{payload.vendor_id}",
    )
    
    # Add to existing quotes
    existing_quotes.append(new_quote.model_dump(mode="json"))
    job.set_json_field("quotes_json", existing_quotes)
    
    # Store transcript
    job.set_json_field(f"transcript_{payload.vendor_id}", payload.transcript)
    
    await session.commit()
    
    return {
        "status": "success",
        "job_id": payload.job_id,
        "quote_added": new_quote.model_dump(mode="json"),
    }


@router.get("/transcript/{job_id}/{vendor_id}")
async def get_transcript(
    job_id: str,
    vendor_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Retrieve a call transcript for a specific vendor."""
    job = await session.get(JobRecord, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    transcript = job.get_json_field(f"transcript_{vendor_id}") or "Transcript not available"
    
    return {
        "job_id": job_id,
        "vendor_id": vendor_id,
        "transcript": transcript,
    }


@router.get("/ngrok-url")
async def get_ngrok_url() -> dict:
    """Return the current ngrok URL for agent configuration."""
    import os
    ngrok_url = os.getenv("NGROK_URL", "http://127.0.0.1:8000")
    return {"ngrok_url": ngrok_url, "webhook_url": f"{ngrok_url}/api/webhook/elevenlabs"}