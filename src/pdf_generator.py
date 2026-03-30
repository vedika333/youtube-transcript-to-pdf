# src/pdf_generator.py
# ─────────────────────────────────────────────────────────────────────────────
# Generates PDF using WeasyPrint (HTML → PDF)
# Full Unicode support for ALL languages — Hindi, Arabic, Chinese, etc.
# Works because browsers/WeasyPrint use system fonts that cover all scripts
# No font downloading, no font registration, no failures
# ─────────────────────────────────────────────────────────────────────────────

import re
import requests
import base64
from io import BytesIO

from weasyprint import HTML, CSS


def _fetch_thumbnail_base64(url: str) -> str | None:
    """Download thumbnail and return as base64 data URI for embedding in HTML."""
    if not url:
        return None
    try:
        resp = requests.get(
            url,
            timeout=10,
            proxies={"http": None, "https": None},
        )
        resp.raise_for_status()
        b64 = base64.b64encode(resp.content).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        print(f"  Could not fetch thumbnail: {e}")
        return None


def _safe(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _build_html(
    metadata: dict,
    paragraphs: list,
    raw_transcript: list,
    include_timestamps: bool,
    include_metadata: bool,
    thumbnail_b64: str | None,
) -> str:
    """Build complete HTML document for PDF generation."""

    from .transcript_fetcher import format_timestamp

    # ── CSS ───────────────────────────────────────────────────────────────────
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap');

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        font-family: 'Noto Sans', 'Noto Sans Devanagari', 'Arial Unicode MS',
                     'DejaVu Sans', sans-serif;
        font-size: 11pt;
        color: #1a1a1a;
        line-height: 1.7;
    }

    /* ── Cover Page ── */
    .cover {
        background: #0f0f0f;
        min-height: 100vh;
        padding: 60px;
        page-break-after: always;
        position: relative;
    }

    .cover-bar {
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 8px;
        background: #ff0000;
    }

    .cover-label {
        color: #ff0000;
        font-size: 9pt;
        font-weight: bold;
        letter-spacing: 2px;
        margin-bottom: 30px;
        margin-top: 20px;
    }

    .cover-row {
        display: flex;
        gap: 20px;
        align-items: flex-start;
        margin-bottom: 20px;
    }

    .cover-thumbnail {
        width: 180px;
        height: 101px;
        object-fit: cover;
        border-radius: 4px;
        flex-shrink: 0;
    }

    .cover-title {
        color: #ffffff;
        font-size: 22pt;
        font-weight: bold;
        line-height: 1.3;
        margin-bottom: 8px;
    }

    .cover-channel {
        color: #aaaaaa;
        font-size: 13pt;
    }

    .cover-divider {
        border: none;
        border-top: 1px solid #606060;
        margin: 20px 0;
    }

    .cover-stats {
        display: flex;
        gap: 0;
        margin-bottom: 16px;
    }

    .cover-stat {
        flex: 1;
    }

    .cover-stat-label {
        color: #aaaaaa;
        font-size: 8pt;
        font-weight: bold;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }

    .cover-stat-value {
        color: #ffffff;
        font-size: 15pt;
        font-weight: bold;
    }

    .cover-url {
        color: #aaaaaa;
        font-size: 9pt;
        word-break: break-all;
        margin-bottom: 16px;
    }

    .cover-desc-label {
        color: #aaaaaa;
        font-size: 8pt;
        font-weight: bold;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 20px;
        margin-bottom: 8px;
    }

    .cover-desc {
        color: #cccccc;
        font-size: 10pt;
        line-height: 1.6;
    }

    /* ── Transcript Page ── */
    .transcript-page {
        padding: 60px;
    }

    .section-label {
        color: #ff0000;
        font-size: 9pt;
        font-weight: bold;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .page-title {
        font-size: 18pt;
        font-weight: bold;
        color: #1a1a1a;
        line-height: 1.3;
        margin-bottom: 6px;
    }

    .page-channel {
        font-size: 10pt;
        color: #606060;
        margin-bottom: 16px;
    }

    .transcript-divider {
        border: none;
        border-top: 1px solid #e0e0e0;
        margin-bottom: 24px;
    }

    .paragraph {
        font-size: 11pt;
        color: #1a1a1a;
        line-height: 1.8;
        margin-bottom: 16px;
        text-align: justify;
    }

    .timestamp {
        color: #ff0000;
        font-size: 8pt;
        font-weight: bold;
        letter-spacing: 1px;
        margin-top: 12px;
        margin-bottom: 4px;
    }

    .ts-text {
        font-size: 10pt;
        color: #1a1a1a;
        line-height: 1.7;
        margin-bottom: 8px;
        margin-left: 12px;
    }

    /* ── Page numbers ── */
    @page {
        margin: 0;
        @bottom-center {
            content: counter(page) " / " counter(pages);
            font-family: 'Noto Sans', sans-serif;
            font-size: 8pt;
            color: #aaaaaa;
        }
    }

    @page :first {
        @bottom-center { content: ""; }
    }
    """

    # ── Cover Page HTML ───────────────────────────────────────────────────────
    cover_html = ""
    if include_metadata:
        thumb_html = ""
        if thumbnail_b64:
            thumb_html = f'<img class="cover-thumbnail" src="{thumbnail_b64}" alt="thumbnail">'

        desc_html = ""
        if metadata.get("description"):
            desc = metadata["description"][:500] + ("..." if len(metadata["description"]) > 500 else "")
            desc_html = f"""
            <hr class="cover-divider">
            <div class="cover-desc-label">Description</div>
            <div class="cover-desc">{_safe(desc)}</div>
            """

        cover_html = f"""
        <div class="cover">
            <div class="cover-bar"></div>
            <div class="cover-label">&#9654; YOUTUBE TRANSCRIPT</div>
            <div class="cover-row">
                {thumb_html}
                <div>
                    <div class="cover-title">{_safe(metadata['title'])}</div>
                    <div class="cover-channel">by {_safe(metadata['channel_name'])}</div>
                </div>
            </div>
            <hr class="cover-divider">
            <div class="cover-stats">
                <div class="cover-stat">
                    <div class="cover-stat-label">Duration</div>
                    <div class="cover-stat-value">{_safe(metadata['duration_formatted'])}</div>
                </div>
                <div class="cover-stat">
                    <div class="cover-stat-label">Views</div>
                    <div class="cover-stat-value">{_safe(metadata['view_count'])}</div>
                </div>
                <div class="cover-stat">
                    <div class="cover-stat-label">Published</div>
                    <div class="cover-stat-value">{_safe(metadata['upload_date'])}</div>
                </div>
            </div>
            <div class="cover-url">{_safe(metadata['video_url'])}</div>
            {desc_html}
        </div>
        """

    # ── Transcript Body HTML ──────────────────────────────────────────────────
    body_html = ""
    if include_timestamps:
        for item in raw_transcript:
            ts = format_timestamp(item.get("start", 0))
            body_html += f"""
            <div class="timestamp">[{ts}]</div>
            <div class="ts-text">{_safe(item['text'])}</div>
            """
    else:
        for para in paragraphs:
            body_html += f'<div class="paragraph">{_safe(para["text"])}</div>\n'

    # ── Full HTML Document ────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="auto">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{_safe(metadata['title'])}</title>
    <style>{css}</style>
</head>
<body>
    {cover_html}
    <div class="transcript-page">
        <div class="section-label">Transcript</div>
        <div class="page-title">{_safe(metadata['title'])}</div>
        <div class="page-channel">{_safe(metadata['channel_name'])}</div>
        <hr class="transcript-divider">
        {body_html}
    </div>
</body>
</html>"""

    return html


def generate_transcript_pdf(
    metadata: dict,
    paragraphs: list,
    raw_transcript: list,
    output_path: str,
    include_timestamps: bool = False,
    include_metadata: bool = True,
) -> str:
    """
    Build and save the transcript PDF using WeasyPrint.
    Full Unicode support — Hindi, Arabic, Chinese, any language works.
    Returns output_path.
    """
    print("  Fetching thumbnail...")
    thumbnail_b64 = None
    if include_metadata and metadata.get("thumbnail_url"):
        thumbnail_b64 = _fetch_thumbnail_base64(metadata["thumbnail_url"])

    print("  Building HTML...")
    html_content = _build_html(
        metadata=metadata,
        paragraphs=paragraphs,
        raw_transcript=raw_transcript,
        include_timestamps=include_timestamps,
        include_metadata=include_metadata,
        thumbnail_b64=thumbnail_b64,
    )

    print("  Rendering PDF...")
    HTML(string=html_content).write_pdf(output_path)

    print(f"  PDF saved: {output_path}")
    return output_path


def sanitize_filename(title: str, video_id: str) -> str:
    safe = re.sub(r'[^\w\s-]', '', title)
    safe = re.sub(r'\s+', '_', safe)[:60]
    return f"{safe}_{video_id}.pdf"