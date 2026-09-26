#!/usr/bin/env python3
"""
fetch_transcript.py - Fetch a YouTube transcript as JSON for the youtube-summary skill.

Usage:
    python3 fetch_transcript.py <youtube_url> [--lang en] [-o transcript.json]
    python3 fetch_transcript.py <youtube_url> --from-text pasted.txt [-o transcript.json]

Output JSON:
    {"video_id", "url", "title", "channel", "language", "is_generated",
     "segments": [{"start": 12.3, "duration": 4.1, "text": "..."}]}

On failure, exits non-zero and prints {"error": CODE, "detail": ...} to stderr.
Codes: INVALID_URL, NETWORK_BLOCKED, YOUTUBE_BOT_CHECK, NO_TRANSCRIPT,
VIDEO_UNAVAILABLE, MISSING_DEPENDENCY, UNKNOWN_ERROR.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from urllib.parse import parse_qs, urlparse

ID_RE = r"[A-Za-z0-9_-]{11}"


def fail(code: str, detail: str, video_id: str | None = None) -> None:
    print(json.dumps({"error": code, "detail": detail, "video_id": video_id}), file=sys.stderr)
    sys.exit(1)


def extract_video_id(url: str) -> str | None:
    """Pull the 11-character video ID out of any common YouTube URL shape."""
    url = url.strip()
    if re.fullmatch(ID_RE, url):
        return url
    try:
        parsed = urlparse(url if "://" in url else "https://" + url)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    for prefix in ("www.", "m.", "music."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    if host == "youtu.be":
        candidate = parsed.path.lstrip("/").split("/")[0]
        return candidate if re.fullmatch(ID_RE, candidate) else None
    if host.endswith("youtube.com") or host.endswith("youtube-nocookie.com"):
        if parsed.path == "/watch":
            v = parse_qs(parsed.query).get("v", [""])[0]
            return v if re.fullmatch(ID_RE, v) else None
        m = re.match(rf"^/(?:shorts|embed|v|live)/({ID_RE})", parsed.path)
        if m:
            return m.group(1)
    return None


def fetch_metadata(video_id: str) -> dict:
    """Title and channel via YouTube's public oEmbed endpoint (best effort)."""
    url = f"https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v={video_id}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.load(resp)
        return {"title": data.get("title"), "channel": data.get("author_name")}
    except Exception:
        return {"title": None, "channel": None}


def classify_error(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}"
    # YouTube answered, but refused this IP: a redirect to google.com/sorry, a
    # "sign in to confirm you're not a bot" response, or the library's IP-block errors.
    if any(k in text for k in ("google.com/sorry", "/sorry/index", "RequestBlocked", "IpBlocked",
                               "PoTokenRequired", "LOGIN_REQUIRED", "not a bot")):
        return "YOUTUBE_BOT_CHECK"
    if any(k in text for k in ("ProxyError", "ConnectionError", "Tunnel connection failed",
                               "Max retries exceeded", "403 Forbidden", "timed out")):
        return "NETWORK_BLOCKED"
    return "UNKNOWN_ERROR"


def fetch_segments(video_id: str, lang: str) -> tuple[list[dict], str, bool]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api import _errors as yterr
    except ImportError:
        fail("MISSING_DEPENDENCY", "pip install youtube-transcript-api", video_id)

    try:
        listing = YouTubeTranscriptApi().list(video_id)
        preferred = [lang, "en", "en-GB", "en-AU", "en-US"]
        try:
            transcript = listing.find_manually_created_transcript(preferred)
        except yterr.NoTranscriptFound:
            try:
                transcript = listing.find_generated_transcript(preferred)
            except yterr.NoTranscriptFound:
                transcript = next(iter(listing))
        fetched = transcript.fetch()
        segments = [{"start": round(s.start, 2), "duration": round(s.duration, 2), "text": s.text}
                    for s in fetched]
        return segments, transcript.language_code, transcript.is_generated
    except StopIteration:
        fail("NO_TRANSCRIPT", "The video has no caption tracks.", video_id)
    except (yterr.TranscriptsDisabled, yterr.NoTranscriptFound) as exc:
        fail("NO_TRANSCRIPT", str(exc).splitlines()[0], video_id)
    except (yterr.VideoUnavailable, yterr.VideoUnplayable, yterr.AgeRestricted) as exc:
        fail("VIDEO_UNAVAILABLE", str(exc).splitlines()[0], video_id)
    except Exception as exc:  # noqa: BLE001
        fail(classify_error(exc), f"{type(exc).__name__}: {str(exc).splitlines()[0] if str(exc) else ''}", video_id)


def segments_from_text(path: str) -> list[dict]:
    """Parse a transcript pasted from YouTube's 'Show transcript' panel.

    Handles lines like '1:23 some words', a timestamp on its own line followed by
    text, or plain text with no timestamps at all.
    """
    ts_re = re.compile(r"^\s*(?:(\d+):)?(\d{1,2}):(\d{2})\s*(.*)$")
    segments: list[dict] = []
    pending_start = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            m = ts_re.match(line)
            if m:
                h, mnt, sec, rest = m.groups()
                pending_start = int(h or 0) * 3600 + int(mnt) * 60 + int(sec)
                if rest:
                    segments.append({"start": pending_start, "duration": 0, "text": rest})
                    pending_start = None
                continue
            start = pending_start if pending_start is not None else (segments[-1]["start"] if segments else 0)
            segments.append({"start": start, "duration": 0, "text": line})
            pending_start = None
    return segments


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--from-text", help="Use a transcript the user pasted instead of fetching")
    ap.add_argument("-o", "--output", help="Write JSON here (default: stdout)")
    args = ap.parse_args()

    video_id = extract_video_id(args.url)
    if not video_id:
        fail("INVALID_URL", f"Could not find a video ID in {args.url!r}")

    if args.from_text:
        segments, language, generated = segments_from_text(args.from_text), args.lang, None
        meta = fetch_metadata(video_id)
    else:
        segments, language, generated = fetch_segments(video_id, args.lang)
        meta = fetch_metadata(video_id)

    result = {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "title": meta["title"],
        "channel": meta["channel"],
        "language": language,
        "is_generated": generated,
        "segments": segments,
    }
    out = json.dumps(result, ensure_ascii=False, indent=1)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(out)
        words = sum(len(s["text"].split()) for s in segments)
        print(f"OK {video_id}: {len(segments)} segments, ~{words} words -> {args.output}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
