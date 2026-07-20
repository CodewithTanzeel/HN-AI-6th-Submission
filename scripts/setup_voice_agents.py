#!/usr/bin/env python3
"""
Setup script for ElevenLabs Voice Agent Integration
This script helps configure the environment and validate API keys.
"""

import os
import re
from pathlib import Path


def validate_api_key(key: str, key_type: str) -> bool:
    """Validate API key format."""
    if key_type == "elevenlabs":
        return key.startswith("xi_") and len(key) > 10
    elif key_type == "openai":
        return key.startswith("sk_") and len(key) > 10
    return False


def update_env_file(env_path: Path, updates: dict) -> None:
    """Update .env file with new values."""
    content = env_path.read_text() if env_path.exists() else ""
    
    for key, value in updates.items():
        pattern = f"^{key}=.*"
        if re.search(pattern, content, re.MULTILINE):
            content = re.sub(pattern, f"{key}={value}", content)
        else:
            content += f"\n{key}={value}"
    
    env_path.write_text(content.strip() + "\n")


def main():
    print("=" * 60)
    print("ElevenLabs Voice Agent Setup")
    print("=" * 60)
    
    # Get API keys from user
    print("\n📝 Enter your API keys (press Enter to skip):")
    
    elevenlabs_key = input("ElevenLabs API Key (xi_...): ").strip()
    openai_key = input("OpenAI API Key (sk_...): ").strip()
    
    # Validate keys
    if elevenlabs_key and not validate_api_key(elevenlabs_key, "elevenlabs"):
        print("⚠️  Warning: ElevenLabs key should start with 'xi_'")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != "y":
            elevenlabs_key = ""
    
    if openai_key and not validate_api_key(openai_key, "openai"):
        print("⚠️  Warning: OpenAI key should start with 'sk_'")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != "y":
            openai_key = ""
    
    # Update .env file
    root = Path(__file__).parent.parent
    env_path = root / ".env"
    
    updates = {}
    if elevenlabs_key:
        updates["ELEVENLABS_API_KEY"] = elevenlabs_key
    if openai_key:
        updates["OPENAI_API_KEY"] = openai_key
    
    if updates:
        update_env_file(env_path, updates)
        print(f"\n✅ Updated {env_path}")
    
    # Update frontend .env.local
    frontend_env = root / "frontend" / ".env.local"
    if elevenlabs_key:
        update_env_file(frontend_env, {"NEXT_PUBLIC_ELEVENLABS_API_KEY": elevenlabs_key})
        print(f"✅ Updated {frontend_env}")
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Create agents in ElevenLabs dashboard:")
    print("   https://elevenlabs.io/app/conversational-ai")
    print("\n2. Start the backend:")
    print("   uvicorn app.main:app --app-dir backend --reload")
    print("\n3. Start the frontend:")
    print("   cd frontend && npm run dev")
    print("\n4. Test at: http://localhost:3000/intake/voice")


if __name__ == "__main__":
    main()