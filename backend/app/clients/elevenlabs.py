import os
from typing import Protocol

import httpx
from app.models.job_spec import JobSpec


class ElevenLabsClientProtocol(Protocol):
    async def start_intake_session(self, job_id: str, webhook_url: str = "") -> dict: ...

    async def parse_voice_transcript(self, transcript: str) -> JobSpec: ...


class ElevenLabsClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")
        self.base_url = "https://api.elevenlabs.io/v1"
        self.use_real_api = bool(self.api_key)
        self.ngrok_url = os.getenv("NGROK_URL", "")

    def _get_webhook_url(self) -> str:
        """Get the webhook URL for callbacks."""
        if self.ngrok_url:
            return f"{self.ngrok_url}/api/webhook/elevenlabs"
        return ""

    async def start_intake_session(self, job_id: str, webhook_url: str = "") -> dict:
        if not self.use_real_api:
            return self._mock_start_session(job_id)

        # Use provided webhook_url or get from environment
        callback_url = webhook_url or self._get_webhook_url()

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "name": "Neogitatera",  # Updated to your agent name
                    "conversation_config": {
                        "agent": {
                            "prompt": {
                                "prompt": "You are a professional moving estimator assistant. Your goal is to gather all necessary information for a moving quote. Required Information to Collect: 1. Origin address (city, state) 2. Destination address (city, state) 3. Move date 4. Home size (bedrooms, bathrooms) 5. Inventory details (large items, special items) 6. Distance in miles 7. Stairs or special access requirements. Be friendly and ask one question at a time.",
                                "llm": "gpt-4o",
                            }
                        }
                    },
                }
                
                # Add webhook URL if available
                if callback_url:
                    payload["webhook_url"] = callback_url

                response = await client.post(
                    f"{self.base_url}/convai/agents",
                    headers={"xi-api-key": self.api_key},
                    json=payload,
                    timeout=10.0,
                )
                if response.status_code == 200:
                    agent_data = response.json()
                    return {
                        "session_id": f"session_{job_id}",
                        "agent_id": agent_data.get("agent_id", "estimator_agent"),
                        "widget_url": f"https://elevenlabs.io/convai/widget?agent_id={agent_data.get('agent_id', 'estimator_agent')}",
                        "webhook_url": callback_url,
                    }
        except Exception:
            pass

        return self._mock_start_session(job_id)

    async def start_counterparty_session(
        self, 
        job_id: str, 
        vendor_id: str, 
        vendor_name: str,
        negotiation_style: str,
        webhook_url: str = ""
    ) -> dict:
        """Start a session for a counterparty agent (Carolina, Budget, Premium)."""
        if not self.use_real_api:
            return self._mock_start_session(f"{job_id}_{vendor_id}")

        callback_url = webhook_url or self._get_webhook_url()
        
        # Get negotiation style prompt
        prompts = {
            "tough_negotiator": "You are a tough but fair moving company representative. You start with a competitive but firm price, ask detailed questions about the move, mention your experience and reliability, and offer small concessions when pushed.",
            "hidden_fees_lowballer": "You are a budget moving company that gives low initial quotes but add hidden fees for stairs, long carries, etc. You seem helpful but have many add-ons and reveal additional fees after initial agreement.",
            "hard_sell_upseller": "You are a premium moving company that starts with higher quotes, pushes additional services (packing, insurance, storage), emphasizes quality and professionalism, and offers package deals.",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/convai/agents",
                    headers={"xi-api-key": self.api_key},
                    json={
                        "name": vendor_name,
                        "conversation_config": {
                            "agent": {
                                "prompt": {
                                    "prompt": prompts.get(negotiation_style, prompts["tough_negotiator"]),
                                    "llm": "gpt-4o",
                                }
                            }
                        },
                        "webhook_url": callback_url,
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    agent_data = response.json()
                    return {
                        "session_id": f"session_{job_id}_{vendor_id}",
                        "agent_id": agent_data.get("agent_id", vendor_id),
                        "widget_url": f"https://elevenlabs.io/convai/widget?agent_id={agent_data.get('agent_id', vendor_id)}",
                        "webhook_url": callback_url,
                    }
        except Exception:
            pass

        return self._mock_start_session(f"{job_id}_{vendor_id}")

    async def parse_voice_transcript(self, transcript: str) -> JobSpec:
        if not self.use_real_api:
            return self._mock_parse_transcript(transcript)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/text-to-speech",
                    headers={"xi-api-key": self.api_key},
                    json={"text": transcript},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    from app.services.document_intake import DocumentIntakeService

                    parser = DocumentIntakeService()
                    return parser.parse_text_content(transcript)
        except Exception:
            pass

        return self._mock_parse_transcript(transcript)

    def _mock_start_session(self, job_id: str) -> dict:
        return {
            "session_id": f"session_{job_id}",
            "agent_id": "estimator_agent",
            "widget_url": f"https://elevenlabs.io/convai/demo?session={job_id}",
            "webhook_url": self._get_webhook_url(),
        }

    def _mock_parse_transcript(self, transcript: str) -> JobSpec:
        from app.services.document_intake import DocumentIntakeService

        parser = DocumentIntakeService()
        return parser.parse_text_content(transcript)