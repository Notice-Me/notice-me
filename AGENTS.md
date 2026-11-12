# Repository instructions

## GitHub 협업 규칙

1. 작업을 시작하기 전에 `git fetch origin`으로 기존 비공개 저장소 `Notice-Me/notice-me`의 원격 상태를 갱신합니다. 저장소나 조직을 새로 만들지 않습니다.
2. 최신 `origin/main`에서 작업 목적에 맞는 새 기능 브랜치를 만듭니다.
3. 서버 기능은 `feat/server-*`, 차량 앱 기능은 `feat/vehicle-*`로 이름을 정합니다. 공통 작업은 범위가 드러나는 이름을 사용합니다.
4. 기존 팀원 브랜치와 열린 PR이 있으면 커밋과 변경 내역을 확인합니다. 작업을 중복하거나 다른 팀원의 변경을 덮어쓰지 않습니다. API 계약 변경은 `docs/API_CONTRACT.md`에 기록합니다.
5. 변경 후 관련 테스트를 실행하고 통과 결과와 미검증 항목을 구분합니다. 문서만 바뀌면 문서 검사를 수행하고 실행하지 않은 테스트를 명시합니다.
6. 원격 저장소, 작업 브랜치, 커밋할 변경 범위, 테스트 결과, 비밀값 포함 여부를 확인합니다. 기능 브랜치에 커밋하고 푸시한 뒤 `main`을 대상으로 PR을 엽니다.
7. PR 설명에는 변경 이유, 주요 수정 사항, 테스트 결과, 남은 문제를 기록합니다.
8. PR을 열면 팀원 검토를 기다립니다. 사용자가 해당 PR의 병합을 명시적으로 승인하기 전에는 병합하거나 자동 병합을 설정하지 않습니다.
9. `main`에 직접 푸시하거나 force push를 하지 않습니다. 팀원 브랜치를 포함해 브랜치를 임의로 삭제하지 않습니다.
10. 기존 `.env`, 인증키, DB, 개인 설정 파일은 유지합니다. 해당 파일이나 비밀값을 커밋하거나 GitHub에 업로드하지 않습니다.

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
