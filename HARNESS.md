# Use Podcast Digest with any agent harness

The **portable core** is `SETUP.md` (onboarding), `SPEC.md` (normative workflow), `feeds.json` (sample inputs), and the destination mappings. The optional `SKILL.md` adds an Agent Skills-style entrypoint. None of these requires a particular model vendor.

| Your environment | Recommended path | What's still your responsibility |
|---|---|---|
| Agent with file/web/tool access, but no skill loader | Clone/download this repo; give the assistant `SETUP.md` and `SPEC.md` | Provide permissions, choose feeds/destination, run one-episode smoke test |
| Claude or another Agent Skills-compatible agent | Import the folder using the platform's documented Skill installation route; `SKILL.md` describes the workflow | Enable tools and storage; schedule separately where supported |
| ChatGPT or Codex with Skill support | Import the skill folder/ZIP through the applicable Skill interface; `agents/openai.yaml` is only optional UI metadata | Connect apps/services explicitly; use supported scheduling separately |
| Coding agent reading a cloned repository | Ask it to read `AGENTS.md`, then `SETUP.md` and `SPEC.md` | Provide runtime, credentials/permissions, destination and scheduler |
| No agent automation | Follow `SETUP.md` manually; use the two Python reference helpers when useful | Run the digest, record and delivery steps yourself |

**Compatibility is capability-dependent.** A readable `SKILL.md` does not give an agent network access, file-system writes, transcription, scheduled execution, or external-app permissions. This repository offers a *specification and helper scripts*, not a turnkey hosted application. Platform-specific auto-discovery and ZIP import behavior vary; consult the relevant platform documentation.

## Files with platform-specific meaning

- `SKILL.md`: portable Agent Skills-style Markdown entrypoint, useful where supported; optional if you use `SETUP.md` directly.
- `agents/openai.yaml`: optional OpenAI presentation metadata. It does not change the workflow, and other harnesses can ignore or remove it.
- `AGENTS.md`: lightweight pointer for coding agents that read repo instructions. It does not replace `SETUP.md` or `SPEC.md`.

## Common first prompt

> Read `SETUP.md` and `SPEC.md` in this repository. Help me run a one-episode podcast digest using my chosen RSS feeds. Ask which feeds and destination I want, use only tools available in this environment, and report any unsupported steps explicitly. Do not schedule anything or send messages until I approve.

Keep `.env`, local `config.json`, `transcripts/`, `records/` and `digests/` private. The public repo should include the workflow and examples, **not** user-specific output or third-party copyrighted transcripts.