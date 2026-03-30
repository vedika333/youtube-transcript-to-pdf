# src/metadata_fetcher.py
# ─────────────────────────────────────────────────────────────────────────────
# Fetches YouTube video metadata FREE using yt-dlp
# Supports proxy for cloud IP bypass
# ─────────────────────────────────────────────────────────────────────────────

import yt_dlp
from datetime import datetime


def fetch_video_metadata(video_id: str, proxy_url: str = None) -> dict:
    """
    Fetch video metadata from YouTube using yt-dlp.
    Completely free, no YouTube Data API key needed.
    Supports optional proxy_url to bypass YouTube cloud IP blocks.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "quiet":         True,
        "no_warnings":   True,
        "skip_download": True,
        "extract_flat":  False,
        "encoding":      "utf-8",
    }

    # Add proxy if provided
    if proxy_url:
        ydl_opts["proxy"] = proxy_url

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        duration_s = int(info.get("duration") or 0)

        # Best thumbnail = last in list (highest resolution)
        thumbnails    = info.get("thumbnails") or []
        thumbnail_url = thumbnails[-1].get("url") if thumbnails else None

        # Safe int conversion — view/like count can be None
        view_count = int(info.get("view_count") or 0)
        like_count = int(info.get("like_count") or 0)

        return {
            "title":              info.get("title") or f"YouTube Video ({video_id})",
            "channel_name":       info.get("uploader") or info.get("channel") or "Unknown",
            "channel_url":        info.get("channel_url") or info.get("uploader_url") or "",
            "video_url":          url,
            "video_id":           video_id,
            "thumbnail_url":      thumbnail_url,
            "duration_seconds":   duration_s,
            "duration_formatted": _format_duration(duration_s),
            "view_count":         f"{view_count:,}",
            "like_count":         f"{like_count:,}",
            "upload_date":        _format_date(info.get("upload_date")),
            "description":        (info.get("description") or "")[:500],
            "tags":               (info.get("tags") or [])[:10],
        }

    except Exception as e:
        print(f"  Could not fetch metadata for {video_id}: {e}")

        # Return safe stub so Actor never crashes on metadata failure
        return {
            "title":              f"YouTube Video ({video_id})",
            "channel_name":       "Unknown",
            "channel_url":        "",
            "video_url":          url,
            "video_id":           video_id,
            "thumbnail_url":      None,
            "duration_seconds":   0,
            "duration_formatted": "Unknown",
            "view_count":         "0",
            "like_count":         "0",
            "upload_date":        "Unknown",
            "description":        "",
            "tags":               [],
        }


def _format_duration(total_seconds: int) -> str:
    if not total_seconds:
        return "Unknown"
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    if h > 0:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"


def _format_date(yt_date: str | None) -> str:
    if not yt_date or len(yt_date) != 8:
        return "Unknown"
    try:
        dt = datetime.strptime(yt_date, "%Y%m%d")
        return dt.strftime("%b %d, %Y")
    except Exception:
        return yt_date or "Unknown"