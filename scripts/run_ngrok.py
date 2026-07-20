#!/usr/bin/env python3
"""
Ngrok launcher script for The Negotiator project.
This script starts ngrok and updates the environment dynamically.
"""

import os
import re
import subprocess
import time
import requests
from pathlib import Path


def get_ngrok_url() -> str | None:
    """Get the public URL from ngrok API."""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get("tunnels", [])
            if tunnels:
                return tunnels[0].get("public_url")
    except Exception:
        pass
    return None


def wait_for_ngrok(max_wait: int = 10) -> str | None:
    """Wait for ngrok to be ready and return the URL."""
    for _ in range(max_wait):
        url = get_ngrok_url()
        if url:
            return url
        time.sleep(1)
    return None


def main():
    print("=" * 60)
    print("The Negotiator - Ngrok Launcher")
    print("=" * 60)
    
    # Check if ngrok is installed
    try:
        result = subprocess.run(["ngrok", "version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ ngrok not found. Please install it first:")
            print("   https://ngrok.com/download")
            return
        print(f"✅ ngrok found: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ ngrok not installed. Please install from: https://ngrok.com/download")
        return
    
    # Start ngrok for port 8000
    print("\n🚀 Starting ngrok on port 8000...")
    ngrok_process = subprocess.Popen(
        ["ngrok", "http", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for ngrok to be ready
    ngrok_url = wait_for_ngrok()
    
    if not ngrok_url:
        print("❌ Failed to get ngrok URL. Is port 8000 in use?")
        return
    
    print(f"✅ Ngrok URL: {ngrok_url}")
    
    # Update .env with ngrok URL
    root = Path(__file__).parent.parent
    env_path = root / ".env"
    
    if env_path.exists():
        content = env_path.read_text()
        # Update or add NGROK_URL
        if "NGROK_URL=" in content:
            content = re.sub(r"NGROK_URL=.*", f"NGROK_URL={ngrok_url}", content)
        else:
            content += f"\nNGROK_URL={ngrok_url}\n"
        env_path.write_text(content)
        print(f"✅ Updated {env_path} with NGROK_URL")
    
    # Create frontend .env.local
    frontend_env = root / "frontend" / ".env.local"
    frontend_env.write_text(f"NEXT_PUBLIC_API_URL={ngrok_url}\n")
    print(f"✅ Created {frontend_env}")
    
    print("\n" + "=" * 60)
    print("Ngrok is running! Use this URL in ElevenLabs:")
    print(f"  {ngrok_url}")
    print("=" * 60)
    print("\nPress Ctrl+C to stop ngrok...")
    
    try:
        ngrok_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping ngrok...")
        ngrok_process.terminate()


if __name__ == "__main__":
    main()