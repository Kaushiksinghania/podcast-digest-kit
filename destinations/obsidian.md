# Destination example — Obsidian / a markdown folder

The lowest-friction option, and the one I'd default to. No API, no schema, no rate limits — just
files that are yours forever, greppable, and versionable. It also happens to work well with most
agents, because writing a file is the one thing every agent can do.

## Folder layout

```
podcast-digest/
├── transcripts/
│   └── 2026-11-13-the-twenty-minute-vc-arthur-mensch.txt
└── notes/
    └── 2026-11-13-20vc-arthur-mensch.md
```

Key files by **date + a slug**, not by raw title — titles contain characters that break
filenames, and two shows can publish the same title on the same day.

## Note format

YAML frontmatter carries the queryable fields (Dataview, Obsidian search, and most agents all read
YAML directly); the body carries the substance.

```markdown
---
title: "Arthur Mensch on Europe's AI Moment"
podcast: "The Twenty Minute VC (20VC)"
date: 2026-11-13
host: "Harry Stebbings"
guest: "Arthur Mensch"
role: "Co-founder & CEO"
company: "Mistral AI"
linkedin: "https://www.linkedin.com/in/arthur-mensch"
url: "https://example.com/episode"
spotify: "https://open.spotify.com/episode/..."
method: supadata
tags: [podcast, ai, europe]
---

# Arthur Mensch on Europe's AI Moment

**The Twenty Minute VC** with Harry Stebbings · November 2026
[Spotify](...) · [Source](...)

**Arthur Mensch**, Co-founder & CEO at Mistral AI. ...

## Guest Takeaways — Arthur Mensch

1. **Open weights are a distribution strategy, not a philosophy** — ...
2. ...

## Host Takeaways — Harry Stebbings

1. ...

## Mental Models & Frameworks

- **Compute as the real moat:** ...

## Operator & Investor Lessons

- ...

## Notable Quotes

> "..."

## Transcript

[[2026-11-13-20vc-arthur-mensch]]

<!-- or, if you don't want graph links: -->
<!-- full transcript inline below, collapsed -->
```

## Why this works well

- **`method:` frontmatter is the honesty flag.** You can query for every shallow record and
  re-run those episodes later once a better transcript exists.
- **`tags:` is where the real value compounds.** Once a few hundred notes exist, a tag like
  `#pricing` or `#ai-infra` becomes a personal index that no podcast app gives you. Let the agent
  propose 2–4 tags per episode.
- **Wiki-links beat pasted transcripts.** Keeping the transcript as its own note means it's
  searchable without bloating every digest note.
- **Git it.** A markdown folder in a private repo gives you history, diffs, and a real backup for
  free.

## Where people get this wrong

- **If your agent can't write files, this destination won't work.** Check that first; it's a
  hard dependency.
- **Don't let the agent rename or reorganise old notes.** Append-only. Reorganisation destroys
  wiki-links and is never worth it.
- **Frontmatter must stay machine-parseable.** A stray unquoted colon in `title:` breaks YAML
  parsing for everything downstream. Quote every string value.
- **Same-day collisions.** Two episodes, same date, same show → include the episode slug, or a
  short id, in the filename.