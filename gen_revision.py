#!/usr/bin/env python3
"""
Revision chapter generator. Rewrites a chapter from a specific revision brief.
Usage: python gen_revision.py <chapter_num> <brief_file>
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
        system=("You are rewriting a fantasy novel chapter based on a specific revision brief. "
            "You follow the brief exactly. You preserve the voice, world, and characters "
            "from the existing draft while making the structural changes specified. "
            "You write the FULL chapter. Do not truncate or summarize."),
        prompt=prompt,
        model=WRITER_MODEL,
        max_tokens=max_tokens,
        temperature=0.8,
        api_base=API_BASE,
        api_key=API_KEY,
    )
def main():
    ch_num = int(sys.argv[1])
    brief_file = sys.argv[2]
    
    voice = (BASE_DIR / "voice.md").read_text()
    characters = (BASE_DIR / "characters.md").read_text()
    world = (BASE_DIR / "world.md").read_text()
    brief = Path(brief_file).read_text()
    
    # Load adjacent chapters for continuity
    prev_path = BASE_DIR / "chapters" / f"ch_{ch_num - 1:02d}.md"
    next_path = BASE_DIR / "chapters" / f"ch_{ch_num + 1:02d}.md"
    prev_tail = prev_path.read_text()[-2000:] if prev_path.exists() else "(first chapter)"
    next_head = next_path.read_text()[:1500] if next_path.exists() else "(last chapter)"
    
    # Load old version if exists
    old_path = BASE_DIR / "chapters" / f"ch_{ch_num:02d}.md"
    old_text = old_path.read_text() if old_path.exists() else "(no existing draft)"
    
    prompt = f"""Rewrite Chapter {ch_num} of "The Second Son of the House of Bells."

REVISION BRIEF (follow this exactly):
{brief}

VOICE DEFINITION:
{voice}

CHARACTER REGISTRY:
{characters}

WORLD BIBLE:
{world}

PREVIOUS CHAPTER ENDING (maintain continuity):
{prev_tail}

NEXT CHAPTER OPENING (end so this flows into it):
{next_head}

THE EXISTING DRAFT (use as raw material -- keep what works, cut what doesn't):
{old_text}

ANTI-PATTERN RULES:
- NO triadic sensory lists (X. Y. Z.)
- NO "He did not [verb]" more than once
- NO "He thought about [X]" constructions
- NO "the way [X] did [Y]" more than twice
- NO "not X, but Y" formula in narration
- NO over-explaining after showing
- MAX 2 section breaks
- At least one moment that genuinely surprises
- 70%+ in-scene (dialogue and action, not summary)
- Dialogue should sound like speech, not prose

Write the FULL revised chapter now."""

    print(f"Rewriting Chapter {ch_num}...", file=sys.stderr)
    result = call_writer(prompt)
    
    out_path = BASE_DIR / "chapters" / f"ch_{ch_num:02d}.md"
    out_path.write_text(result)
    print(f"Saved to {out_path}", file=sys.stderr)
    print(f"Word count: {len(result.split())}", file=sys.stderr)

if __name__ == "__main__":
    main()
