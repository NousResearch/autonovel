#!/usr/bin/env python3
"""Batch draft chapters with quick slop fix and spot-check evals."""
import subprocess
import sys
import re
import json

def run(cmd, timeout=600):
    import shlex
    if isinstance(cmd, str):
        cmd_list = shlex.split(cmd)
    else:
        cmd_list = cmd
    r = subprocess.run(cmd_list, shell=False, capture_output=True, text=True, timeout=timeout)
    return r.stdout + r.stderr, r.returncode

def slop_check(ch):
    out, _ = run(f'.venv/bin/python3 -c "from evaluate import slop_score, load_file; import json; r=slop_score(load_file(\'chapters/ch_{ch:02d}.md\')); print(json.dumps(r))"')
    return json.loads(out.strip())

def pattern_check(ch):
    out, _ = run(f"grep -c 'He did not\\|He had not' chapters/ch_{ch:02d}.md")
    didnot = int(out.strip()) if out.strip().isdigit() else 0
    out, _ = run(f"grep -c 'He thought about\\|He thought of' chapters/ch_{ch:02d}.md")
    thought = int(out.strip()) if out.strip().isdigit() else 0
    out, _ = run(f"wc -w < chapters/ch_{ch:02d}.md")
    words = int(out.strip())
    return words, didnot, thought

def spot_eval(ch):
    out, rc = run(f'.venv/bin/python3 evaluate.py --chapter={ch}', timeout=300)
    m_overall = re.search(r'overall_score: ([\d.]+)', out)
    m_raw = re.search(r'raw_judge_score: (\d+)', out)
    if m_overall and m_raw:
        return float(m_overall.group(1)), int(m_raw.group(1))
    return None, None

# Chapters to draft
chapters = list(range(11, 25))
spot_check_chapters = {13, 17, 20, 24}  # midpoint, all-is-lost, break-into-3, finale

results = []

for ch in chapters:
    print(f"\n{'='*50}")
    print(f"DRAFTING CH {ch}")
    print(f"{'='*50}")
    
    # Draft
    out, rc = run(f'.venv/bin/python3 draft_chapter.py {ch}')
    if rc != 0:
        print(f"  DRAFT FAILED: {out[:200]}")
        results.append((ch, 0, 0, "FAILED"))
        continue
    
    # Word count and patterns
    words, didnot, thought = pattern_check(ch)
    slop = slop_check(ch)
    
    print(f"  Words: {words}")
    print(f"  Slop penalty: {slop['slop_penalty']}")
    print(f"  Tier1: {len(slop['tier1_hits'])}  Fiction: {len(slop['fiction_ai_tells'])}  Telling: {slop['telling_violations']}")
    print(f"  Patterns: didnot={didnot} thought={thought}")
    
    # Spot-check eval on selected chapters
    score = None
    if ch in spot_check_chapters:
        print(f"  === SPOT-CHECK EVAL ===")
        score, raw = spot_eval(ch)
        if score is not None:
            print(f"  Score: {score} (raw {raw})")
            if score < 6.0:
                print(f"  *** BELOW THRESHOLD -- flagging for retry ***")
        else:
            print(f"  Eval parse failed")
    
    results.append((ch, words, slop['slop_penalty'], score))
    
    # Git commit
    run(f"cd /home/jeffq/autonovel && git add chapters/ch_{ch:02d}.md state.json")
    
    # Update state.json
    with open("state.json") as f:
        state = json.load(f)
    state["current_focus"] = f"ch_{ch:02d}"
    state["chapters_drafted"] = ch
    with open("state.json", "w") as f:
        json.dump(state, f, indent=2)

print(f"\n\n{'='*60}")
print("BATCH DRAFTING COMPLETE")
print(f"{'='*60}")
total_words = 0
for ch, words, penalty, score in results:
    status = f"score={score}" if score else "drafted"
    print(f"  Ch {ch:2d}: {words:5d}w  slop={penalty:.1f}  {status}")
    total_words += words
print(f"\n  Total new words: {total_words}")
print(f"  Chapters drafted: {len([r for r in results if r[1] > 0])}")
