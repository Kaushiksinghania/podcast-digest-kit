# Destination example — Google Sheets (or Airtable)

A sheet is the lightest useful destination: you can skim a row per episode, sort by guest, and
pivot on podcast. It is less good for long text (cells get unwieldy) — so the pattern is
**metadata in columns, substance in one long cell or a linked doc**.

## Header row

```
Date | Podcast | Episode | Host | Guest | Guest Role | Guest Company | LinkedIn |
Summary | Guest Takeaways | Host Takeaways | Mental Models | Lessons | Quotes | Source URL | Transcript
```

## How each record maps

| Column | From the record | Formatting |
|---|---|---|
| Date | `date` | ISO `YYYY-MM-DD` so sorting works |
| Podcast | `podcast` | plain text |
| Episode | `title` | plain text |
| Host | `host.name` | — |
| Guest | `guest.name` | empty for solo shows |
| Guest Role | `guest.role` | — |
| Guest Company | `guest.company` | — |
| LinkedIn | `guest.linkedin` | full URL |
| Summary | `summary` | ≤200 chars |
| Guest Takeaways | `guest_takeaways` | `1. **{title}** — {body}\n` joined |
| Host Takeaways | `host_takeaways` | same |
| Mental Models | `mental_models` | `- **{name}:** {explanation}\n` |
| Lessons | `lessons` | same |
| Quotes | `quotes` | one per line, prefixed `> ` |
| Source URL | `url` | hyperlink |
| Transcript | `transcript_file` | **link to the file, don't paste it** |

## Where people get this wrong

- **Don't paste the transcript into a cell.** Google Sheets caps a cell at 50,000 characters and
  silently truncates. Keep the transcript as a file in Drive and link to it.
- **Don't let the agent "helpfully" reformat.** Markdown bold inside a cell shows as literal
  asterisks unless you use rich-text values. Either accept plain text (recommended — it's
  searchable) or use the API's rich-text format deliberately.
- **Freeze the first row and set the date column to date type** — otherwise you get 40 rows you
  can't sort, which defeats the point.
- **Append, don't rewrite.** Reading the whole sheet, adding a row, and writing it back will
  eventually race with a human editing at the same time. Use `append`.
- **Airtable equivalent:** columns become fields, `Publication` and `Type` become single-selects,
  and the transcript can be an attachment field instead of a link.

## A note on readability

A row with 8 takeaways crammed into one cell is not pleasant to read. If you find yourself
scrolling horizontally, you've outgrown the sheet — move to Notion (see `notion.md`) and keep the
sheet as a lightweight index of `Date | Podcast | Episode | Guest | Link`.