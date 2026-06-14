#!/usr/bin/env python3
"""
One-shot characters.md generator for foundation phase.
Reads seed.txt + voice.md + world.md + CRAFT.md, calls writer model.
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
        system=("You are a character designer for literary fiction with deep knowledge of "
            "wound/want/need/lie frameworks, Sanderson's three sliders, and dialogue "
            "distinctiveness. You create characters who feel like real people with "
            "contradictions, secrets, and speech patterns you can hear. "
            "You never use AI slop words. You write in clean, direct prose."),
        prompt=prompt,
        model=WRITER_MODEL,
        max_tokens=max_tokens,
        temperature=0.7,
        api_base=API_BASE,
        api_key=API_KEY,
    )
seed = (BASE_DIR / "seed.txt").read_text()
world = (BASE_DIR / "world.md").read_text()

# Voice Part 2 only
voice = (BASE_DIR / "voice.md").read_text()
voice_lines = voice.split('\n')
part2_start = next(i for i, l in enumerate(voice_lines) if 'Part 2' in l)
voice_part2 = '\n'.join(voice_lines[part2_start:])

prompt = f"""Build a complete character registry for this fantasy novel. This is CHARACTERS.MD --
the definitive reference for WHO exists in this story, what drives them, how they speak,
and what secrets they carry.

SEED CONCEPT:
{seed}

WORLD BIBLE (the world these characters inhabit):
{world}

VOICE IDENTITY (the novel's tone):
{voice_part2}

CHARACTER CRAFT REQUIREMENTS (from CRAFT.md):

### The Three Sliders (Sanderson)
Every character has three independent dials (0-10):
  PROACTIVITY -- Do they drive the plot or react to it?
  LIKABILITY  -- Does the reader empathize with them?
  COMPETENCE  -- Are they good at what they do?
Rule: compelling = HIGH on at least TWO, or HIGH on one with clear growth.

### Wound / Want / Need / Lie Framework
A causal chain:
  GHOST (backstory event) -> WOUND (ongoing damage) -> LIE (false belief to cope)
    -> WANT (external goal driven by Lie) -> NEED (internal truth, opposes Lie)
Rules: Want and Need must be IN TENSION. Lie statable in one sentence.
  Truth is its direct opposite.

### Dialogue Distinctiveness (8 dimensions)
1. Vocabulary level  2. Sentence length  3. Contractions/formality
4. Verbal tics  5. Question vs statement ratio  6. Interruption patterns
7. Metaphor domain  8. Directness vs indirectness
Test: Remove dialogue tags. Can you tell who's speaking?

BUILD THE REGISTRY WITH AT LEAST THESE CHARACTERS:

1. **Cass Bellwright** (protagonist, POV character)
   - Full wound/want/need/lie chain
   - Three sliders with justification
   - Arc type (positive/negative/flat)
   - Detailed speech pattern (8 dimensions)
   - Physical habits and tells
   - At least 2 secrets
   - Key relationships mapped

2. **Eddan Bellwright** (father)
   - Same depth as Cass
   - His relationship to the sealed journals, the shaking hands
   - What he knows and what he's hiding

3. **Perin Bellwright** (brother) 
   - Even though he's absent for much of the story, he needs full depth
   - What actually happened with the Corda contract
   - His presence through absence

4. **Maret Corda** (antagonist)
   - Not a villain -- someone whose interests conflicts with Cass's
   - Her own wound/want/need/lie (she should be understandable)

5. **Rector Suvaine** (Academy Chancellor)
   - The institutional antagonist -- the system personified
   - She believes she's protecting Cantamura

6. **Torvald Hess** (Compact leader)
   - The outsider perspective on the system
   - What he represents thematically

7. **At least 1-2 additional characters** that the story needs
   - A peer/friend for Cass at the Academy?
   - Someone at the House of Corda who knows Perin?
   - A Court Singer with divided loyalties?

FOR EACH CHARACTER INCLUDE:
- Name, age, role
- Ghost/Wound/Want/Need/Lie chain (for major characters)
- Three sliders (proactivity/likability/competence) with numbers and justification
- Arc type and arc trajectory
- Speech pattern (all 8 dimensions, with example lines)
- Physical appearance (specific, not generic)
- Physical habits and unconscious tells
- Secrets (what the reader doesn't learn immediately)
- Key relationships (mapped to other characters)
- Thematic role (what question does this character embody?)

IMPORTANT:
- Characters must INTERCONNECT. Their wants should conflict with each other.
- Every secret should be something that would CHANGE the story if revealed.
- Speech patterns must be distinct enough to pass the no-tags test.
- Give Cass habits that come from his gift (the pain, the constant listening).
- The father's shaking hands should connect to something specific.
- Maret Corda should be as fully realized as Cass -- a worthy antagonist.
- Target ~3000-4000 words. Dense character work, not padding.
"""

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
print(result)
