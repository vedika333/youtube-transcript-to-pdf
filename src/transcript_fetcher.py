# src/transcript_fetcher.py
# ─────────────────────────────────────────────────────────────────────────────
# Fetches YouTube transcripts FREE via youtube-transcript-api >= 1.0.0
# PERMANENT SOLUTION: Always fetches whatever transcript is available
# Never fails due to language — grabs any caption YouTube provides
# ─────────────────────────────────────────────────────────────────────────────

import re
import html
import os


def extract_video_id(url: str) -> str:
    """
    Extract YouTube video ID from any URL format:
      - https://www.youtube.com/watch?v=ID
      - https://youtu.be/ID
      - https://youtube.com/embed/ID
      - https://youtube.com/shorts/ID
      - raw 11-char ID
    """
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url

    patterns = [
        r'(?:youtube\.com/watch\?.*v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract video ID from URL: {url}")


def fetch_transcript(video_id: str, language: str = "en", proxy_url: str = None) -> list[dict]:
    from youtube_transcript_api import YouTubeTranscriptApi

    if proxy_url:
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url

    try:
        ytt = YouTubeTranscriptApi()

        # Get ALL available transcripts — no language filter
        try:
            transcript_list = ytt.list(video_id)
        except Exception as e:
            raise RuntimeError(f"Could not list transcripts for '{video_id}'. Detail: {e}")

        all_transcripts = list(transcript_list)

        if not all_transcripts:
            raise RuntimeError(f"No captions found for video '{video_id}'.")

        # Score: manual > auto, requested language > english > anything
        best = None
        best_score = -1

        for t in all_transcripts:
            score = 0
            lang = (t.language_code or "").lower()
            is_manual = not getattr(t, 'is_generated', True)

            if lang == language.lower():
                score += 100
            elif lang.startswith("en"):
                score += 10
            if is_manual:
                score += 20

            # KEY CHANGE: also give score to ANY transcript
            # so even if no language match, we always pick something
            score += 1

            if score > best_score:
                best_score = score
                best = t

        fetched = best.fetch()
        lang_used = getattr(best, 'language_code', 'unknown')
        is_auto = getattr(best, 'is_generated', False)
        print(f"  Transcript fetched: lang='{lang_used}' auto={is_auto}")
        return [{"text": s.text, "start": s.start, "duration": s.duration} for s in fetched]

    finally:
        if proxy_url:
            os.environ.pop("HTTP_PROXY", None)
            os.environ.pop("HTTPS_PROXY", None)


def clean_transcript(items: list[dict], clean: bool = True) -> list[dict]:
    """
    Clean raw transcript items:
    - Remove [Music], [Applause], (laughter) annotations
    - Decode HTML entities
    - Normalize whitespace
    - Filter empty entries
    """
    cleaned = []

    for item in items:
        text = item.get("text", "")

        if clean:
            text = re.sub(r'\[.*?\]', '', text)
            text = re.sub(r'\(.*?\)', '', text)
            text = html.unescape(text)
            text = text.replace('\n', ' ')
            text = re.sub(r'\s+', ' ', text).strip()

        if text:
            cleaned.append({**item, "text": text})

    return cleaned


def merge_into_paragraphs(items: list[dict], words_per_para: int = 80) -> list[dict]:
    """
    Merge caption segments into readable paragraphs (~80 words each).
    Breaks at sentence-ending punctuation for natural flow.
    """
    if not items:
        return []

    paragraphs = []
    current_words = []
    current_offset = items[0].get("start", 0)
    word_count = 0

    for item in items:
        words = item["text"].split()
        current_words.extend(words)
        word_count += len(words)

        last_word = current_words[-1] if current_words else ""
        ends_sentence = last_word.endswith(('.', '!', '?'))

        if word_count >= words_per_para and ends_sentence:
            paragraphs.append({
                "text": " ".join(current_words),
                "start_offset": current_offset,
            })
            current_words = []
            word_count = 0
            current_offset = item.get("start", 0)

    if current_words:
        paragraphs.append({
            "text": " ".join(current_words),
            "start_offset": current_offset,
        })

    return paragraphs


def format_timestamp(seconds: float) -> str:
    """Convert float seconds to MM:SS or HH:MM:SS."""
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"