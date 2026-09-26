#!/usr/bin/env python3
"""
render_summary.py - Turn a summary JSON (written by Claude) into a standalone HTML page,
checking every quote against the raw transcript first.

Usage:
    python3 render_summary.py summary.json --transcript transcript.json -o summary.html
    python3 render_summary.py summary.json --transcript transcript.json --check-only

Summary JSON shape (only "tldr" and one of "sections"/"key_points" are required):
{
  "title": "...", "channel": "...",            # default to the transcript's metadata
  "tldr": "One or two sentences.",
  "key_points": ["...", "..."],
  "sections": [{"heading": "...", "start": 95,
                "paragraphs": ["..."],
                "quotes": [{"text": "...", "speaker": "...", "start": 101}]}],
  "quotes": [{"text": "...", "speaker": "...", "start": 300, "context": "..."}],
  "corrections": [{"heard": "...", "corrected": "...", "note": "..."}],
  "notes": "Caveats about transcript quality, etc."
}

Quote check: each quote is matched against the raw caption text (case, punctuation and
[bracketed editorial insertions] ignored, and the listed corrections applied). A quote
whose best match scores below --threshold is reported and, unless --allow-unverified is
given, the script exits non-zero without writing HTML. A missing "start" is filled in
from the best-matching segment so every quote links to its moment in the video.
"""

from __future__ import annotations

import argparse
import difflib
import html
import json
import re
import sys
from datetime import date


def norm_words(text: str) -> list[str]:
    text = re.sub(r"\[[^\]]*\]", " ", text)          # drop [editorial insertions]
    text = text.replace("’", "'").replace("‘", "'")
    text = re.sub(r"[^\w'\s]", " ", text.lower())
    return [w.strip("'") for w in text.split() if w.strip("'")]


def build_index(segments: list[dict], corrections: list[dict]):
    """Flatten the transcript into words, remembering each word's segment start time."""
    words, starts = [], []
    subs = [(norm_words(c.get("heard", "")), norm_words(c.get("corrected", ""))) for c in corrections]
    for seg in segments:
        for w in norm_words(seg.get("text", "")):
            words.append(w)
            starts.append(seg.get("start", 0))
    # Apply corrections so a quote using the corrected wording still matches.
    for heard, fixed in subs:
        if not heard or not fixed:
            continue
        i, out_w, out_s = 0, [], []
        while i < len(words):
            if words[i:i + len(heard)] == heard:
                out_w.extend(fixed)
                out_s.extend([starts[i]] * len(fixed))
                i += len(heard)
            else:
                out_w.append(words[i])
                out_s.append(starts[i])
                i += 1
        words, starts = out_w, out_s
    return words, starts


def best_match(quote: str, words: list[str], starts: list[float]):
    q = norm_words(quote)
    if not q or not words:
        return 0.0, None
    n = len(q)
    first = set(q[:3])
    best, best_start = 0.0, None
    sm = difflib.SequenceMatcher(autojunk=False)
    sm.set_seq2(q)
    for i in range(max(1, len(words) - n + 1)):
        if words[i] not in first and i % 4:          # cheap pruning, still samples every 4th word
            continue
        for width in (n - 2, n, n + 2):
            if width <= 0:
                continue
            sm.set_seq1(words[i:i + width])
            r = sm.ratio()
            if r > best:
                best, best_start = r, starts[i]
    return best, best_start


def fmt_ts(seconds) -> str:
    s = int(seconds or 0)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def check_quotes(summary: dict, transcript: dict, threshold: float) -> list[str]:
    words, starts = build_index(transcript.get("segments", []), summary.get("corrections", []))
    problems = []
    all_quotes = list(summary.get("quotes", []))
    for sec in summary.get("sections", []):
        all_quotes.extend(sec.get("quotes", []))
    for q in all_quotes:
        score, start = best_match(q["text"], words, starts)
        q["_score"] = round(score, 2)
        if q.get("start") is None and start is not None:
            q["start"] = start
        status = "ok " if score >= threshold else "LOW"
        print(f"[{status}] {score:.2f} @ {fmt_ts(q.get('start'))}  {q['text'][:70]}", file=sys.stderr)
        if score < threshold:
            problems.append(q["text"])
    return problems


CSS = """
:root{--bg:#fbfaf7;--surface:#ffffff;--text:#1d1f23;--muted:#555b66;--rule:#e2dfd8;
--accent:#1f5f8b;--accent-soft:#e8f0f6;--quote-bar:#1f5f8b;--mark:#fff3c4;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15171a;--surface:#1d2024;
--text:#e8e6e1;--muted:#a3a9b3;--rule:#33373d;--accent:#8cc4ec;--accent-soft:#1f2a33;
--quote-bar:#8cc4ec;--mark:#4a4020;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#15171a;--surface:#1d2024;--text:#e8e6e1;--muted:#a3a9b3;--rule:#33373d;
--accent:#8cc4ec;--accent-soft:#1f2a33;--quote-bar:#8cc4ec;--mark:#4a4020;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font:1.0625rem/1.65 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
main{max-width:46rem;margin:0 auto;padding:2.5rem 1rem 4rem}
header{border-bottom:1px solid var(--rule);padding-bottom:1.25rem;margin-bottom:1.75rem}
.eyebrow{font-size:.8125rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0 0 .5rem}
h1{font-size:clamp(1.6rem,4vw,2.1rem);line-height:1.2;margin:0 0 .5rem;text-wrap:balance}
h2{font-size:1.3rem;margin:2.25rem 0 .75rem;line-height:1.3}
.meta{color:var(--muted);margin:0;font-size:.9375rem}
a{color:var(--accent);text-underline-offset:.15em}
a:focus-visible{outline:3px solid var(--accent);outline-offset:2px;border-radius:2px}
.tldr{background:var(--accent-soft);border-radius:.5rem;padding:1rem 1.25rem;margin:0 0 1.5rem}
.tldr strong{display:block;font-size:.8125rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:.25rem}
.tldr p{margin:0}
ul.points{padding-left:1.25rem}ul.points li{margin:.35rem 0}
nav.toc ol{padding-left:1.25rem;margin:.25rem 0 0}nav.toc{font-size:.9375rem}
blockquote{margin:1.25rem 0;padding:.25rem 0 .25rem 1.1rem;border-left:4px solid var(--quote-bar)}
blockquote p{margin:0;font-style:italic}
blockquote footer{margin-top:.35rem;font-size:.875rem;color:var(--muted);font-style:normal}
.ts{font-variant-numeric:tabular-nums;font-size:.875rem;white-space:nowrap}
figure.featured{margin:0}figure.featured blockquote{background:var(--surface);border:1px solid var(--rule);
border-left:4px solid var(--quote-bar);border-radius:.25rem;padding:.9rem 1.1rem}
figure.featured figcaption{font-size:.875rem;color:var(--muted);margin:-.75rem 0 1.25rem 1.3rem}
table{width:100%;border-collapse:collapse;font-size:.9375rem;margin:.75rem 0}
th,td{text-align:left;vertical-align:top;padding:.5rem .6rem;border-bottom:1px solid var(--rule)}
th{color:var(--muted);font-weight:600}
.table-wrap{overflow-x:auto}
.unverified{font-size:.8125rem;color:var(--muted)}
.notes{color:var(--muted);font-size:.9375rem}
footer.page{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--rule);color:var(--muted);font-size:.875rem}
@media print{body{background:#fff;color:#000}a{color:#000}}
"""


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def ts_link(url: str, start) -> str:
    if start is None:
        return ""
    sec = int(start)
    return (f'<a class="ts" href="{esc(url)}&amp;t={sec}s" '
            f'aria-label="Watch from {fmt_ts(sec)}">{fmt_ts(sec)}</a>')


def render_quote(q: dict, url: str) -> str:
    bits = []
    if q.get("speaker"):
        bits.append(esc(q["speaker"]))
    link = ts_link(url, q.get("start"))
    if link:
        bits.append(link)
    flag = "" if q.get("_score", 1) >= q.get("_threshold", 0) else ' <span class="unverified">(paraphrase check failed)</span>'
    foot = f"<footer>— {' · '.join(bits)}{flag}</footer>" if bits or flag else ""
    return f"<blockquote><p>“{esc(q['text'])}”</p>{foot}</blockquote>"


def render(summary: dict, transcript: dict) -> str:
    url = transcript.get("url") or summary.get("url") or ""
    title = summary.get("title") or transcript.get("title") or "Video summary"
    channel = summary.get("channel") or transcript.get("channel")
    sections = summary.get("sections", [])
    out = []
    meta = []
    if channel:
        meta.append(esc(channel))
    if url:
        meta.append(f'<a href="{esc(url)}">Watch on YouTube</a>')
    out.append(f'<header><p class="eyebrow">Video summary</p><h1>{esc(title)}</h1>'
               f'<p class="meta">{" · ".join(meta)}</p></header>')
    out.append(f'<section class="tldr" aria-label="In brief"><strong>In brief</strong><p>{esc(summary["tldr"])}</p></section>')

    if summary.get("key_points"):
        out.append('<section aria-labelledby="kp"><h2 id="kp">Key points</h2><ul class="points">'
                   + "".join(f"<li>{esc(p)}</li>" for p in summary["key_points"]) + "</ul></section>")

    if len(sections) > 2:
        out.append('<nav class="toc" aria-labelledby="toc"><h2 id="toc">Contents</h2><ol>'
                   + "".join(f'<li><a href="#s{i}">{esc(s["heading"])}</a></li>' for i, s in enumerate(sections, 1))
                   + "</ol></nav>")

    for i, sec in enumerate(sections, 1):
        start = ts_link(url, sec.get("start"))
        out.append(f'<section aria-labelledby="s{i}"><h2 id="s{i}">{esc(sec["heading"])}'
                   + (f' <span class="meta">{start}</span>' if start else "") + "</h2>")
        for p in sec.get("paragraphs", []):
            out.append(f"<p>{esc(p)}</p>")
        for q in sec.get("quotes", []):
            out.append(render_quote(q, url))
        out.append("</section>")

    if summary.get("quotes"):
        out.append('<section aria-labelledby="fq"><h2 id="fq">Notable quotes</h2>')
        for q in summary["quotes"]:
            out.append('<figure class="featured">' + render_quote(q, url)
                       + (f"<figcaption>{esc(q['context'])}</figcaption>" if q.get("context") else "")
                       + "</figure>")
        out.append("</section>")

    if summary.get("corrections"):
        rows = "".join(f"<tr><td>{esc(c.get('heard'))}</td><td>{esc(c.get('corrected'))}</td>"
                       f"<td>{esc(c.get('note'))}</td></tr>" for c in summary["corrections"])
        out.append('<section aria-labelledby="corr"><h2 id="corr">Transcript corrections</h2>'
                   '<p class="notes">The captions were corrected before summarising. Quotes use the corrected wording; '
                   'words in [square brackets] were added for clarity.</p>'
                   '<div class="table-wrap"><table><thead><tr><th scope="col">Captions said</th>'
                   '<th scope="col">Corrected to</th><th scope="col">Why</th></tr></thead>'
                   f"<tbody>{rows}</tbody></table></div></section>")

    if summary.get("notes"):
        out.append(f'<section aria-labelledby="nt"><h2 id="nt">Notes</h2><p class="notes">{esc(summary["notes"])}</p></section>')

    source = "auto-generated captions" if transcript.get("is_generated") else "captions"
    out.append(f'<footer class="page">Summarised from the video’s {source} on {date.today():%-d %B %Y}. '
               "Timestamps link to the moment in the video.</footer>")

    lang = "en-AU"
    return (f'<!doctype html>\n<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{esc(title)}</title>\n<style>{CSS}</style>\n</head>\n<body>\n<main>\n"
            + "\n".join(out) + "\n</main>\n</body>\n</html>\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("summary")
    ap.add_argument("--transcript", required=True)
    ap.add_argument("-o", "--output", default="summary.html")
    ap.add_argument("--threshold", type=float, default=0.8)
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--allow-unverified", action="store_true")
    args = ap.parse_args()

    with open(args.summary, encoding="utf-8") as fh:
        summary = json.load(fh)
    with open(args.transcript, encoding="utf-8") as fh:
        transcript = json.load(fh)
    if not summary.get("tldr"):
        sys.exit("summary.json needs a 'tldr'")

    problems = check_quotes(summary, transcript, args.threshold)
    for q in summary.get("quotes", []) + [q for s in summary.get("sections", []) for q in s.get("quotes", [])]:
        q["_threshold"] = args.threshold
    if problems:
        print(f"\n{len(problems)} quote(s) could not be matched to the transcript. Fix them to match "
              "what was said, or drop them.", file=sys.stderr)
        if not args.allow_unverified:
            sys.exit(2)
    if args.check_only:
        return
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(render(summary, transcript))
    print(f"Wrote {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
