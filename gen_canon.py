#!/usr/bin/env python3
"""
Generate canon.md by extracting all hard facts from world.md + characters.md.
"""
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

def call_writer(prompt, max_tokens=16000):
    return call_llm(
        system=("You are a continuity editor extracting hard facts from fantasy novel "
            "planning documents. You are precise, exhaustive, and never invent facts "
            "that aren't in the source material. Every entry must be traceable to a "
            "specific statement in the source documents."),
        prompt=prompt,
        model=WRITER_MODEL,
        max_tokens=max_tokens,
        temperature=0.2,
        api_base=API_BASE,
        api_key=API_KEY,
    )
world = (BASE_DIR / "world.md").read_text()
characters = (BASE_DIR / "characters.md").read_text()
seed = (BASE_DIR / "seed.txt").read_text()

prompt = f"""Extract EVERY hard fact from these planning documents into a structured canon database.
A "hard fact" is anything a writer must not contradict: names, ages, dates, physical descriptions,
rules of the magic system, geography, relationships, established events.

SOURCE DOCUMENTS:

=== SEED.TXT ===
{seed}

=== WORLD.MD ===
{world}

=== CHARACTERS.MD ===
{characters}

FORMAT THE OUTPUT AS CANON.MD with these categories:

## Geography
- Specific facts about locations, distances, physical properties

## Timeline
- Dated events, ages, durations

## Magic System Rules
- Hard rules of Tonal Law (intervals, costs, limitations)
- Cass's gift specifics

## Character Facts
- Ages, physical descriptions, habits, relationships
- One entry per fact (not paragraphs)

## Political / Factional
- Who controls what, alliances, conflicts, contracts

## Cultural
- Customs, taboos, laws, festivals, food, clothing

## Established In-Story
- Events that have already happened in the story's past
- The Perin contract, the Expansion Wars, etc.

RULES:
- One fact per bullet point. Short. Specific. Checkable.
- Include the source (world.md or characters.md) in parentheses after each fact.
- Aim for 80-120 entries minimum. Be exhaustive.
- If two documents give slightly different details, note the discrepancy.
- DO NOT invent facts. Only record what's explicitly stated.
"""

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
print(result)
