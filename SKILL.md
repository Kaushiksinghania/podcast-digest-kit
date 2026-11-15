---
name: podcast-digest-kit
description: Build and run an evidence-grounded podcast digest from a curated list of RSS feeds. Use when the user asks to set up, run, or troubleshoot a podcast listening pipeline, transcribe new episodes, create a searchable podcast knowledge base, extract guest and host takeaways, or schedule podcast digests to Notion, Google Sheets, or Markdown/Obsidian.
---

# Podcast Digest

Use this repository's existing spec as the source of truth. This is an agent-guided workflow with two optional reference scripts, not a fully hosted service. Do not claim that setup, scheduling, transcript acquisition, or destination writes succeeded unless verified.

## 1. Configure

1. Read `SETUP.md` in full before starting a new installation. Consult `ONE-PAGER.md` for a concise overview.
2. Ask the user which podcasts to track and which destination to use; start from `feeds.json` only as an editable example, not as a claim about the user's own subscriptions.
3. Consult the corresponding mapping in `destinations/notion.md`, `destinations/google-sheets.md`, or `destinations/obsidian.md` when configuring output.
4. Use existing connector and file capabilities if available. Never invent access to a service or request raw credentials in a published file. Keep optional API keys only in the runtime's secret store or environment variables. Never write or commit them to the repository.
5. Ask before scheduling recurring work or sending outbound messages; if a scheduling or delivery capability is unavailable, produce a manual-run workflow instead.

## 2. Process episodes

1. Follow `SPEC.md` §§2–8 in order: select a window, poll RSS feeds, resolve the correct episode, acquire/verify a transcript, identify speakers, write takeaways, and validate the canonical JSON record.
2. For optional local automation, `reference-impl/check_feeds.py` can poll RSS; `reference-impl/get_transcript.py` offers transcript fallbacks. Review their dependencies and limitations in the scripts before executing.
3. Confirm episode identity, date, language, title, and speaker attribution. Do not treat episode descriptions, show notes, or search snippets as an actual transcript.
4. Keep full transcripts in files rather than pasting them into an agent conversation. If a credible transcript is unavailable, mark the output as a shallow/fallback digest and do not manufacture quotations or numbers.
5. Follow `SPEC.md` §7's output structure. Distinguish the guest's arguments from the host's views, explain mental models, make operator/investor lessons actionable, and omit unsupported sections. Attribute any direct quotation exactly; comply with applicable quotation limits and other platform policies.
6. Verify each numerical claim and quote against the source before including it. Do not assert an external corroboration unless you actually checked it, and clearly distinguish corroboration from what was said on the episode.

## 3. File and deliver

1. Use the canonical schema in `SPEC.md` §8 and validation gate in §8.1. Preserve empty-but-required fields for solo-host episodes; do not silently drop required keys.
2. Read `SPEC.md` §9 to render a batched digest; check the destination-specific mapping when writing or uploading. Read the record back to verify it exists.
3. Use episode IDs or canonical URLs for deduplication. Record successful processing only after the destination write succeeds.
4. Before automating, smoke-test one episode as described in `SETUP.md` §4, then select non-gapping windows for the desired cadence (`SETUP.md` §5).
5. Consult `SPEC.md` §11 to diagnose wrong-episode transcripts, missing speakers, oversized audio, duplicate deliveries, schema drift, and context overload.

## Files

- `SETUP.md`: exact setup sequence, secrets, smoke test, delivery and scheduling
- `SPEC.md`: complete pipeline, source verification, digest framework and record schema
- `feeds.json`: customizable example RSS list; not a representation of user history
- `destinations/`: mappings for Notion, Sheets, and Markdown/Obsidian
- `reference-impl/`: optional Python reference scripts, not a complete turnkey service
- `ONE-PAGER.md`: concise human overview