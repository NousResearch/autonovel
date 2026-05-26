#!/usr/bin/env python3
"""
Revision chapter generator. Rewrites a chapter from a specific revision brief.
Usage: python gen_revision.py <chapter_num> <brief_file>
       python gen_revision.py <chapter_num> <brief_file> --title "My Novel"
"""
import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")


def get_novel_title(state_path=None):
    """Get novel title from state.json or environment, with fallback."""
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)
    
    if state_path is None:
        state_path = BASE_DIR / "state.json"
    else:
        state_path = Path(state_path)
    
    if state_path.exists():
        try:
            with open(state_path) as f:
                state = json.load(f)
            title = state.get("novel_title", "").strip()
            if title:
                return title
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load title from {state_path}: {e}")
    
    title = os.environ.get("AUTONOVEL_NOVEL_TITLE", "").strip()
    if title:
        return title
    
    return "Untitled Novel"


def call_writer(prompt, max_tokens=16000):
    """Rewrite a chapter based on revision brief."""
    import httpx
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "context-1m-2025-08-07",
        "content-type": "application/json",
    }
    payload = {
        "model": WRITER_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.8,
        "system": (
            "You are rewriting a fantasy novel chapter based on a specific revision brief. "
            "You follow the brief exactly. You preserve the voice, world, and characters "
            "from the existing draft while making the structural changes specified. "
            "You write the FULL chapter. Do not truncate or summarize."
        ),
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = httpx.post(f"{API_BASE}/v1/messages", headers=headers, json=payload, timeout=600)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def rewrite_chapter(ch_num, brief_file, novel_title):
    """Rewrite a chapter with the given revision brief and novel title."""
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
    
    prompt = f"""Rewrite Chapter {ch_num} of "{novel_title}"

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

    print(f"Rewriting Chapter {ch_num} of \"{novel_title}\"...", file=sys.stderr)
    result = call_writer(prompt)
    
    out_path = BASE_DIR / "chapters" / f"ch_{ch_num:02d}.md"
    out_path.write_text(result)
    print(f"Saved to {out_path}", file=sys.stderr)
    print(f"Word count: {len(result.split())}", file=sys.stderr)
    print(result)


def main():
    parser = argparse.ArgumentParser(description="Rewrite a chapter from revision brief")
    parser.add_argument("chapter", type=int, help="Chapter number")
    parser.add_argument("brief_file", type=str, help="Path to revision brief file")
    parser.add_argument("--title", type=str, default=None, help="Override novel title")
    parser.add_argument("--state", type=str, default=None, help="Path to state.json")
    args = parser.parse_args()
    
    novel_title = args.title if args.title else get_novel_title(args.state)
    rewrite_chapter(args.chapter, args.brief_file, novel_title)


if __name__ == "__main__":
    main()