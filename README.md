# Podcast Digest — a portable agent-run listening pipeline

**Created by Rahul Mathur · rahul@devc.com** — questions, feedback, or "it broke on my setup," email me.

---

## Start here

**This kit is harness-agnostic.** It is a reusable workflow, not a hosted app or a ChatGPT-only product. Use it with Claude, ChatGPT, Codex, a local agent, or another assistant that can read files and access your chosen tools. Features like scheduling, web access, transcription, and Notion/Sheets writes depend on the capabilities and permissions of **your** agent.

**Fastest way, on any harness:** Fork, clone, or download the repository. Give your agent [`SETUP.md`](SETUP.md) and tell it to follow the instructions. [`SPEC.md`](SPEC.md) defines the output format and quality gates; [`HARNESS.md`](HARNESS.md) explains the platform choices and limitations.

**If your platform supports Agent Skills:** The top-level [`SKILL.md`](SKILL.md) provides a portable entrypoint for compatible skill loaders. It is **not** proprietary to ChatGPT. Install or copy the skill folder using your platform's supported mechanism; a GitHub link alone does not automatically install it. The optional [`agents/openai.yaml`](agents/openai.yaml) contains OpenAI display hints only, can be ignored by other platforms, and is not needed by the core pipeline.

**Optional Python helpers:** Install `pip install -r requirements.txt` to use the included RSS-polling and transcript reference scripts. Transcript and destination services may need separate credentials or permissions. These scripts are helpers, **not** an end-to-end automated service.

**Privacy and rights:** Keep local `config.json`, `.env`, transcripts, records, and digests private. These paths are excluded by `.gitignore`, but `.gitignore` does not protect files already committed or files stored elsewhere. Respect publishers' rights and platform terms when obtaining, storing, quoting, or sharing transcripts; this public repository contains no third-party full transcripts.

## What this is

A spec for teaching your own AI agent to turn the podcasts you already listen to into a
structured, searchable knowledge base — automatically, once a day or a few times a week.

You point it at a list of podcast RSS feeds. It finds every episode published in a window,
gets a real transcript, and then writes each episode up in a consistent format: what the guest
actually argued, what the host contributed, the mental models on display, the operational
lessons, and verbatim quotes worth remembering. Then it files that record wherever you want —
a Notion database, a Google Sheet, a folder of markdown notes, or just a dated file.

It is deliberately **not** a summariser. A summary tells you the episode happened. This tells
you what was *said*, in enough depth to use in a meeting two weeks later without re-listening.

## Why it's opinionated

Most podcast tooling optimises for coverage — transcribe everything, summarise everything,
rank by relevance. That produces a feed you skim and forget.

This does the opposite. It assumes a **short, deliberately curated** feed list and spends its
effort on depth per episode. The included 23-feed list is one person's actual subscription
list; treat it as a starting point, not gospel. Cut it to five shows you truly listen to and
the output gets better, not worse.

## What you get per episode

| Section | What's in it |
|---|---|
| **Guest Takeaways** (6–8) | The guest's actual arguments, 3–5 sentences each, with the numbers, company names and frameworks they used |
| **Host Takeaways** (2–4) | The interviewer's own views — hosts are often the sharper party and usually get flattened into "asked questions" |
| **Mental Models & Frameworks** | The reasoning structures on display, explained rather than just named |
| **Operator & Investor Lessons** | Actionable: what would you do differently after hearing this |
| **Confirmatory & Contradictory Signals** | External data points that support or complicate the episode's thesis — included only when genuinely obvious |
| **Notable Quotes** (3–4) | Verbatim, attributed to the speaker, checked against the transcript |

Plus: guest name, role, company, background and LinkedIn; host name; episode date; source links;
and the full transcript filed alongside.

## What's in the box

```
README.md                  ← you are here
SKILL.md                   ← portable Agent Skills entrypoint (optional)
agents/openai.yaml         ← optional OpenAI-only display metadata
.gitignore                 ← excludes local data, keys and generated transcripts
requirements.txt           ← Python helper dependency
SETUP.md                   ← step-by-step configuration, written to be handed to your agent
HARNESS.md                 ← choosing an installation route for any agent platform
AGENTS.md                  ← short repo-level instructions for coding agents
SPEC.md                    ← the pipeline spec: every step, the traps, the quality gates
feeds.json                 ← 23 podcast feeds with RSS URLs
destinations/
  notion.md                ← what the record looks like as a Notion database
  google-sheets.md         ← ... as a Google Sheet
  obsidian.md              ← ... as a folder of markdown notes
reference-impl/
  check_feeds.py           ← optional: RSS window poller
  get_transcript.py        ← optional: transcript acquisition with fallback chain
ONE-PAGER.md               ← the whole thing condensed to a single page
```

## Do I need any of this to be technical?

No. `SETUP.md` is written to be **pasted into your agent** — it tells the agent what to
configure, in what order, and how to check its own work. If you'd rather do it by hand, the
same document works as a checklist.

## Third-party services

Several are optional, and the pipeline degrades gracefully without any of them.

| Service | What it's for | Needed? |
|---|---|---|
| **Supadata** (`supadata.ai`) | Pulls YouTube transcripts by video id | Optional — strongest transcript path |
| **Whisper** (OpenAI, or any OpenAI-compatible STT endpoint e.g. OpenRouter) | Transcribes audio when no transcript exists | Optional — the fallback |
| **Diarize.io** | Speaker-labelled transcripts for interview shows | Optional — nice-to-have |
| Your **RSS reader / HTTP fetch** | Reading the feeds | Required (built into most agents) |

No API keys are required to *try* it — you can run a single episode end-to-end with only the
RSS feed and your agent's own web access, using show notes as a degraded fallback. Add Supadata
or Whisper when you want real transcripts.

## Cost & footprint

Roughly one transcript pull plus one long-context summarisation pass per episode. On a
typical paid API that's cents per episode; on a generous free tier it's free. The pipeline
processes episodes in parallel batches and never holds more than one transcript in context
at a time — that discipline is in the spec for a reason (see `SPEC.md` §11).

## Where to file it

Your call — the spec defines a canonical record shape and then shows three worked mappings.
Most people end up on one of:

- **Notion** — if you want to query it, filter it, and share it
- **Google Sheets** — if you want to skim a row per episode and pivot on guests
- **Markdown/Obsidian** — if you want it in your own notes graph, versioned, forever

None of these is more "correct." The value is the record shape, not the container.

---

*Licence: MIT — fork it, cut the feed list down, change the sections to what you care about.*