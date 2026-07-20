#!/usr/bin/env python3
"""
Validate ElevenLabs API key and test connectivity.
"""

import asyncio
import httpx
import sys
from pathlib import Path


async def validate_elevenlabs_key(api_key: str) -> bool:
    """Test if the API key is valid for ElevenLabs."""
    if not api_key:
        print("No API key provided")
        return False
    
    print(f"Testing API key: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        async with httpx.AsyncClient() as client:
            # Try the user endpoint to validate key
            response = await client.get(
                "https://api.elevenlabs.io/v1/user",
                headers={"xi-api-key": api_key},
                timeout=10.0,
            )
            
            if response.status_code == 200:
                print("API key is valid for ElevenLabs!")
                data = response.json()
                print(f"   Subscription: {data.get('subscription', {}).get('tier', 'unknown')}")
                return True
            elif response.status_code == 401:
                print("Invalid API key - authentication failed")
                return False
            else:
                print(f"Unexpected response: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"Error testing API key: {e}")
        return False


async def validate_openai_key(api_key: str) -> bool:
    """Test if the API key is valid for OpenAI."""
    if not api_key:
        print("No API key provided")
        return False
    
    print(f"Testing OpenAI key: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0,
            )
            
            if response.status_code == 200:
                print("OpenAI API key is valid!")
                return True
            elif response.status_code == 401:
                print("Invalid OpenAI API key")
                return False
            else:
                print(f"Unexpected response: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"Error testing OpenAI key: {e}")
        return False


def main():
    # Read keys from .env
    env_path = Path(__file__).parent.parent / ".env"
    env_content = env_path.read_text()
    
    elevenlabs_key = ""
    openai_key = ""
    
    for line in env_content.split("\n"):
        if line.startswith("ELEVENLABS_API_KEY="):
            elevenlabs_key = line.split("=", 1)[1].strip()
        elif line.startswith("OPENAI_API_KEY="):
            openai_key = line.split("=", 1)[1].strip()
    
    print("=" * 60)
    print("API Key Validation")
    print("=" * 60)
    
    if elevenlabs_key:
        print("\nValidating ElevenLabs key...")
        result = asyncio.run(validate_elevenlabs_key(elevenlabs_key))
    else:
        print("\nNo ElevenLabs API key found in .env")
    
    if openai_key:
        print("\nValidating OpenAI key...")
        result = asyncio.run(validate_openai_key(openai_key))
    else:
        print("\nNo OpenAI API key found in .env")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()