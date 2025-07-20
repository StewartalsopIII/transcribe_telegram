# Potential Bugs

## Clarified Text JSON Fallback Issue (rare)

* **First observed:** 2025-07-13 (single occurrence)
* **Symptom:** Instead of sending plain clarified text, the bot replied with the full JSON blob (wrapped in ```json fences).

### Details
When `TextProcessor.rewrite_for_clarity()` fails to parse the model’s JSON, the fallback path returns the **entire** response.  The downstream `handle_audio()` then forwards that raw JSON to Telegram, resulting in a bulky message that is hard to read and copy.

### Suspected root causes
1. **Illegal new-lines inside a JSON string** – the model sometimes inserts literal line breaks (`\n`) that break `json.loads()`.
2. **Missing / malformed closing code fence** – stray ``` line causes our fence-stripper to leave garbage.
3. Fancy quotes / UTF-8 punctuation corrupting string delimiters.
4. Leading commentary before the first `{`, confusing the brace-finding heuristic.
5. Trailing commentary after the final `}`.
6. Multiple `{}` pairs in the response, leading the heuristic to grab the wrong span.
7. Response truncation (token limit) leaving a half-finished JSON object.

**Most likely:** (#1) illegal newlines, and (#2) missing code fence.

### Current action
* Logged here for tracking – no code change yet.
* If it recurs, harden `_extract_json` and/or tighten the Gemini prompt to enforce valid JSON output.

### Relevant code locations & potential fixes

| Area | File & approx. lines | What to tweak |
|------|----------------------|---------------|
| JSON extraction helper | `main.py` lines ~120-150 (`_extract_json` inside `rewrite_for_clarity`) |  • Escape literal newlines (`replace("\n", "\\n")` before `json.loads`)<br> • Strip smart quotes / odd punctuation<br> • Add try/except around fence-stripping to ignore stray back-ticks |
| Code-fence handling | Same block (`_extract_json`) | Ensure both opening and closing ``` are removed, even if trailing fence is missing. |
| Grounding step parsing | `main.py` lines ~190-230 (JSON extraction inside `ground_ambiguous_terms`) | Mirror any robustness improvements made to `_extract_json`. |
| Prompt wording | `rewrite_for_clarity` prompt (same file, lines ~110-118) | Add explicit instruction: “Return **only** valid JSON with escaped newline characters.” |

Implement these tweaks if the issue resurfaces more than once. 