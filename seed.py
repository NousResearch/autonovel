#!/usr/bin/env python3
"""
seed.py -- Generate fantasy novel seed concepts.

Usage:
  uv run python seed.py              # Generate 10 concepts, pick one
  uv run python seed.py --count=5    # Generate 5 concepts
  uv run python seed.py --riff "magic costs memories"  # Riff on an idea
"""

import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from llm_client import call_llm

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "openrouter/nex-agi/nex-n2-pro:free")
API_KEY = os.environ.get("AUTONOVEL_API_KEY", os.environ.get("ANTHROPIC_API_KEY", "local"))
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "http://localhost:20128/v1")
ANTHROPIC_BETA = "context-1m-2025-08-07"


def call_writer(prompt, max_tokens=16000):
    return call_llm(
        system=("You are a fantasy novelist with deep knowledge of the genre's "
            "best works -- Tolkien, Le Guin, Rothfuss, Wolfe, Jemisin, Peake, "
            "Susanna Clarke, Andrew Peterson, Sofia Samatar. You generate "
            "novel concepts that are SPECIFIC, SURPRISING, and STRUCTURALLY "
            "SOUND. You never propose generic medieval Europe + elves. Each "
            "concept should make a reader think 'I've never seen THAT before.'"),
        prompt=prompt,
        model=WRITER_MODEL,
        max_tokens=max_tokens,
        temperature=1.0,
        api_base=API_BASE,
        api_key=API_KEY,
    )


def main():
    parser = argparse.ArgumentParser(description="Generate novel seed concepts")
    parser.add_argument("--count", type=int, default=10,
                        help="Number of concepts to generate (default: 10)")
    parser.add_argument("--riff", type=str, default=None,
                        help="Riff on an existing idea")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: Set API_KEY in .env first")
        sys.exit(1)

    if args.riff:
        print(f"Riffing on: {args.riff}\n")
        prompt = RIFF_PROMPT.format(idea=args.riff)
    else:
        print(f"Generating {args.count} seed concepts...\n")
        prompt = GENERATE_PROMPT.format(count=args.count)

    result = call_writer(prompt, max_tokens=8000)
    print(result)
    print("\n" + "=" * 60)
    print("To pick a seed, copy the concept you like into seed.txt:")
    print("  nano seed.txt")
    print("Or remix several concepts into your own seed.")
    print("Then proceed to Step 2 in WORKFLOW.md.")


if __name__ == "__main__":
    main()
