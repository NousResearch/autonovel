#!/usr/bin/env python3
"""
One-shot world.md generator for foundation phase.
Reads seed.txt + voice.md, calls the writer model, outputs world.md content.
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
        system=("You are a fantasy worldbuilder with deep knowledge of Sanderson's Laws, "
            "Le Guin's prose philosophy, and TTRPG-quality lore design. "
            "You write world bibles that are specific, interconnected, and imply depth "
            "beyond what's stated. You never use AI slop words (delve, tapestry, myriad, etc). "
            "You write in clean, direct prose. Every rule has a cost. Every cultural detail "
            "implies a history. Every location has a sensory signature."),
        prompt=prompt,
        model=WRITER_MODEL,
        max_tokens=max_tokens,
        temperature=0.7,
        api_base=API_BASE,
        api_key=API_KEY,
    )
seed = (BASE_DIR / "seed.txt").read_text()
voice = (BASE_DIR / "voice.md").read_text()
craft = (BASE_DIR / "CRAFT.md").read_text()

# Extract voice Part 2 only (the novel-specific voice)
voice_lines = voice.split('\n')
part2_start = next(i for i, l in enumerate(voice_lines) if 'Part 2' in l)
voice_part2 = '\n'.join(voice_lines[part2_start:])

prompt = f"""Build a complete world bible for this fantasy novel. This is the WORLD.MD file -- 
the definitive reference for everything that EXISTS in this world. A writer should be able 
to resolve any worldbuilding question from this document alone.

SEED CONCEPT:
{seed}

VOICE IDENTITY (the tone and register of this novel):
{voice_part2}

CRAFT REQUIREMENTS (from CRAFT.md -- follow these):
- Magic system needs HARD RULES with COSTS and LIMITATIONS per Sanderson's Second Law
- Limitations >= powers in narrative prominence
- Trace implications of magic through society, economy, law, religion
- At least 2-3 societal implications of magic explored in depth
- History must create PRESENT-DAY TENSIONS that drive the plot (not just backdrop)
- Geography must be specific and sensory (not generic fantasy)
- Iceberg principle: imply more than you state
- Interconnection: pulling one thread should move everything

STRUCTURE THE DOCUMENT WITH THESE SECTIONS:

## Cosmology & History
A timeline of major events. Focus on events that create PRESENT-DAY tensions.
Include the founding myth, key turning points, and recent events that matter to the plot.

## Magic System
### Hard Rules (Tonal Law)
Specific, testable rules. What intervals do what. What progressions bind.
What happens when you break the rules. Include COSTS and LIMITATIONS prominently.

### Soft Magic (Cass's Gift)
What he perceives, how it works, what it costs HIM specifically.
This should be mysterious but have consistent internal logic.

### Societal Implications
How does tonal law shape: governance, commerce, education, class structure,
crime, family life, childhood, aging, disability?

## Geography
Cantamura's physical layout, districts, the natural amphitheater's acoustic properties.
Neighboring places (at least 2-3). Sensory signatures for each location.

## Factions & Politics
Who holds power, who wants it, who's being crushed by it.
At least 3-4 factions with opposing interests.

## Bestiary / Flora / Natural World
What's unique about the natural world in and around Cantamura?

## Cultural Details
Customs, taboos, festivals, food, clothing, coming-of-age rituals.
Things that make daily life feel SPECIFIC.

## Internal Consistency Rules
Hard constraints a writer must not violate. The physics of sound in this world.
What's possible and what's not.

IMPORTANT:
- Be SPECIFIC. Not "the city has districts" but name them, describe them, 
  give them sensory signatures.
- Every rule should have a COST or LIMITATION stated alongside it.
- Include 2-3 facts per section that are unexplained, hinting at deeper systems 
  (iceberg depth).
- Facts should INTERCONNECT: the magic should shape the politics, the geography 
  should shape the culture, the history should explain current faction conflicts.
- Write in clean, direct prose. No AI slop. No "rich tapestry." No "delving."
- The world should feel grounded and LIVED-IN, not imagined. Think: what does 
  breakfast smell like? What do children play? How do old people complain?
- Target ~3000-4000 words. Dense, not padded.
"""

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
print(result)
