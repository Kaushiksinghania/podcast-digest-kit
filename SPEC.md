# SPEC — Podcast Digest pipeline

The normative specification. `SETUP.md` tells you how to stand it up; this file tells you
exactly what the pipeline does and where the sharp edges are.

Written to be **implemented by an agent in any stack**. Where a step is fiddly, there is
pseudocode. Where a trap cost real debugging time, it is called out as a **⚠️ TRAP** with the
fix. Nothing here requires a specific vendor, framework, or language.

---

## §1 — Purpose and invariants

**Input:** an RSS feed list, a time window.
**Output:** for each new episode — a transcript file, a canonical JSON record, a rendered
human-readable digest, and an entry in the user's chosen destination. Then one batched
delivery per run.

Four invariants. If a step conflicts with one of these, the invariant wins:

| # | Invariant | Why |
|---|---|---|
| I1 | **The transcript is the source of truth.** Takeaways come from the transcript, never from the show notes, never from a web summary. | Show notes describe what the episode is *about*; the transcript is what was *said*. Conflating them is how you get plausible-sounding invention. |
| I2 | **Every claim must be traceable to a transcript span.** Quotes are verbatim or omitted. | This output gets used in real conversations. A fabricated quote is worse than no quote. |
| I3 | **The transcript never enters the orchestrator's context more than once — ideally never.** It lives on disk; summarisation reads it, rendering reads it from disk. | Context blow-ups are the #1 cause of failed runs. |
| I4 | **An episode is never marked processed until its record is confirmed written** (read back from the destination). | Otherwise a transient write failure silently drops it forever. |

---

## §2 — The window

Episodes are selected by publication time, in a window with **both** edges:

```
now          = current time (UTC)
older_edge   = now - since_hours
newer_edge   = now - until_hours
keep episode if  older_edge <= published <= newer_edge
```

The default `since 76 / until 48` assumes **daily** runs: it covers 76→48 hours ago, so there is
a 24-hour overlap with the previous run (protecting against a missed run) while excluding the
last 48 hours (protecting against an episode publishing late and arriving mid-write).

**⚠️ TRAP — the window must tile with your schedule.** A 28-hour window on a twice-weekly cron
loses episodes. Rule of thumb:

```
since_hours = interval_hours + 24
until_hours = 24
```

Daily → `76/48`. Every 3.5 days → `108/24`. Weekly → `192/24`.

**⚠️ TRAP — clock skew and timezones.** Feed dates carry arbitrary offsets and some feeds use
garbage dates. Parse to UTC, keep entries with an unparseable date only if they are *newer* than
the newest item already processed (fall back to entry order). Never assume feed order is
chronological.

---

## §3 — Step 1: poll the feeds

```python
# pseudocode
feeds = load_json(feeds_file)          # {key: {name, rss, apple_id, ...}}
results = []
for key, meta in feeds.items():
    try:
        body = http_get(meta["rss"], timeout=20)
        parsed = parse_rss(body)
    except Timeout, HTTPError:
        log_warning(key)               # a dead feed must NEVER abort the run
        continue
    for entry in parsed.entries:
        if in_window(entry.published, since_hours, until_hours):
            results.append({
                feed_key: key,
                podcast:  meta["name"],
                title:    entry.title,
                published: entry.published (UTC),
                link:     entry.link,
                audio_url: first audio enclosure href,
                description: entry.summary (truncated ~2000 chars)
            })
sort results by published ascending
return results
```

Rules:

- **A single failing feed must never fail the run.** Log and continue. In practice 1–2 feeds a
  week time out; that is normal.
- **Never treat the description as the transcript.** Keep it for guest/topic hints only (I1).
- **Deduplicate by episode link/guid, not by title** — shows republish episodes under new titles.
- Cap the run at `episodes_per_run_max` (default 8) and carry the overflow to the next run, so a
  backlog can't produce a 40-episode monster.

A reference implementation is in `reference-impl/check_feeds.py`.

---

## §4 — Step 2: resolve the *true* episode, then verify it

This is where most naive implementations die. Getting *a* transcript is easy; getting the
*right* one is the hard part.

### 4a. Find a candidate source

In order of preference:

1. **Annotated transcript on the show's own site.** Some feeds mark
   `website_transcripts: true` (see `feeds.json`). If the episode's own page publishes a
   speaker-labelled transcript, use it — no ASR, no diarization, best quality.
2. **A long-form YouTube upload.** Search the episode title (+ guest name) and take a candidate.
   Prefer the channel that matches the show.
3. **The RSS audio itself.** Always available; most expensive to transcribe.

```python
# candidate discovery via yt-dlp search
yt-dlp --flat-playlist \
       --print "%(id)s | %(duration)s | %(channel)s | %(title)s" \
       "ytsearch6:<episode title> <guest name>"
```

**⚠️ TRAP — clip-length matches.** A 90-second clip of the same episode will rank first. Reject
any candidate whose duration is far below the feed's `<itunes:duration>`, or below ~15 minutes
for an interview show.

### 4b. Verify the transcript head against the topic — mandatory

```
head = transcript[:500].lower()
if no meaningful token overlap with episode title + guest name:
    REJECT and try the next candidate
```

**⚠️ TRAP — topically identical, wrong episode.** The failure mode is subtler than "wrong
show": you get a *real* episode of the *right* show, on the *same topic*, from a *different
year*. Only the head check catches it. A real example: a search for a 2026 health episode
returned a 2024 episode of the same show on the same subject. The takeaways would have been
fluent, confident, and about the wrong conversation.

**⚠️ TRAP — wrong language.** Some uploads have auto-captions in the uploader's locale. The
symptom is a transcript full of another script. Fix: re-request explicitly with `lang=en`
against the *correct* video id. This resolves it most of the time — try it **before** falling
back to audio transcription.

### 4c. Record what you did

Every episode carries a `method` field: `website | supadata | whisper | diarize | fallback`.
The rendered output states it, so a reader knows how much to trust the depth.

---

## §5 — Step 3: acquire the transcript

Tier chain, best to worst. Stop at the first that returns usable text.

```
1. website transcript   (if the feed exposes one)      → method=website
2. Supadata             (YouTube id, lang=en)          → method=supadata
3. Whisper / any STT    (RSS audio, chunked)           → method=whisper
4. Diarize.io           (URL-based, speaker labels)    → method=diarize
5. show notes only                                     → method=fallback  (MARK AS SHALLOW)
```

### Supadata (recommended primary)

```
GET https://api.supadata.ai/v1/youtube/transcript?url=<youtube_url>&lang=en
Header: x-api-key: $SUPADATA_API_KEY
→ { content: [ { text, offset, duration }, ... ] }  or  { content: "<plain text>" }
```

Join segments into plain text. Keep it on disk.

### Whisper (fallback — chunking is mandatory)

```bash
# 1. fetch audio
curl -sSL -o ep.mp3 "$AUDIO_URL"

# 2. transcode to mono 16 kHz — this is what stops the 413
ffmpeg -i ep.mp3 -ac 1 -ar 16000 -b:a 32k ep_small.mp3

# 3. segment safely under the upload limit
ffmpeg -i ep_small.mp3 -f segment -segment_time 1200 -c copy chunk_%03d.mp3

# 4. POST each chunk
curl -sS "$STT_OPENAI_BASE_URL/audio/transcriptions" \
  -H "Authorization: Bearer $STT_OPENAI_KEY" \
  -F file=@chunk_000.mp3 \
  -F model=whisper-large-v3 \
  -F response_format=json
```

**⚠️ TRAP — HTTP 413.** Copying the source bitrate into segments produces files over the upload
limit (a 320 kbps, 129 MB episode is the classic case). Always transcode to mono 16 kHz first.

**⚠️ TRAP — parallel chunk uploads get rate-limited or billed twice.** Transcribe chunks
**sequentially**. The temptation to fan out is real and it fails.

**⚠️ TRAP — some environments cannot reach `api.openai.com` directly** but can reach an
OpenAI-compatible gateway. Use `STT_OPENAI_BASE_URL` + `STT_OPENAI_KEY` rather than hardcoding
a vendor URL.

### Diarize.io (speaker labels)

```
POST https://diarize.io/api/v1/jobs      { "sourceUrl": "<youtube|x|instagram|tiktok url>" }
GET  https://diarize.io/api/v1/jobs/<id>   → poll until status=COMPLETED
→ segments of the form "[speaker] text"
```

**⚠️ TRAP — URL-only.** It does not accept raw audio. Audio-only shows therefore cannot use it
and must fall back to Whisper + LLM attribution.

**⚠️ TRAP — free-tier quota.** It is measured in hours, and a few long episodes exhaust it.
Gate it to interview-heavy feeds rather than making it the default.

### Fallback

If nothing works, set `method=fallback`, use only the description, and **explicitly mark the
output shallow** in both the record and the delivery. Do not pad. Two honest lines beat eight
invented ones.

---

## §6 — Step 4: speaker attribution

Two situations:

**Annotated transcript** — speakers already labelled (website transcripts, diarize output).
Map labels to host/guest and move on.

**Raw ASR** — no labels. Then:

1. **Identify host and guest by name before reading for content.** The host is resolved *per
   episode* from the show notes, never hardcoded — several shows rotate hosts. The guest comes
   from the episode title plus a web search.
2. **Attribute turns** using the interview pattern: host asks short questions and reacts; guest
   gives long answers. Verbal cues help ("great to have you", "welcome back", "thanks for
   having me", first-name vocatives).
3. **Split the output** into guest takeaways and host takeaways. Never merge them — the host's
   own view is frequently the most valuable part and it disappears in a merged list.

Edge cases that recur:

| Case | Handling |
|---|---|
| Solo show (no guest) | Everything is host takeaways; leave guest fields empty |
| Panel / multi-host | Put all hosts in the host field and attribute by name inside the body |
| News-roundup episode | No guest — all host, attribute per host by first name |
| Host genuinely uncredited | Say "the host" rather than guessing a name |

**⚠️ TRAP — first names are ambiguous.** Two hosts both named in the ASR are usually safe to
attribute by first name; a guest sharing a first name with a host is not. When in doubt,
attribute by role ("the guest", "the host") rather than inventing precision.

**⚠️ TRAP — ASR mangles proper nouns.** Expect garbled names, especially Indian and non-English
ones. Cross-check any name that matters against the show notes and a web search. Keep a per-show
correction list once you've seen a name mangled twice — it pays for itself.

---

## §7 — Step 5: the takeaway framework

This is the part that makes the output worth keeping. Run it **per episode**, on the diarized
transcript.

### Prompt (adapt, don't dilute)

```
You are writing an investment-grade brief on a single podcast episode. The reader is a
professional who will use this in meetings without re-listening.

HARD RULES
- Use ONLY the transcript below. Never use show notes or outside knowledge for claims.
- Every quote must be VERBATIM. If you cannot find the exact words, omit the quote.
- Every number must appear in the transcript. No rounding, no estimating, no inferring.
- No preamble. Do not write "In this episode, X sits down with Y." Start with the substance.
- If a section has nothing genuine, omit it. Never pad.

OUTPUT — these sections, in this order:

GUEST TAKEAWAYS (6-8)
  Each: an OPINIONATED TITLE (a claim, not a topic), then 3-5 sentences.
  Carry the specific numbers, company names, frameworks and dollar amounts used.
  Titles: ✅ "Valuation matters least — but it matters"  ❌ "Discussion about valuation"

HOST TAKEAWAYS (2-4, omit if the host only asked questions)
  Same depth. The host's own views, not their questions.

MENTAL MODELS & FRAMEWORKS
  Each: name, then 2-3 sentences explaining the LOGIC — not just the label.

OPERATOR & INVESTOR LESSONS (3-6)
  Each: title, then 2-3 sentences. Actionable — what to do, avoid, or watch for.

CONFIRMATORY & CONTRADICTORY SIGNALS
  An obvious external data point that supports / complicates the central thesis.
  ONLY if genuinely obvious from the transcript's own framing. Omit otherwise.

NOTABLE QUOTES (3-4)
  Verbatim, attributed to the speaker, and memorable.

EPISODE METADATA
  guest: full name, role, company, 1-2 line background
  host:  full name
  summary: <=200 characters, no fluff

TRANSCRIPT:
<transcript>
```

### Why each rule exists

| Rule | The failure it prevents |
|---|---|
| Opinionated titles | Topic labels ("Discussion about pricing") are unsearchable six weeks later |
| 3–5 sentences | One-line bullets are useless without the reasoning |
| Numbers from the transcript | A summariser will happily import a figure from the show notes that was never spoken |
| Verbatim quotes only | Paraphrased "quotes" get repeated as quotes |
| Split guest/host | Merging loses the interviewer's own thesis |
| Omit empty sections | Forced "Confirmatory signals" produce fiction |
| No preamble | It survives into every downstream copy |

### Fan-out discipline

Summarisation is the token-heavy step. Process episodes as **one isolated child task per
episode, in a single batch**, each writing its own record file to disk and returning nothing but
a one-line confirmation.

**⚠️ TRAP — child agents drift on schema.** Left unconstrained, a child will invent its own keys
(`operator_lessons`, `notable_quotes`, `takeaway` instead of `body`) or truncate an id. Give each
child the **exact schema** and the episode metadata, then **validate every record before
rendering** (§8.1) and retry only the failing one.

**⚠️ TRAP — a child's numbers are not evidence.** A child may report a figure that appeared in
the show notes' link, not the audio. Spot-check any number that will be repeated.

---

## §8 — Step 6: the canonical record

One JSON file per episode. This is the portable artifact — everything else (Notion, Sheets,
markdown) is a projection of it.

```json
{
  "title": "string",
  "podcast": "string",
  "date": "YYYY-MM-DD",
  "url": "string — canonical episode link",
  "spotify_url": "string — optional",
  "host": { "name": "string" },
  "guest": {
    "name": "string",
    "role": "string",
    "company": "string",
    "background": "string",
    "linkedin": "string — optional"
  },
  "guest_label": "string — display name, empty for solo shows",
  "host_label": "string",
  "summary": "string — <=200 chars",
  "guest_takeaways": [ { "title": "string", "body": "string" } ],
  "host_takeaways":  [ { "title": "string", "body": "string" } ],
  "mental_models":   [ { "name": "string", "explanation": "string" } ],
  "lessons":         [ { "title": "string", "body": "string" } ],
  "confirmatory": "string — optional",
  "contradictory": "string — optional",
  "quotes": [ "Speaker — verbatim text" ],
  "transcript_file": "path",
  "method": "website|supadata|whisper|diarize|fallback"
}
```

### §8.1 Validate before rendering

```
required = [title, podcast, date, url, host, guest, guest_label, host_label,
            summary, guest_takeaways, host_takeaways, mental_models, lessons, quotes]
assert all keys present                       # missing key → retry that episode
assert guest_takeaways or host_takeaways      # empty output → retry, then flag
assert all(isinstance(q, str) for q in quotes)
assert len(summary) <= 200
```

**⚠️ TRAP — a missing key crashes the renderer** (typically `guest_label`, which a child will
cheerfully omit because solo shows make it empty). Default missing string fields to `""` and
missing lists to `[]` **only after** failing validation once.

---

## §9 — Step 7: render and deliver

Render from the record, not from the transcript (I3). One batched output per run.

```markdown
# Podcast Digest — {date} ({n} episodes)

{n} new episodes — {show}, {show}, ...

---

## {episode title}
**{podcast}** with {host} | {Month Year}
[Spotify]({spotify_url}) · [Source]({url})

**{guest name}**, {role} at {company}. {background}. [LinkedIn]({linkedin})

### Guest Takeaways — {guest}
1. **{title}** — {body}
...

### Host Takeaways — {host}
1. **{title}** — {body}

### Mental Models & Frameworks
- **{name}:** {explanation}

### Operator & Investor Lessons
- **{title}:** {body}

### Confirmatory & Contradictory Signals
**Confirmatory:** ... / **Contradictory:** ...

### Notable Quotes
> "{quote}"

*Transcript: {method}*

---
```

**⚠️ TRAP — HTML email renders as raw tags.** If your delivery is email, the body must be sent
as HTML *and* explicitly flagged as HTML, wrapped in a full styled `<html><head><style>…`
document. A bare `<body>` renders cramped and broken on mobile. If you cannot reliably control
this, choose a non-email channel (SETUP.md §3).

**⚠️ TRAP — send storms.** If a send fails and you add an automatic retry, the retry **must**
first check whether the message already went out. A naive "is it in Sent Items?" check that reads
the mailbox oldest-first and unfiltered will always answer "no", and you will resend the same
digest every few minutes until the retry budget expires. Always check **newest-first, filtered to
the last few hours**, and cap at one send per run, full stop.

---

## §10 — What "good" looks like

Keep a reference example of a good single-episode output next to this spec and diff against it
when quality drifts. The signals of a good record:

- You can hold an informed conversation about the episode from the record alone
- Titles are claims you could argue with
- Every number in it can be found in the transcript
- The host section exists and is not filler
- Guest background is accurate (role and company verified, not inferred from the title)
- Nothing in the output would survive if the transcript disappeared — i.e. it is all grounded

Signals of a bad one: "In this episode…", topic-label titles, no numbers, no quotes, a guest
section that restates the show notes, and eight takeaways that could have been written without
listening.

---

## §11 — Failure modes, ranked by how often they bite

| # | Failure | Symptom | Fix |
|---|---|---|---|
| 1 | Transcript in context | Run dies mid-way; "connect timeout"; huge token bill | I3 — transcripts stay on disk; summarise from a file read, never paste |
| 2 | Wrong episode matched | Fluent, confident, about the wrong conversation | §4b head check; reject and retry |
| 3 | Wrong language | Transcript in the uploader's locale | Re-request `lang=en` on the correct id, before Whisper |
| 4 | Clip instead of episode | Very short transcript, thin takeaways | Duration check against feed metadata |
| 5 | 413 on audio upload | Whisper fails every chunk | Transcode mono 16 kHz, segment ~20 min |
| 6 | Parallel chunk uploads | Rate limits, double billing, partial transcripts | Transcribe sequentially |
| 7 | Child schema drift | Renderer crashes on a missing key | §8.1 validate; retry the failing episode only |
| 8 | Hub name mangling | Wrong names in output | Cross-check proper nouns; keep a per-show correction list |
| 9 | Quote not verbatim | A quote you can't find in the transcript | Grep the transcript for every quote before publishing |
| 10 | Number imported from the show notes | A figure in the brief that was never spoken | Every number must appear in the transcript; spot-check the ones you'd repeat |
| 11 | Send storm | Same digest arrives repeatedly | Newest-first filtered sent-check; one send per run |
| 12 | Feed timeout aborts run | Zero episodes despite new ones | Per-feed try/except; log and continue |
| 13 | Window gap | Episodes silently missed | Tile the window to the schedule (§2) |
| 14 | Marked processed before write | Episode lost forever | I4 — confirm the read-back first |
| 15 | Transcript file name collision | Episodes overwrite each other | Key files by stable episode id/guid, not title |
| 16 | Diarize quota exhausted | Silent fallback to unlabelled text | Gate diarization to interview-heavy feeds |

---

## §12 — Extending

- **Add a feed:** one entry in `feeds.json` (`name`, `rss`, optional `website_transcripts`).
  Nothing else changes.
- **Change the framework:** edit §7. Keep the hard rules — they are what stop invention.
- **Add a destination:** project the §8 record onto it. Don't fork the pipeline.
- **Change cadence:** recompute the window (§2). This is the only schedule-coupled parameter.

---

*Created by Rahul Mathur · rahul@devc.com*