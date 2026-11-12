# Repository instructions

## Git and collaboration
- Use existing `Notice-Me/notice-me` private repository. Never create a replacement organization/repository.
- The bootstrap commit alone may be pushed to main. All subsequent feature work must use a feature branch.
- Before push, verify remote, branch, staged diff, tests, and absence of secrets. The user authorized bootstrap push and feature PR creation for this task.
- Create a PR after tests; never merge or enable auto-merge without explicit user approval.
- Preserve existing files and the vehicle developer's work. Record API contract changes in `docs/API_CONTRACT.md`.

## Implementation and evidence
- Python 3.11+, FastAPI, SQLite, httpx, pytest; use `.env` for credentials, never log keys or request URLs containing keys.
- Free plans/quotas only. No billing, paid upgrades, unauthorized scraping, or invented external endpoints.
- Official documentation is required before implementing an external provider. Record calls and failures honestly.
- `LIVE`, `MOCK`, `MIXED` describe actual content provenance. Simulated traffic must carry `SIMULATED` verification.
- News without verified AI/TTS redistribution rights must not enter the voice queue or LLM processing.
- Events/exhibitions require verified driving time <= 60 minutes; unknown routing must be excluded with an explicit diagnostic.
- School AI endpoint is unknown: use an LLMProvider interface and deterministic mock until documented settings arrive.
- Write focused behavior tests for recommendation, rights, expiry, provider failures, and API contracts. Run tests before PR.
- Maintain PROJECT_CONTEXT, PROJECT_STATUS, API_CONTRACT, and DATA_SOURCES while implementing.
- Do not commit personal application forms, phone numbers, emails, precise user location histories, or raw third-party article bodies.

## Korean engineering and learning records (user requirement)
- Keep `docs/TECH_DECISIONS.md`, `docs/DEVELOPMENT_LOG.md`, and `docs/LESSONS_LEARNED.md` cumulative and in Korean.
- For meaningful changes, record the actual reason, mechanism, alternatives considered, tradeoffs, problem/cause, attempted fixes, measured tests/evidence, and remaining gaps. Link existing context/status/contract/source docs instead of duplicating them.
- Distinguish user-mandated stack choices, implemented choices, documentation-only comparisons, and experiments actually performed. Never invent benchmarks, provider success, personal learning, AI reviews, or vehicle/TTS validation.
- Update these records alongside the implementation without delaying the MVP for unrelated research. Add dates/evidence when facts change; retain earlier verified observations as history.
