#!/usr/bin/env python3
"""
Parse novel chapters into speaker-attributed audiobook scripts.

For each chapter, uses Claude to:
  - Identify every dialogue line and its speaker
  - Tag narration as NARRATOR
  - Add [audio tags] for emotional delivery based on context

Usage:
  python gen_audiobook_script.py           # All chapters
  python gen_audiobook_script.py 1         # Single chapter
  python gen_audiobook_script.py 1 5       # Range of chapters
"""
import os
import sys
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from llm_client import call_llm

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env", override=True)

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "openrouter/nex-agi/nex-n2-pro:free")
API_KEY = os.environ.get("AUTONOVEL_API_KEY", os.environ.get("ANTHROPIC_API_KEY", "local"))
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "http://localhost:20128/v1")

CHAPTERS_DIR = BASE_DIR / "chapters"
AUDIO_DIR = BASE_DIR / "audiobook"
SCRIPTS_DIR = AUDIO_DIR / "scripts"

# Characters from the novel
CHARACTERS = {
    "NARRATOR": "The narrative voice — warm, measured, precise. Reads prose with the rhythm of the novel's world.",
    "CASS": "14-year-old boy. Dry, sharp, sometimes frustrated. His voice tightens when he lies or holds back.",
    "EDDAN": "52, Cass's father. Deep, rough, terse. Sentences often trail off or restart. Workshop voice is steadier than kitchen voice.",
    "PERIN": "26, Cass's brother. Dry, precise, carries something heavy. Letters-voice is more controlled than in-person voice.",
    "LENNE": "14, female. Quick, confident, intellectually sharp. Composes while she talks — fingers moving, voice certain.",
    "TORVALD": "63, retired dye merchant. Gravelly, warm, rambling. Outer-district speech — longer sentences, less careful, trade metaphors.",
    "MARET": "60, female. Controlled, precise, still. No wasted words. When she finally shows emotion it's devastating.",
    "DAV_SORN": "34, Court Singer. Formal, clipped, self-correcting. Starts sentences and abandons them. Qualifying everything.",
    "PROCTOR_FEN": "Male, middle-aged, Academy teacher. Dry, archly amused, pedagogical.",
    "FERREN": "40, acoustician. Clinical, measured, professional.",
    "MIRA_FEN": "60s, female, Academy scholar. Quiet, precise, carrying thirty years of regret.",
    "VELLA": "Lenne's mother, Court Singer. Measured, formal, the weight of knowing she's about to risk everything.",
    "OSSIAN": "14, male student. Nervous, eager, tends to overstate.",
}

AUDIO_TAG_GUIDE = """
Available ElevenLabs v3 audio tags (use sparingly, only when the emotion is CLEAR):

Emotions: [happy] [sad] [angry] [excited] [nervous] [calm] [worried] [frustrated] [hopeful] [tense]
Delivery: [whisper] [softly] [firmly] [hesitantly] [sarcastically] [matter-of-factly] [gently]
Reactions: [gasp] [sigh] [laughs] [clears throat]
Volume: [quietly] [loudly]
Pacing: [slowly] [quickly] [pause]

Rules:
- Narration: use tags VERY sparingly. Mostly just read it straight. Use [softly] for tender moments, [slowly] for revelations, [tense] for suspense.
- Dialogue: use tags to match the speaker's emotional state in context. A worried father sounds different from an angry teenager.
- Don't over-tag. One tag per segment is usually enough. None is fine for neutral delivery.
- [pause] before revelations or after devastating lines.
- [whisper] for secrets, locked-room scenes, late-night moments.
"""


def call_claude(prompt, max_tokens=8000):
    return call_llm(
        system='You are parsing a novel chapter into an audiobook script. Break text into speaker-attributed segments and optional audio tags.',
        prompt=prompt,
        model=WRITER_MODEL,
        max_tokens=max_tokens,
        temperature=0.1,
        api_base=API_BASE,
        api_key=API_KEY,
    )
def parse_chapter(ch_num):
    """Parse a chapter into speaker-attributed segments."""
    ch_path = CHAPTERS_DIR / f"ch_{ch_num:02d}.md"
    if not ch_path.exists():
        print(f"  Chapter {ch_num} not found", file=sys.stderr)
        return None

    text = ch_path.read_text()
    title = text.split("\n")[0].lstrip("# ").strip()
    wc = len(text.split())

    prompt = f"""You are parsing a novel chapter into an audiobook script. Your job is to break the text into segments, each attributed to a speaker, with optional audio delivery tags.

CHARACTERS IN THIS NOVEL:
{json.dumps(CHARACTERS, indent=2)}

AUDIO TAG GUIDE:
{AUDIO_TAG_GUIDE}

RULES:
1. Every piece of text must be attributed to a speaker. Narration = "NARRATOR".
2. Dialogue lines must be attributed to the character who speaks them.
3. Remove quotation marks from dialogue — the voice actor performs them.
4. Keep narration segments reasonably sized (2-4 sentences each). Split long paragraphs.
5. Dialogue "he said" / "she said" tags should be part of the NARRATOR segment AFTER the dialogue, not part of the character's line.
6. Scene breaks (---) become {{"speaker": "NARRATOR", "text": "[pause]"}}
7. Chapter titles become the first segment: {{"speaker": "NARRATOR", "text": "[slowly] Chapter One: The Morning Pitch"}}
8. Add audio tags based on emotional context. Be subtle — most lines need no tag.
9. Internal thoughts in *italics* should be read by the CHARACTER (Cass usually), tagged [softly] or [whisper].

OUTPUT FORMAT: A JSON array of objects, each with:
  "speaker": character name (from the list above)
  "text": the text to speak (with optional [audio tags] at the start)

CHAPTER {ch_num}: "{title}" ({wc} words)

{text}

Output the JSON array only. No other text."""

    print(f"  Ch {ch_num}: parsing '{title}' ({wc}w)...", end="", flush=True)
    result = call_claude(prompt)

    # Extract JSON from response
    result = result.strip()
    if result.startswith("```"):
        result = re.sub(r'^```\w*\n?', '', result)
        result = re.sub(r'\n?```$', '', result)

    try:
        segments = json.loads(result)
    except json.JSONDecodeError:
        # Try to fix common JSON issues from LLM output
        # 1. Remove trailing commas before ] or }
        cleaned = re.sub(r',\s*([}\]])', r'\1', result)
        # 2. Fix unescaped newlines in strings
        cleaned = cleaned.replace('\n', '\\n')
        # 3. Re-add structural newlines (between array elements)
        cleaned = cleaned.replace('\\n{', '\n{').replace('\\n]', '\n]')
        try:
            segments = json.loads(cleaned)
        except json.JSONDecodeError:
            # Last resort: extract individual objects
            print(f" (fixing JSON...)", end="", flush=True)
            segments = []
            for m in re.finditer(r'\{\s*"speaker"\s*:\s*"([^"]+)"\s*,\s*"text"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}', result):
                segments.append({
                    "speaker": m.group(1),
                    "text": m.group(2).replace('\\n', '\n').replace('\\"', '"'),
                })
            if not segments:
                print(f" PARSE ERROR", file=sys.stderr)
                (SCRIPTS_DIR / f"ch{ch_num:02d}_raw.txt").write_text(result)
                return None

    print(f" → {len(segments)} segments")
    return {
        "chapter": ch_num,
        "title": title,
        "segments": segments,
        "total_segments": len(segments),
        "speakers": list(set(s["speaker"] for s in segments)),
        "total_chars": sum(len(s["text"]) for s in segments),
    }


def main():
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    # Parse args for chapter range
    chapters = sorted(CHAPTERS_DIR.glob("ch_*.md"))
    total = len(chapters)

    if len(sys.argv) == 2:
        start = end = int(sys.argv[1])
    elif len(sys.argv) == 3:
        start, end = int(sys.argv[1]), int(sys.argv[2])
    else:
        start, end = 1, total

    print(f"Parsing chapters {start}-{end} into audiobook scripts...")

    all_scripts = []
    for ch_num in range(start, end + 1):
        script = parse_chapter(ch_num)
        if script:
            # Save individual chapter script
            out_path = SCRIPTS_DIR / f"ch{ch_num:02d}_script.json"
            out_path.write_text(json.dumps(script, indent=2))
            all_scripts.append(script)

    # Summary
    print(f"\n{'='*50}")
    print(f"AUDIOBOOK SCRIPT SUMMARY")
    print(f"  Chapters: {len(all_scripts)}")
    total_segs = sum(s["total_segments"] for s in all_scripts)
    total_chars = sum(s["total_chars"] for s in all_scripts)
    all_speakers = set()
    for s in all_scripts:
        all_speakers.update(s["speakers"])
    print(f"  Total segments: {total_segs}")
    print(f"  Total characters: {total_chars:,}")
    print(f"  Speakers found: {sorted(all_speakers)}")
    print(f"  Scripts saved to: {SCRIPTS_DIR}/")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
