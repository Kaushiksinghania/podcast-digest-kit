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