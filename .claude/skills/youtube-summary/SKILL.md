---
name: youtube-summary
description: Turn a YouTube link into a polished, standalone HTML summary. Fetches the video's transcript, corrects obvious mistranscriptions, punctuation and grammar, then writes an HTML page with a brief overview, key points, sectioned summary and verified direct quotes linked to their timestamps. Use whenever the user gives a YouTube URL (youtube.com/watch, youtu.be, shorts, embed, live) and wants a summary, notes, write-up, study guide or HTML page of the video.
---

# YouTube summary to HTML

Input: a YouTube link. Output: one self-contained `.html` file summarising the video,
written from a **corrected** transcript, with correct punctuation, grammar and Australian
English spelling, and with **direct quotes** that have been checked against the captions.

Scripts live in `scripts/` next to this file. Work in the scratchpad (or a temp dir) and
only put the final HTML where the user wants it.

## Step 1 — Fetch the transcript

```bash
pip install youtube-transcript-api --quiet   # if not already installed
python3 scripts/fetch_transcript.py "<youtube url>" -o transcript.json
```

The URL can be any common shape (`youtu.be/ID?si=...`, `watch?v=ID&t=30s`, `shorts/ID`, ...).
`transcript.json` holds `video_id`, `url`, `title`, `channel`, `is_generated` and a list of
`segments` (`start` seconds, `text`).

If it fails, the script prints `{"error": CODE, ...}` and exits non-zero:

| Code | What to do |
|---|---|
| `NETWORK_BLOCKED` | The sandbox cannot reach youtube.com. Say so plainly and name the host. Ask the user to either allow `www.youtube.com` in the environment's network settings, or paste the transcript (on YouTube: **…** under the video → **Show transcript**, then copy). Save a paste to a file and run `python3 scripts/fetch_transcript.py "<url>" --from-text pasted.txt -o transcript.json`. Never invent the video's content. |
| `YOUTUBE_BOT_CHECK` | YouTube is reachable but refused this machine's IP address (a redirect to `google.com/sorry`, or "sign in to confirm you're not a bot"). This is common from cloud servers and is not a network setting. Do not try to get around it. Ask the user to paste the transcript and use `--from-text` as above; the title and channel are still filled in from YouTube's oEmbed endpoint. |
| `NO_TRANSCRIPT` | The video has no captions. Tell the user; offer to summarise a pasted transcript instead. |
| `VIDEO_UNAVAILABLE` | Private, deleted, age-restricted or region-locked. Ask for another source. |
| `INVALID_URL` | Ask the user to check the link. |
| `MISSING_DEPENDENCY` | Install `youtube-transcript-api` and retry. |
| `UNKNOWN_ERROR` | Show the detail and offer the paste workaround. |

## Step 2 — Read and correct the transcript

Read every segment (for long videos read in chunks; do not skim). Auto-generated captions
have no punctuation and mishear words. Build a mental "clean" version of the transcript:

- **Mistranscriptions** — fix words that are obviously wrong in context: technical terms
  ("pro teen" → "protein", "hydro phobic" → "hydrophobic"), proper nouns and names (use the
  title, channel and repeated usage as evidence), homophones ("there/their", "affect/effect"),
  split or merged words, and numbers/units ("twenty five percent" → "25%").
  Only correct what is **obvious**: if the intended word is genuinely uncertain, leave it and
  mention the ambiguity in `notes` rather than guessing.
- **Punctuation and grammar** — add sentence boundaries, commas, apostrophes and capitals;
  remove caption artefacts (`[Music]`, `>>`, duplicated words from overlapping captions) and
  filler ("um", "uh", false starts) where it does not change meaning.
- **Spelling** — Australian English (colour, organise, analyse, centre, behaviour, -ise),
  except inside names and titles.
- Record each **meaningful** correction (not every added comma) as
  `{"heard": "<caption text>", "corrected": "<fix>", "note": "<why>"}`. Keep `heard` as the
  exact caption words so the quote checker can apply it.

## Step 3 — Write `summary.json`

```json
{
  "title": "Corrected video title (optional; defaults to YouTube's)",
  "channel": "Optional",
  "tldr": "One or two sentences with the core message.",
  "key_points": ["3–7 tight bullets, in the order they appear"],
  "sections": [
    {"heading": "Topic of this part", "start": 95,
     "paragraphs": ["Prose summary in your own words, clean grammar."],
     "quotes": [{"text": "A direct quote from this part.", "speaker": "Name if known"}]}
  ],
  "quotes": [{"text": "The most memorable lines.", "speaker": "...", "context": "Why it matters"}],
  "corrections": [{"heard": "pro teen", "corrected": "protein", "note": "Technical term"}],
  "notes": "Caveats: auto captions, unclear passages, music-only sections, etc."
}
```

Guidance:

- Follow the video's structure: 3–8 sections for most videos, each with a `start` time taken
  from the segment where that topic begins. Adapt to the genre — tutorials get steps,
  interviews get who-said-what, lectures get concepts and examples.
- Summary prose is paraphrase: accurate, neutral, and no claims the video does not make.
- **Direct quotes** (aim for 1–2 per section plus 3–6 featured): copy the speaker's actual
  words from the transcript, with the corrections and punctuation applied. You may trim
  filler or use an ellipsis (…) for an omission, and put clarifying words you add in
  `[square brackets]`. Do not reword a quote — if you want different wording, paraphrase it
  in a paragraph instead. Keep each quote short (roughly one to three sentences).
- Leave a quote's `start` out if unsure; the renderer fills it in from the best match.
- Plain text only in all fields (the renderer escapes HTML). Use curly quotes “ ” inside
  paragraphs when quoting a phrase in prose.

## Step 4 — Verify quotes and render

```bash
python3 scripts/render_summary.py summary.json --transcript transcript.json -o "<name>.html"
```

The renderer compares every quote with the raw captions (ignoring case, punctuation and
`[brackets]`, after applying your `corrections`). Each quote prints a score; any below 0.80
stops the render with exit code 2. When that happens, reopen the transcript near that point,
fix the quote so it matches what was said (or drop it) and rerun. Only use
`--allow-unverified` if the user explicitly accepts that (e.g. a pasted transcript that was
itself edited).

Name the file after the video, e.g. `how-enzymes-work-summary.html`. The page is standalone
(no external assets), readable on phones, works in light and dark mode, and prints cleanly.

## Step 5 — Hand it over

Give the user the file (and publish/share it if that is how this environment delivers HTML),
followed by a two-to-three line recap: the TL;DR, how many corrections were made, and any
caveats from `notes`. Do not paste the whole summary into chat.
