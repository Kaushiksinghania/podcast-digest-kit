# Destination example — Notion

Notion works when you want to **query** the archive: "every episode where the guest was a fintech
founder", "all takeaways about pricing", "what did I record in March". The database is just a
projection of the canonical record in `SPEC.md` §8 — nothing about the pipeline changes.

## Database shape

One row per episode. Six properties carry the queryable metadata; the page body carries the
substance.

| Property | Type | Value |
|---|---|---|
| **Name** (title) | Title | Episode title |
| **Publication** | Select | Podcast name, one option per show in `feeds.json` |
| **Date** | Date | Publication date |
| **Type** | Select | `Podcast` (add `Article` / `Video` later if you extend this) |
| **URL** | URL | Canonical episode link |
| **Summary** | Text | ≤200 characters |

Everything else goes in the **page body**, in this order — it keeps the page scannable and makes
the record readable on mobile:

```
## Guest Takeaways
1. **{title}** — {body}

## Host Takeaways
1. **{title}** — {body}

## Mental Models & Frameworks
- **{name}:** {explanation}

## Operator & Investor Lessons
- **{title}:** {body}

## Notable Quotes
> "{quote}"

## Full Transcript
{transcript}
```

## Where people get this wrong

- **Select options must pre-exist.** Writing a `Publication` value that isn't already an option
  in the database creates a silent ghost option or fails, depending on the API. Create the options
  when you add a feed, not when you write the first episode.
- **Don't put the transcript in a property.** Notion property values are size-limited; a
  60,000-character transcript belongs in the body, appended as paragraph blocks.
- **Append in batches.** Most APIs cap blocks per call (often 50). Chunk the transcript rather
  than trying to send it in one request.
- **Read back to confirm.** A successful write response is not proof the body populated. Fetch the
  page's blocks and confirm the count is non-zero before marking the episode processed (I4).
- **One database per language/topic, not per year.** Filtering by date beats hunting across
  databases.

## If you'd rather not use Notion

Keep the same six metadata fields as columns in a sheet, or as YAML frontmatter in a markdown
file. The container is genuinely interchangeable; the record shape is what matters.
## Podcast directory (companion database)

Next to the episode database, keep a second database, **Podcast directory** (Kaushik's: https://app.notion.com/p/426049ee99d8819195a7e3d19a712d2e, data source collection://426049ee-99d8-81e7-bcb9-000bb683a988), with one row per show
in `feeds.json`, active and parked. It is a readable view of the feed list, nothing more:
`feeds.json` stays the source of truth.

| Property | Type | From feeds.json |
|---|---|---|
| Show | title | the feed's key |
| Host / publisher | text | `host` |
| Status | select: Active, Parked | `parked` |
| Transcript source | text | `transcript_source` |
| Tags | multi-select | `categories` |
| RSS feed | url | `rss` |

At the start of every run, after reading `feeds.json`:

1. `python3 reference-impl/directory_rows.py --feeds feeds.json --out directory.json`
2. Query the Podcast directory database. Match rows by Show.
3. Add a row for each show that is missing, update any row whose properties differ, and move to
   trash any row whose show is no longer in `feeds.json`.

So adding, removing or parking a show is still a one-file edit to `feeds.json`; the directory
catches up on the next run.
