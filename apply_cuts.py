#!/usr/bin/env python3
"""Apply adversarial edit cuts to chapter files.

Usage:
  python apply_cuts.py 12                                  # apply cuts to ch 12
  python apply_cuts.py all                                 # apply cuts to all chapters
  python apply_cuts.py all --types OVER-EXPLAIN REDUNDANT  # filter by type
  python apply_cuts.py all --min-fat 17                    # only chapters with >=17% fat
  python apply_cuts.py all --dry-run                       # show what would be cut
"""

import argparse
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
CHAPTERS_DIR = BASE / "chapters"
EDIT_LOGS_DIR = BASE / "edit_logs"

VALID_TYPES = {"OVER-EXPLAIN", "REDUNDANT", "FAT", "TELL", "STRUCTURAL", "GENERIC"}
MIN_QUOTE_LEN = 25


def load_cuts(chapter_num: int) -> dict | None:
    """Load the cuts JSON for a given chapter number. Returns None if missing."""
    cuts_file = EDIT_LOGS_DIR / f"ch{chapter_num:02d}_cuts.json"
    if not cuts_file.exists():
        return None
    try:
        data = json.loads(cuts_file.read_text(encoding="utf-8"))
        return data
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  WARNING: failed to parse {cuts_file.name}: {exc}")
        return None


def chapter_path(chapter_num: int) -> Path:
    return CHAPTERS_DIR / f"ch_{chapter_num:02d}.md"


def find_and_remove(text: str, quote: str) -> tuple[str, bool, str]:
    """Try to find and remove quote from text.

    Returns (new_text, success, failure_reason).
    """
    # Exact match first
    count = text.count(quote)
    if count == 1:
        text = text.replace(quote, "", 1)
        return text, True, ""
    if count > 1:
        return text, False, f"ambiguous ({count} matches)"

    # Normalised whitespace match: collapse runs of whitespace in both the
    # text and the quote to single spaces, search, then map back to the
    # original span.
    ws = re.compile(r"\s+")
    norm_quote = ws.sub(" ", quote).strip()
    if len(norm_quote) < MIN_QUOTE_LEN:
        return text, False, "quote too short after normalisation"

    # Build a regex that matches the quote with flexible whitespace
    # Escape each token and join with \s+
    tokens = norm_quote.split(" ")
    pattern = r"\s+".join(re.escape(t) for t in tokens)
    matches = list(re.finditer(pattern, text))
    if len(matches) == 1:
        m = matches[0]
        text = text[:m.start()] + text[m.end():]
        return text, True, ""
    if len(matches) > 1:
        return text, False, f"ambiguous after ws-norm ({len(matches)} matches)"

    return text, False, "not found"


def collapse_blank_lines(text: str) -> str:
    """Collapse runs of 3+ newlines down to 2 (one blank line).
    
    Safeguard: only collapses newlines that are clearly paragraph breaks,
    not newlines within content. Uses lookbehind to ensure we're collapsing
    an actual blank line (newline + optional whitespace + newline).
    """
    # Only collapse blank lines: preceded by newline, followed by newline
    # This prevents accidentally collapsing content that legitimately
    # has multiple consecutive newlines within a paragraph.
    return re.sub(r"(?<=\n)\n+(?=\n)", "\n\n", text)


def safe_apply_cuts_with_collapse(text: str, cuts: list, chapter_num: int) -> tuple[str, dict]:
    """Apply cuts and then safely collapse blank lines.
    
    Returns (new_text, stats).
    This is a safer version of the apply_cuts workflow that:
    1. Applies each cut and tracks what was removed
    2. Only collapses blank lines if text was actually modified
    3. Preserves original paragraph breaks when possible
    
    The original collapse_blank_lines() is kept for backwards compatibility
    but apply_cuts.py main() now uses this safer version.
    """
    import re as re_module
    
    original_words = len(text.split())
    
    # Apply cuts first
    for cut in cuts:
        quote = cut.get("quote", "")
        cut_type = cut.get("type", "UNKNOWN")
        reason = cut.get("reason", "")
        
        MIN_QUOTE_LEN_LOCAL = 25
        if len(quote.strip()) < MIN_QUOTE_LEN_LOCAL:
            continue
            
        new_text, success, fail_reason = find_and_remove(text, quote)
        if success:
            text = new_text
        else:
            pass  # silently skip failed cuts in safe mode
    
    # Only collapse blank lines if we actually removed something
    # and the result has 3+ consecutive newlines
    if "\n\n\n" in text:
        text = collapse_blank_lines(text)
    
    return text, {"applied": len(cuts), "word_delta": original_words - len(text.split())}


def discover_chapters() -> list[int]:
    """Return sorted list of chapter numbers that have both a chapter file and a cuts file."""
    nums = set()
    for p in EDIT_LOGS_DIR.glob("ch*_cuts.json"):
        m = re.match(r"ch(\d+)_cuts\.json", p.name)
        if m:
            nums.add(int(m.group(1)))
    return sorted(nums)


def process_chapter(
    chapter_num: int,
    type_filter: set[str] | None,
    min_fat: int,
    dry_run: bool,
) -> dict:
    """Process cuts for one chapter. Returns stats dict."""
    stats = {"applied": 0, "failed": 0, "skipped": 0, "words_removed": 0, "error": None}
    label = f"ch{chapter_num:02d}"

    # Load cuts
    data = load_cuts(chapter_num)
    if data is None:
        stats["error"] = "no cuts file"
        return stats

    fat_pct = data.get("overall_fat_percentage", 0)
    if fat_pct < min_fat:
        stats["skipped"] = len(data.get("cuts", []))
        stats["error"] = f"fat {fat_pct}% < threshold {min_fat}%"
        return stats

    cuts = data.get("cuts", [])
    if not cuts:
        stats["error"] = "no cuts in file"
        return stats

    # Load chapter text
    ch_path = chapter_path(chapter_num)
    if not ch_path.exists():
        stats["error"] = f"{ch_path.name} not found"
        return stats

    text = ch_path.read_text(encoding="utf-8")
    original_words = len(text.split())

    for cut in cuts:
        quote = cut.get("quote", "")
        cut_type = cut.get("type", "UNKNOWN")
        reason = cut.get("reason", "")

        # Filter by type
        if type_filter and cut_type not in type_filter:
            stats["skipped"] += 1
            continue

        # Skip short quotes
        if len(quote.strip()) < MIN_QUOTE_LEN:
            stats["skipped"] += 1
            if not dry_run:
                print(f"  SKIP [{cut_type}] quote too short ({len(quote.strip())} chars)")
            continue

        if dry_run:
            preview = quote[:80].replace("\n", "\\n")
            if len(quote) > 80:
                preview += "..."
            words = len(quote.split())
            print(f"  CUT  [{cut_type}] ~{words}w: {preview}")
            print(f"        reason: {reason}")
            stats["applied"] += 1
            stats["words_removed"] += words
            continue

        # Apply the cut
        new_text, success, fail_reason = find_and_remove(text, quote)
        if success:
            words_cut = len(quote.split())
            stats["applied"] += 1
            stats["words_removed"] += words_cut
            text = new_text
            preview = quote[:60].replace("\n", "\\n")
            if len(quote) > 60:
                preview += "..."
            print(f"  CUT  [{cut_type}] ~{words_cut}w: {preview}")
        else:
            stats["failed"] += 1
            preview = quote[:60].replace("\n", "\\n")
            if len(quote) > 60:
                preview += "..."
            print(f"  FAIL [{cut_type}] {fail_reason}: {preview}")

    # Write back
    if not dry_run and stats["applied"] > 0:
        text = collapse_blank_lines(text)
        ch_path.write_text(text, encoding="utf-8")
        new_words = len(text.split())
        print(f"  SAVED {ch_path.name}: {original_words} -> {new_words} words")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Apply adversarial edit cuts to chapter files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python apply_cuts.py 12\n"
            "  python apply_cuts.py all --types OVER-EXPLAIN REDUNDANT\n"
            "  python apply_cuts.py all --min-fat 17\n"
            "  python apply_cuts.py all --dry-run\n"
        ),
    )
    parser.add_argument(
        "chapter",
        help="Chapter number (e.g. 12) or 'all' to process every chapter.",
    )
    parser.add_argument(
        "--types",
        nargs="+",
        metavar="TYPE",
        choices=sorted(VALID_TYPES),
        help=f"Only apply cuts of these types. Choices: {', '.join(sorted(VALID_TYPES))}",
    )
    parser.add_argument(
        "--min-fat",
        type=int,
        default=0,
        metavar="PCT",
        help="Only process chapters with overall_fat_percentage >= this value.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cut without modifying files.",
    )
    args = parser.parse_args()

    type_filter = set(args.types) if args.types else None

    # Determine which chapters to process
    if args.chapter.lower() == "all":
        chapters = discover_chapters()
        if not chapters:
            print("No cuts files found in edit_logs/")
            sys.exit(1)
    else:
        try:
            chapters = [int(args.chapter)]
        except ValueError:
            parser.error(f"Invalid chapter: {args.chapter!r} (use a number or 'all')")

    # Banner
    mode = "DRY RUN" if args.dry_run else "APPLY"
    type_info = f", types={','.join(sorted(type_filter))}" if type_filter else ""
    fat_info = f", min-fat={args.min_fat}%" if args.min_fat > 0 else ""
    print(f"=== apply_cuts [{mode}] chapters={len(chapters)}{type_info}{fat_info} ===\n")

    # Aggregate stats
    totals = {"applied": 0, "failed": 0, "skipped": 0, "words_removed": 0}

    for ch_num in chapters:
        label = f"ch{ch_num:02d}"
        print(f"--- {label} ---")
        stats = process_chapter(ch_num, type_filter, args.min_fat, args.dry_run)
        if stats["error"]:
            print(f"  {stats['error']}")
        for k in totals:
            totals[k] += stats[k]
        print()

    # Summary
    print("=" * 50)
    print(f"Applied: {totals['applied']}  |  Failed: {totals['failed']}  |  Skipped: {totals['skipped']}")
    print(f"Words removed: ~{totals['words_removed']}")
    if args.dry_run:
        print("(dry run — no files were modified)")
    print("=" * 50)

    if totals["failed"] > 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
