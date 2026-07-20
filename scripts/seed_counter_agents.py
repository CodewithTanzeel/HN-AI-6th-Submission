#!/usr/bin/env python3
"""Print counterparty persona definitions from vertical config."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.config.loader import load_vertical_config

CONFIG = Path(__file__).resolve().parents[1] / "config" / "verticals" / "moving.yaml"


def main() -> None:
    config = load_vertical_config(CONFIG)
    for cp in config.counterparties:
        print(f"- {cp.id}: {cp.name} ({cp.negotiation_style})")


if __name__ == "__main__":
    main()
