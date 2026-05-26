#!/usr/bin/env python3
"""
Draft a single chapter using the writer model.
Usage: python draft_chapter.py 1
       python draft_chapter.py 1 --title "My Novel"
       python draft_chapter.py 1 --state /path/to/state.json
"""
import os
import re
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
CHAPTERS_DIR = BASE_DIR / "chapters"


def get_novel_title(state_path=None):
    """Get novel title from state.json or environment, with fallback."""
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
        except (json.JSONDecodeError, IOError):
            pass
    
    title = os.environ.get("AUTONOVEL_NOVEL_TITLE", "").strip()
    if title:
        return title
    
    return "Untitled Novel"


def call_writer(prompt, max_tokens=16000):
    """Draft a single chapter of the novel."""
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
            "You are a literary fiction writer drafting a fantasy novel chapter. "
            "You write in third-person limited past tense, locked to one POV character. "
            "You follow the voice definition exactly. You hit every beat in the outline. "
            "You never use words from the banned list. You show, never tell emotions. "
            "Your prose is specific, sensory, grounded. Metaphors come from the character's "
            "experience. You vary sentence length. You trust the reader. "
            "You write the FULL chapter -- do not truncate, summarize, or skip ahead."
        ),
        "messages": [{"role": "user", "content": prompt}],
    }
    if API_BASE:
        resp = httpx.post(f"{API_BASE}/v1/messages", headers=headers, json=payload, timeout=600)
    else:
        resp = httpx.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=600)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


"""
Generic Formula: SECURE_EXCEPTION_HANDLING
Expression: λ(exception, fallback, message) → (log_warning(message), return fallback)

Parameters:
    - exception: The caught exception object
    - fallback: Value to return on error
    - message: Human-readable warning message for logging
    
Security: Always log before returning fallback to avoid silent failures.
"""
import logging
logger = logging.getLogger(__name__)

def load_file(path):
    """Load a file, returning empty string if not found. Logs warning on error."""
    try:
        return Path(path).read_text()
    except FileNotFoundError:
        logger.warning(f"File not found: {path}, returning empty string")
        return ""
    except IOError as e:
        logger.warning(f"IO error reading {path}: {e}, returning empty string")
        return ""


def extract_chapter_outline(outline_text, chapter_num):
    """Extract a specific chapter's outline entry."""
    pattern = rf'### Ch {chapter_num}:.*?(?=### Ch {chapter_num + 1}:|## Foreshadowing|$)'
    match = re.search(pattern, outline_text, re.DOTALL)
    return match.group(0).strip() if match else "(not found)"


def extract_next_chapter_outline(outline_text, chapter_num):
    """Extract the next chapter's outline (just first few lines for continuity)."""
    next_entry = extract_chapter_outline(outline_text, chapter_num + 1)
    if next_entry == "(not found)":
        return "(final chapter)"
    lines = next_entry.split('\n')[:10]
    return '\n'.join(lines)


def draft_chapter(chapter_num, novel_title):
    """Draft a single chapter with the given chapter number and novel title."""
    # Load all context
    voice = load_file(BASE_DIR / "voice.md")
    world = load_file(BASE_DIR / "world.md")
    characters = load_file(BASE_DIR / "characters.md")
    outline = load_file(BASE_DIR / "outline.md")
    canon = load_file(BASE_DIR / "canon.md")
    
    # Chapter-specific context
    chapter_outline = extract_chapter_outline(outline, chapter_num)
    next_chapter = extract_next_chapter_outline(outline, chapter_num)
    
    # Previous chapter (if exists)
    prev_path = CHAPTERS_DIR / f"ch_{chapter_num - 1:02d}.md"
    if prev_path.exists():
        prev_text = prev_path.read_text()
        prev_tail = prev_text[-2000:] if len(prev_text) > 2000 else prev_text
    else:
        prev_tail = "(first chapter -- no previous)"
    
    prompt = f"""Write Chapter {chapter_num} of "{novel_title}"

VOICE DEFINITION (follow this exactly):
{voice}

THIS CHAPTER'S OUTLINE (hit every beat):
{chapter_outline}

NEXT CHAPTER'S OUTLINE (for continuity -- end this chapter so it flows into the next):
{next_chapter}

PREVIOUS CHAPTER'S ENDING (continue from here):
{prev_tail}

WORLD BIBLE (reference for worldbuilding details):
{world}

CHARACTER REGISTRY (reference for speech patterns and behavior):
{characters}

WRITING INSTRUCTIONS:
1. Write the COMPLETE chapter. Target ~3,200 words. Do not truncate or summarize.
2. Third-person limited, past tense, locked to Cass's POV.
3. Hit ALL numbered beats from the outline in order.
4. Plant ALL foreshadowing elements listed under "Plants."
5. Show sensory detail: what Cass hears, smells, feels physically.
6. The under-note causes specific physical pain (needle behind left eye, not vague discomfort).
7. Dialogue follows the speech patterns defined in characters.md.
8. No banned words from voice.md Part 1 guardrails.
9. No AI fiction tells: no "a sense of," no "couldn't help but feel," no "eyes widened."
10. Vary sentence length. Short sentences for impact. Longer ones to build.
11. Metaphors from Cass's experience: sound, bronze, craft, the body's response to pitch.
12. Trust the reader. Don't explain what scenes mean. Let them land.
13. Start the chapter in scene, not with exposition. End on a moment, not a summary.

PATTERNS TO AVOID (these have been flagged in previous chapters):
14. NO triadic sensory lists. Never "X. Y. Z." or "X and Y and Z" as three
    separate items in a row. Combine two, cut one, or restructure.
15. NO "He did not [verb]" more than once per chapter. Convert negatives
    to active alternatives or just cut them.
16. NO "He thought about [X]" constructions. Replace with: the thought
    itself as a fragment, a physical action, or dialogue.
17. NO "the way [X] did [Y]" as a simile connector more than twice per
    chapter. Use different simile structures or cut the comparison.
18. NO over-explaining after showing. If a scene demonstrates something,
    do not have the narrator restate it. Trust the scene.
19. NO section breaks (---) as rhythm crutches. Only use for genuine
    time/location jumps. Max 2 per chapter.
20. VARY paragraph length deliberately. Never more than 3 consecutive
    paragraphs of similar length. Include at least one 1-2 sentence
    paragraph and one 6+ sentence paragraph.
21. END the chapter differently from previous chapters. Do NOT end with
    Cass outside listening to his father work. Find the ending that
    belongs to THIS chapter specifically.
22. INCLUDE at least one moment that surprises -- a character saying
    the wrong thing, an emotional beat arriving early or late, a detail
    that doesn't fit the expected pattern. Predictable excellence is
    still predictable.
23. FAVOR scene over summary. At least 70% of the chapter should be
    in-scene (moment by moment, with dialogue and action) rather than
    summary (narrator compressing time).
24. DIALOGUE should sound like speech, not prose. Characters should
    occasionally stumble, interrupt, trail off, or say something
    slightly wrong. A 14-year-old does not speak in polished epigrams.

Write the chapter now. Full text, beginning to end.
"""

    print(f"Drafting Chapter {chapter_num} of \"{novel_title}\"...", file=sys.stderr)
    result = call_writer(prompt)
    
    # Save
    out_path = CHAPTERS_DIR / f"ch_{chapter_num:02d}.md"
    out_path.write_text(result)
    print(f"Saved to {out_path}", file=sys.stderr)
    print(f"Word count: {len(result.split())}", file=sys.stderr)
    print(result)


def main():
    parser = argparse.ArgumentParser(description="Draft a chapter")
    parser.add_argument("chapter", type=int, help="Chapter number")
    parser.add_argument("--title", type=str, default=None, help="Override novel title")
    parser.add_argument("--state", type=str, default=None, help="Path to state.json")
    args = parser.parse_args()
    
    chapter_num = args.chapter
    novel_title = args.title if args.title else get_novel_title(args.state)
    
    draft_chapter(chapter_num, novel_title)


if __name__ == "__main__":
    main()