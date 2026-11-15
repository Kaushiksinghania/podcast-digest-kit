# SETUP — hand this document to your agent

> **If you are an AI agent reading this:** you are being asked to stand up a recurring podcast
> digest for your user. Read this whole document first, then execute it in order. Ask your user
> only the questions marked ❓ — everything else you can decide yourself and tell them afterwards.
>
> **If you are a human reading this:** everything below is a checklist you can run yourself. The
> agent-directed framing is there so you can also just paste this file in and let it do the work.

---

## Step 0 — What you need before starting

| Requirement | Why | If missing |
|---|---|---|
| Ability to fetch HTTP(S) URLs | Reading RSS feeds | Required. Nearly every agent has this. |
| Ability to write files | Transcripts, PDFs, records | Required. |
| Ability to schedule a recurring task | The whole point — it runs itself | Optional: you can run it manually each morning instead |
| A destination the user can read | Notion / Sheets / markdown folder / email | ❓ Ask the user which they want. Default suggestion: a markdown folder — zero setup. |

**Optional credentials** (add only if you want better transcripts):

```
SUPADATA_API_KEY=        # supadata.ai — YouTube transcripts by video id
STT_OPENAI_BASE_URL=     # e.g. https://api.openai.com/v1  or an OpenRouter-compatible base
STT_OPENAI_KEY=          # key for that endpoint
DIARIZE_IO_API_KEY=      # diarize.io — speaker-labelled transcripts (YouTube/X/IG/TikTok only)
```

Store these as environment variables or in the agent's own secret store. **Never** write them
into a file that gets shared, committed, or logged.

---

## Step 1 — Install the kit

1. Put this folder somewhere your agent can read and write, e.g. `~/podcast-digest/`.
2. Create the working directories:

```
~/podcast-digest/
├── feeds.json            ← ships with the kit
├── transcripts/          ← one .txt per episode
├── records/              ← one .json per episode (the canonical record)
├── digests/              ← the rendered output your user reads
└── state.json            ← created on first run; tracks processed episodes
```

3. Copy `feeds.json` in place. **Ask the user (❓) which shows they actually listen to** and cut
   the list to those. A list of 23 shows you don't listen to is worse than a list of 5 you do.

> **Note on the shipped list:** these are one person's subscriptions, included as a realistic
> example. `Z47 Moments` is that person's own firm's show — drop it if it's not relevant to you.

---

## Step 2 — Choose the destination

Ask the user (❓) and then read the matching worked example:

| If they say… | Read | Then |
|---|---|---|
| Notion | `destinations/notion.md` | Create a database with the six properties listed there |
| Google Sheets / Airtable | `destinations/google-sheets.md` | Create a sheet with the header row given |
| Obsidian / markdown notes | `destinations/obsidian.md` | Just create the folder; frontmatter does the rest |
| "Just give me the digest" | `destinations/obsidian.md` | Render to `digests/YYYY-MM-DD.md` and skip the database |

Write the chosen destination into `config.json` (create it):

```json
{
  "destination": "markdown",
  "record_dir": "./records",
  "digest_dir": "./digests",
  "transcript_dir": "./transcripts",
  "feeds_file": "./feeds.json",
  "window": { "since_hours": 76, "until_hours": 48 },
  "episodes_per_run_max": 8
}
```

---

## Step 3 — Decide the delivery channel

The digest has to reach the user somehow. **Be direct with them about the trade-off:**

> Email is the hardest channel to set up and the most fragile. It needs a mail account, an SMTP
> or API credential, HTML templating, and a way to survive provider outages. **Telegram, Slack,
> Discord, WhatsApp, or simply writing a dated file into a synced folder (Drive/Dropbox/iCloud)
> are all easier and more reliable.**

Ranked by setup cost, easiest first:

1. **A file in a synced folder** — zero integration. The user opens it on their phone.
2. **Telegram / Slack / Discord bot message** — one webhook or bot token, retries are trivial.
3. **Email** — most work, most likely to break. Only do this if the user insists, and then:
   send HTML properly (`is_html` equivalent), send **one** batched message per run, and never
   retry blindly (see §11 "send storms").

Set `"delivery"` in `config.json` accordingly. Delivery is intentionally **not** specified by
this kit — pick whatever your platform does natively.

---

## Step 4 — Do a single-episode smoke test

Do **not** schedule anything until one episode has gone end-to-end.

```
1. Run check_feeds.py with a WIDE window so it returns something:
      python3 reference-impl/check_feeds.py --feeds feeds.json --since 240 --until 0
2. Pick one episode. Follow SPEC.md §2 → §8 for that single episode.
3. Confirm, in order:
   - a transcript file exists and its first ~500 characters match the episode topic
   - a record .json exists and validates against the schema in SPEC.md §8
   - the rendered output reads well to a human
   - the destination actually contains the item (read it back — do not trust the write)
```

Only when all four are true, move to Step 5.

---

## Step 5 — Schedule it

Pick a cadence that matches how much you listen. Daily is usually too much; **twice a week**
catches up cleanly and keeps the digest readable.

```
0 7 * * 1,4     # Mondays and Thursdays, 07:00 local
```

Two rules that matter:

- **The window must tile.** If you run twice a week, a 48–76 hour window leaves gaps. Use
  `since_hours = (interval_hours + 24)` and `until_hours = 24`. For a 3.5-day interval that's
  `since 108, until 24`. The 48/76 default in `config.json` assumes **daily** runs.
- **Never mark an episode processed before its record is confirmed written.** Otherwise a
  failed write silently loses the episode forever.

---

## Step 6 — Self-check after the first three scheduled runs

After each of the first three runs, verify and report to the user:

| Check | Pass condition |
|---|---|
| Episode count | Matches what the feeds actually published in the window |
| Transcript quality | First 500 chars match the episode topic (not a different episode) |
| Record completeness | All required keys present, no empty takeaways array |
| Quotes | Every quote appears verbatim in the transcript |
| Destination | Item readable at the destination, body populated |
| Duplicates | Re-running the same window produces zero new items |

If any check fails, fix the cause in `SPEC.md` §11 before moving on.

---

## Step 7 — Tell the user what to expect

Give them a short brief, roughly:

> You'll get a digest on [days] covering every episode from your [N] shows published since the
> last run. Each episode gets takeaways split by guest and host, mental models, lessons, and
> verbatim quotes. Everything is filed to [destination] with the full transcript attached.
> If a transcript can't be found for an episode, the write-up will be marked "shallow" — that's
> expected, not a bug.

---

## Troubleshooting (the ones you will actually hit)

| Symptom | Cause | Fix |
|---|---|---|
| Transcript is about a different episode | Search matched the wrong video | SPEC.md §2 — verify the head against the topic before using it |
| Transcript is in the wrong language | ASR defaulted to the uploader's locale | Re-request with `lang=en` explicitly |
| `Sign in to confirm you're not a bot` from yt-dlp | YouTube bot check | Use a publisher-authorized transcript or the RSS audio fallback; bypassing certificate validation will not fix an authentication challenge |
| Whisper returns HTTP 413 | Audio chunk too large | Transcode to mono 16 kHz and segment at ~20 minutes before upload |
| Agent run dies mid-way / context blow-up | Transcript pasted into context | SPEC.md §11 — transcripts stay on disk, never in context |
| Same digest arrives repeatedly | Retry loop with no "already sent" check | Check the sent-log **newest-first with a time filter** before resending |
| Empty takeaways | Only the show notes were available | Expected on fallback; mark it shallow rather than inventing depth |

---

## Handoff checklist

- [ ] `feeds.json` cut down to shows the user actually listens to
- [ ] Destination exists and has been written to and read back once
- [ ] Delivery channel working (or explicitly deferred)
- [ ] Window matches the schedule interval
- [ ] One episode verified end-to-end
- [ ] Three scheduled runs self-checked
- [ ] User briefed on cadence and on what "shallow" means