# Agent instructions for this repository

This is a portable podcast-digest workflow, not a vendor-specific app or a completed backend.

1. Read `SETUP.md` before taking setup actions and use `SPEC.md` as the normative processing and schema reference.
2. Ask the user which RSS feeds and destination to use. Treat `feeds.json` as an example, not as the user's actual subscriptions.
3. Check actual tool permissions before promising web access, transcription, destination writes, notifications, or scheduling.
4. Smoke-test a single episode, verify the transcript/quotes and destination read-back, and mark it processed only after a successful write.
5. Never commit secrets, private user data, full third-party transcripts, digests, or runtime state. Respect publishers' rights and service terms.

For supported Agent Skills loaders, also read `SKILL.md`. For other platforms, `SETUP.md` is sufficient to begin.