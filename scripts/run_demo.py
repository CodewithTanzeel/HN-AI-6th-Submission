#!/usr/bin/env python3
"""Run the end-to-end demo flow against the local API."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

BASE_URL = "http://127.0.0.1:8000"


async def run_demo() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        job = (await client.post("/api/jobs")).json()
        job_id = job["id"]
        print(f"Created job {job_id}")

        await client.post(
            f"/api/jobs/{job_id}/voice",
            json={
                "transcript": (
                    "Moving from Rock Hill to Charlotte, 45 miles, "
                    "2 bedroom apartment, 2 flights of stairs"
                )
            },
        )
        files = {"file": ("quote.txt", b"Rock Hill to Charlotte 45 miles piano packing 2 bedroom", "text/plain")}
        await client.post(f"/api/jobs/{job_id}/documents", files=files)
        await client.post(f"/api/jobs/{job_id}/confirm", json={})
        calls = (await client.post(f"/api/jobs/{job_id}/calls")).json()
        print(f"Collected {len(calls['quotes'])} quotes")
        negotiation = (await client.post(f"/api/jobs/{job_id}/negotiate")).json()
        changed = [n for n in negotiation["negotiations"] if n["changed"]]
        print(f"Negotiations changed: {len(changed)}")
        report = (await client.get(f"/api/jobs/{job_id}/report")).json()
        print(report["summary"])


if __name__ == "__main__":
    asyncio.run(run_demo())
