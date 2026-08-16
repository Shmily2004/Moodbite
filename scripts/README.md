Legacy and utility scripts

Files moved into `scripts/legacy/` are one-off utilities or older helpers kept for reference.

Contents:
- `check_mood_improvement.py` - quick CSV checks to profile mood coverage
- `merge_csv_direct.py` - specific CSV merge helper (kept for compatibility)
- `merge_csv_direct_v2.py` - generalized CSV merge tool that reads all JSONs
- `extract_docs.py` - docx -> markdown extractor used to generate docs/extracted/

Guidelines:
- Prefer scripts under `scripts/` for non-production utilities. Production code belongs in `src/`.
- When consolidating, keep the most general, well-documented script and archive the rest.
