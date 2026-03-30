# 🎬 YouTube Transcript to PDF Generator

> **Turn any YouTube video into a beautifully formatted PDF in seconds — no API keys, no manual copy-pasting, no hassle.**

---

## 💡 Why You Need This

You've watched a brilliant YouTube tutorial. A masterclass. A 2-hour deep dive. And now... it's gone. You can't search it. You can't highlight it. You can't read it on a plane.

**YouTube transcripts exist — but they're buried, ugly, and impossible to use.**

This Actor fixes that. Paste any YouTube URL, get a clean, professional PDF with the full transcript, cover page, video metadata, and thumbnail. Ready to read, share, archive, or feed into your AI workflows.

---

## ✨ What Makes This Different

| Feature | This Actor | Manual Copy-Paste | Other Tools |
|---|---|---|---|
| Professional PDF with cover page | ✅ | ❌ | ❌ |
| Video thumbnail + metadata | ✅ | ❌ | ❌ |
| Batch process multiple videos | ✅ | ❌ | ❌ |
| Removes [Music] [Applause] noise | ✅ | ❌ | ❌ |
| Clean justified paragraphs | ✅ | ❌ | ❌ |
| Optional timestamps per line | ✅ | ❌ | Rarely |
| No API key required | ✅ | ✅ | ❌ |
| Works on any public video | ✅ | ✅ | Sometimes |

---

## 🚀 Use Cases

**📚 Students & Researchers**
Convert lecture videos, TED talks, and educational content into study material you can annotate, highlight, and search.

**✍️ Content Creators**
Repurpose competitor content analysis, transcribe your own videos for blog posts, or extract scripts for editing.

**🏢 Businesses & Teams**
Archive webinars, training videos, and conference talks as searchable PDF documents for your knowledge base.

**🤖 AI & Automation Workflows**
Feed clean transcripts into ChatGPT, Claude, or your RAG pipeline. PDFs are already formatted — no preprocessing needed.

**📰 Journalists & Writers**
Transcribe interviews, press conferences, and source material instantly. No more replaying the same 30-second clip.

---

## 📄 What the PDF Looks Like

Every generated PDF includes:

- **Cover page** with video thumbnail, title, channel name, duration, view count, and publish date
- **Clean transcript** merged into readable justified paragraphs (no more one-word lines)
- **Optional timestamps** `[MM:SS]` if you need to reference back to the video
- **Page numbers** on every page
- **Professional typography** using Helvetica with proper line spacing

---

## ⚡ How to Use

### 1. Basic — Single Video
```json
{
  "urls": ["https://www.youtube.com/watch?v=YOUR_VIDEO_ID"],
  "language": "en",
  "includeMetadata": true,
  "cleanTranscript": true
}
```

### 2. Batch — Multiple Videos at Once
```json
{
  "urls": [
    "https://www.youtube.com/watch?v=VIDEO_1",
    "https://www.youtube.com/watch?v=VIDEO_2",
    "https://www.youtube.com/watch?v=VIDEO_3"
  ],
  "language": "en"
}
```

### 3. With Timestamps (great for reference material)
```json
{
  "urls": ["https://www.youtube.com/watch?v=YOUR_VIDEO_ID"],
  "includeTimestamps": true
}
```

### 4. Non-English Video
```json
{
  "urls": ["https://www.youtube.com/watch?v=YOUR_VIDEO_ID"],
  "language": "hi"
}
```
Supports any language YouTube provides captions for — `en`, `hi`, `es`, `fr`, `de`, `ja`, `pt`, `ar`, and more.

---

## 📥 Input Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `urls` | `Array` | **Required** | One or more YouTube video URLs |
| `language` | `String` | `en` | Preferred caption language code |
| `includeTimestamps` | `Boolean` | `false` | Add `[MM:SS]` timestamps to each line |
| `includeMetadata` | `Boolean` | `true` | Cover page with thumbnail and video info |
| `cleanTranscript` | `Boolean` | `true` | Remove `[Music]` `[Applause]` annotations |
| `proxyConfiguration` | `Object` | optional | Proxy settings (required for cloud runs) |

---

## 📤 Output

### Dataset (one row per video)
```json
{
  "status": "success",
  "videoId": "dQw4w9WgXcQ",
  "title": "Rick Astley - Never Gonna Give You Up",
  "channelName": "Rick Astley",
  "durationFormatted": "3m 33s",
  "wordCount": 412,
  "segmentCount": 87,
  "language": "en",
  "pdfKey": "transcript_dQw4w9WgXcQ",
  "filename": "Rick_Astley_Never_Gonna_Give_You_Up_dQw4w9WgXcQ.pdf",
  "processedAt": "2025-01-01T00:00:00.000Z"
}
```

### Key-Value Store
Each PDF is saved as `transcript_{videoId}` with content type `application/pdf`. Click the key in your run's Storage tab to download instantly.

---

## ⚙️ Proxy Configuration

YouTube blocks requests from cloud provider IPs (AWS, GCP, Azure). A residential proxy routes requests through a real home IP address to bypass this.

**Recommended:** Use Apify Residential Proxy — select it from the proxy picker in the input form. Each user is charged for their own proxy usage independently.


---

## ❓ FAQ

**Q: Does it work on videos without manual captions?**
Yes. It automatically falls back to YouTube's auto-generated captions if manual captions aren't available.

**Q: What languages are supported?**
Any language that YouTube provides captions for. Pass the ISO language code in the `language` field (e.g. `hi` for Hindi, `es` for Spanish).

**Q: Can I process an entire YouTube playlist?**
Pass multiple URLs in the `urls` array. For full playlist support, combine this Actor with a YouTube playlist scraper to extract all video URLs first.

**Q: Why is the video title showing as "YouTube Video (ID)"?**
The proxy may not be configured. Metadata fetching requires a proxy on cloud runs. Enable Apify Residential Proxy in the input.

**Q: How long does it take?**
Most videos process in 5–15 seconds. Longer videos (1+ hour) may take up to 30 seconds.

**Q: What happens if a video has no captions?**
The Actor logs a clear error for that video and continues processing the rest. It never crashes on a single failure.

---

## 📊 Performance

- ⚡ Average processing time: **8 seconds per video**
- 📄 Average PDF size: **150–400 KB**
- 🔢 Tested on videos up to **4 hours long**
- 🌍 Tested with **15+ languages**
- ✅ Success rate: **95%+** on videos with captions enabled

---

## 💬 Support

Found a bug or have a feature request? Use the **Issues** tab on this Actor's page. Responses within 24 hours.

---

*Stop watching videos twice. Get the transcript, get the PDF, get on with your work.*