# Podcast Digest — one page

**Created by Rahul Mathur · rahul@devc.com**

---

### What it does

Teaches your AI agent to turn the podcasts you actually listen to into a structured, searchable
knowledge base — automatically, on a schedule. It finds each new episode, gets a real transcript,
and writes it up in a consistent format: what the guest argued, what the host argued, the mental
models, the lessons, and verbatim quotes. Then files it wherever you want.

It is not a summariser. A summary tells you the episode happened. This tells you what was said,
in enough depth to use in a meeting two weeks later without re-listening.

### What you get per episode

- **Guest takeaways (6–8)** — the actual arguments, 3–5 sentences each, with the numbers and names
- **Host takeaways (2–4)** — the interviewer's own views, kept separate (they're usually sharp)
- **Mental models** — the reasoning structures, explained not just named
- **Operator & investor lessons** — what to do differently
- **Confirmatory / contradictory signals** — only when genuinely obvious
- **Notable quotes (3–4)** — verbatim, attributed, checked against the transcript
- Guest name, role, company, background, LinkedIn · host · date · source links · full transcript

### How it works, in six steps

1. **Poll** your RSS list for episodes published in a window (e.g. 76→48 hours ago for a daily run)
2. **Resolve** the true episode — reject clips, wrong years, wrong languages
3. **Transcribe** — show's own transcript → YouTube transcript API → Whisper on the audio → none
4. **Attribute speakers** — identify host and guest *per episode*, never hardcoded
5. **Summarise** the diarised transcript against the framework, one isolated task per episode
6. **File** the record to your destination, then send one batched digest

### What you need

| Thing | Required? |
|---|---|
| An agent that can fetch URLs and write files | Yes |
| A scheduler (cron / scheduled task) | Optional — you can run it manually |
| Supadata key (YouTube transcripts) | Optional, improves quality |
| Whisper / any OpenAI-compatible STT endpoint | Optional, the audio fallback |
| Diarize.io | Optional — speaker labels for interview shows |

No keys are needed to start; you can run one episode end-to-end using show notes as a degraded
fallback. Add transcript keys when you want real depth.

### Where to file it

Your call. The kit defines one canonical record shape and shows three worked mappings:

- **Notion** — queryable, shareable, good filters
- **Google Sheets / Airtable** — skim a row per episode, pivot on guests
- **Markdown / Obsidian** — greppable, versionable, yours forever

The container is interchangeable. The record shape is the value.

### Deliver it however you like — but pick the easy channel

Email is the hardest option and the most fragile: it needs credentials, HTML templating, and it
breaks during provider outages. **Telegram, Slack, Discord, WhatsApp — or just writing a dated
file into a synced folder — are all easier and more reliable.** Every agent can write a file.

### The three rules that make it good

1. **The transcript is the source of truth.** Never the show notes, never a web summary. Notes say
   what an episode is about; the transcript says what was said.
2. **Quotes are verbatim or omitted.** Every number must appear in the transcript. A fabricated
   quote is worse than no quote.
3. **The transcript never sits in the agent's context.** It lives on disk. Context blow-ups are
   the single most common way these pipelines die.

### The traps it already knows about

Search returns *a* video that's often the wrong one — a clip, a different year, the same topic
from a different conversation. Wrong-language auto-captions. Audio uploads rejected for size.
Retry loops that re-send the same digest every three minutes. Agents that invent their own JSON
schema halfway through. Each one is documented with its fix in `SPEC.md` §11.

### Getting started

Hand `SETUP.md` to your agent. It asks two questions (which shows, which destination), then
configures everything, runs one episode end-to-end, and schedules itself. Then cut `feeds.json`
down to the shows you genuinely listen to — five beats twenty-three.

---

*MIT licensed. Fork it, change the sections to what you care about, keep the three rules.*