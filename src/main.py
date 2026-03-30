# src/main.py
# ═══════════════════════════════════════════════════════════════════════════════
# YouTube Transcript → PDF  |  Apify Actor  |  Python
# 100% Free · Supports Apify Proxy · Each user uses their own proxy
# ═══════════════════════════════════════════════════════════════════════════════

# UTF-8 fix for Windows — must be before any other imports
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from apify import Actor

from .transcript_fetcher import (
    extract_video_id,
    fetch_transcript,
    clean_transcript,
    merge_into_paragraphs,
)
from .metadata_fetcher import fetch_video_metadata
from .pdf_generator import generate_transcript_pdf, sanitize_filename

TMP_DIR = Path("/tmp/yt_transcripts")
TMP_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    async with Actor:

        # ── Read Input ─────────────────────────────────────────────────────────
        actor_input = await Actor.get_input() or {}

        urls: list[str] = actor_input.get("urls", [])
        if not urls:
            raise ValueError("'urls' field is required and must contain at least one YouTube URL.")

        language           = actor_input.get("language", "en")
        include_timestamps = actor_input.get("includeTimestamps", False)
        include_metadata   = actor_input.get("includeMetadata", True)
        clean              = actor_input.get("cleanTranscript", True)

        Actor.log.info(f"Processing {len(urls)} video(s) | lang={language} | timestamps={include_timestamps}")

        # ── Proxy Configuration ────────────────────────────────────────────────
        # Each user attaches their own proxy — no shared quota issues
        proxy_url = None
        proxy_input = actor_input.get("proxyConfiguration")

        if proxy_input:
            try:
                proxy_config = await Actor.create_proxy_configuration(
                    actor_proxy_input=proxy_input
                )
                proxy_url = await proxy_config.new_url()
                Actor.log.info(f"  Proxy enabled")
            except Exception as e:
                Actor.log.warning(f"  Proxy setup failed, continuing without proxy: {e}")
        else:
            Actor.log.info("  No proxy configured — may be blocked on cloud runs")

        # ── Open KV Store ──────────────────────────────────────────────────────
        kv_store = await Actor.open_key_value_store()
        results  = []

        # ── Process Each URL ───────────────────────────────────────────────────
        for idx, url in enumerate(urls, 1):
            Actor.log.info(f"[{idx}/{len(urls)}] {url}")
            video_id = None

            try:
                # Step 1 — Extract video ID
                video_id = extract_video_id(url.strip())
                Actor.log.info(f"  Video ID: {video_id}")

                # Step 2 — Fetch metadata via yt-dlp (free, proxy-aware)
                Actor.log.info("  Fetching metadata...")
                metadata = fetch_video_metadata(video_id, proxy_url=proxy_url)
                Actor.log.info(f"  Title:   {metadata['title']}")
                Actor.log.info(f"  Channel: {metadata['channel_name']} | {metadata['duration_formatted']}")

                # Step 3 — Fetch transcript via youtube-transcript-api (free, proxy-aware)
                Actor.log.info("  Fetching transcript...")
                raw = fetch_transcript(video_id, language, proxy_url=proxy_url)
                Actor.log.info(f"  {len(raw)} caption segments")

                # Step 4 — Clean
                cleaned = clean_transcript(raw, clean=clean)
                Actor.log.info(f"  Cleaned -> {len(cleaned)} segments")

                # Step 5 — Merge into paragraphs
                paragraphs = merge_into_paragraphs(cleaned)
                word_count = sum(len(p["text"].split()) for p in paragraphs)
                Actor.log.info(f"  {len(paragraphs)} paragraphs | {word_count:,} words")

                # Step 6 — Generate PDF via ReportLab (free, local)
                filename    = sanitize_filename(metadata["title"], video_id)
                output_path = str(TMP_DIR / filename)
                Actor.log.info("  Generating PDF...")
                generate_transcript_pdf(
                    metadata=metadata,
                    paragraphs=paragraphs,
                    raw_transcript=cleaned,
                    output_path=output_path,
                    include_timestamps=include_timestamps,
                    include_metadata=include_metadata,
                )

                # Step 7 — Upload PDF to Apify KV Store
                store_key = f"transcript_{video_id}"
                with open(output_path, "rb") as f:
                    pdf_bytes = f.read()

                await kv_store.set_value(
                    store_key,
                    pdf_bytes,
                    content_type="application/pdf",
                )
                Actor.log.info(f"  PDF uploaded -> key: {store_key}")

                # Step 8 — Push result to Dataset
                result = {
                    "status":            "success",
                    "videoId":           video_id,
                    "videoUrl":          url,
                    "title":             metadata["title"],
                    "channelName":       metadata["channel_name"],
                    "durationFormatted": metadata["duration_formatted"],
                    "wordCount":         word_count,
                    "segmentCount":      len(raw),
                    "language":          language,
                    "pdfKey":            store_key,
                    "filename":          filename,
                    "processedAt":       datetime.now(timezone.utc).isoformat(),
                }
                await Actor.push_data(result)
                results.append(result)

                # Cleanup temp file
                try:
                    os.remove(output_path)
                except Exception:
                    pass

            except Exception as e:
                Actor.log.error(f"  Failed: {e}")
                fail = {
                    "status":      "failed",
                    "videoId":     video_id,
                    "videoUrl":    url,
                    "error":       str(e),
                    "processedAt": datetime.now(timezone.utc).isoformat(),
                }
                await Actor.push_data(fail)
                results.append(fail)

        # ── Summary ────────────────────────────────────────────────────────────
        ok  = [r for r in results if r["status"] == "success"]
        err = [r for r in results if r["status"] == "failed"]

        Actor.log.info(f"DONE | success={len(ok)} | failed={len(err)} | total={len(urls)}")

        for r in ok:
            Actor.log.info(f"  OK  {r['title']} -> {r['pdfKey']}")
        for r in err:
            Actor.log.info(f"  ERR {r['videoUrl']} -> {r['error']}")

        # Save summary to KV Store
        await kv_store.set_value("OUTPUT_SUMMARY", {
            "totalProcessed": len(urls),
            "successful":     len(ok),
            "failed":         len(err),
            "results":        results,
        })