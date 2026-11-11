# Notice Me

현재 위치·경로·목적지·관심사를 바탕으로 뉴스, 행사, 전시, 생활정보를 추천하는 Pleos 차량 앱 프로토타입입니다. 2인 팀의 서버/차량 앱 공동 저장소이며 2026-11-15 핵심 흐름 시연을 목표로 합니다.

## 디렉터리

- `server/`: Python 3.11+, FastAPI, SQLite, httpx, pytest 백엔드
- `vehicle-app/`: 차량 앱 담당자 작업 공간 및 연동 안내
- `docs/PROJECT_CONTEXT.md`: 전체 기획과 운영 규칙
- `docs/API_CONTRACT.md`: 차량 앱과 공유하는 v1 API 계약
- `docs/PROJECT_STATUS.md`: 실제 완료/미완료 상태와 검증 결과
- `docs/DATA_SOURCES.md`: 공식 출처, 인증, 권리, 실제 호출 결과
- `docs/TECH_DECISIONS.md`: 사용 기술의 선택 이유·원리·대안·검증·한계
- `docs/DEVELOPMENT_LOG.md`: 날짜별 작업·문제·실제 시도·테스트·미해결 이력
- `docs/LESSONS_LEARNED.md`: 검증된 경험에서 정리한 학습·회고·발표 근거

초기화 이후 개발은 `feat/server-content-feed` 등 기능 브랜치에서 진행합니다. main에는 기능 코드를 직접 커밋하지 않으며, 테스트 확인 후 PR을 만들고 사용자 승인 전에는 병합하지 않습니다.

## 실행 (Windows PowerShell)

```powershell
cd server
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
.venv\Scripts\python.exe -m pip install -e . --no-deps
Copy-Item .env.example .env  # 최초 1회만; 기존 .env가 있으면 덮어쓰지 마세요
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

기본은 **MOCK**입니다. 키 없이 가상 콘텐츠·규칙·전체 음성 큐·API 연동을 확인할 수 있습니다. API 문서: http://127.0.0.1:8000/docs . 새 PowerShell에서:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/feed?lat=37.57&lon=126.98&interests=art,science,anime&navigation_active=true&route_link_ids=demo-link-1&route_link_namespace=DEMO'
```

## 실제 공공 데이터 사용

`server/`에서 수집 명령을 실행합니다. 서울시 공식 `sample` 키는 개인 가입 없이 실제 공개 데이터 최초 5건과 광화문·덕수궁 도시데이터를 조회합니다. 데이터 수집과 feed 조회는 분리되어 있어 차량 조회마다 외부 API를 소비하지 않습니다.

```powershell
.venv\Scripts\python.exe -m app.cli ingest --report reports/latest-ingest.json
$env:NOTICE_DATA_MODE='live'   # 실제 수집 자료만 사용; 혼합 시 'mixed'
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --port 8001 --no-access-log
```

`interests=weather` 또는 `interests=생활`을 주면 실제 날씨 생활정보를 볼 수 있습니다. 날씨는 원천 갱신시각 후 1시간에 만료되므로 오래된 경우 먼저 재수집하세요. **LIVE 행사 5건은 자동차 이동시간 검증이 없어 추천에서 제외**됩니다. 교통정보는 같은 링크 체계의 실제 경로 입력과 수집 후 10분 이내 조건이 필요합니다. 이동시간을 직선거리로 대체하지 않습니다.

실측 예시/한계: [PROJECT_STATUS](docs/PROJECT_STATUS.md), [실제 호출 결과](docs/API_VALIDATION_RESULTS.json), [HTTP 검증](docs/HTTP_SMOKE_RESULTS.json).

TourAPI 인증 후 현재/예정 행사만 상한을 두고 수집하려면 `app.cli ingest --public-provider tourapi --report reports/tourapi-next.json`을 사용합니다. 기본 KST 오늘~90일,50건/페이지·최대3페이지/3시도입니다. [실제76건 수집과 제외 사유](docs/TOURAPI_INVESTIGATION.md)를 확인하세요. 날짜 유효와 권리/이동시간 자격은 별개이며 LIVE 행사는 실제 이동시간 검증 전까지 추천에서 제외합니다.

## 테스트와 뉴스 키 설정

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\ruff.exe check app tests scripts
.venv\Scripts\ruff.exe format --check app tests scripts
# 뉴스만, 지정 질의만 검사. 재시도 포함 최대2회. 기존 결과는 다른 report 경로로 보존.
.venv\Scripts\python.exe -m app.cli validate-news --provider freenews --keyword '예술' --window-hours 24 --max-requests 2 --report reports/freenews-targeted.json
# FreeNewsAPI metadata/URL 수집. 목록/상세/재시도 전체 최대4회.
.venv\Scripts\python.exe -m app.cli ingest-news --keyword '예술' --max-requests 4 --report reports/freenews-ingest.json
```

API 키는 각 데이터 제공자가 발급하는 접속 비밀값으로 GitHub 인증과 별개입니다. 키가 없어도 Mock과 서울시 sample은 실행됩니다. [발급/설정 안내](docs/SETUP_API_KEYS.md)를 참고하세요. 키·.env·SQLite·원본 기사 본문은 Git에 올리지 않습니다. `validate`는 소량의 실제 요청을 수행하며 인증이 안 된 뉴스는 기사 수/중복률을 미측정으로 남깁니다.

기존 `ingest`/`validate` 전체 수집·비교 명령도 유지합니다. [FreeNews 오류 조사](docs/FREENEWS_INVESTIGATION.md)에 실제0/5/10건의 의미, 재현된500, timeout·재시도·무료 예산·결과 보존을 정리했습니다. 뉴스 키가 있어도 TTS 권리가 생기지 않으며, 현재 FreeNews 뉴스는 화면 metadata만 가능하고 음성/설명은 차단됩니다. feed에서 실자료를 보려면 서버 모드를 live/mixed로 설정해야 합니다.

## 차량 앱 연동

팀원은 [차량 앱 연동 시작 안내](docs/VEHICLE_INTEGRATION.md)와 [Pleos 앱 담당 확인표](docs/VEHICLE_ACCEPTANCE.md)를 먼저 읽으세요. 서버 주소 설정과 실제 HTTP 계약 검사를 순서대로 실행할 수 있습니다. 서버와 에뮬레이터가 다른 PC라면10.0.2.2가 서버 PC를 가리키지 않는 점을 확인하세요. 시연 날씨만 갱신하려면 `app.cli ingest --public-provider seoul_city`를 사용합니다.

[API 계약](docs/API_CONTRACT.md), [OpenAPI JSON](docs/openapi.json), [LIVE 예시](docs/examples/live-feed.json), [MIXED 예시](docs/examples/mixed-feed.json)를 공유하세요. 차량/에뮬레이터 연결 시 서버를 `--host 0.0.0.0`으로 실행하고 개발 PC의 접근 가능한 주소를 사용합니다. 공개 배포·인증·TLS 설정은 이 프로토타입에 포함되지 않습니다. 차량 앱/SDK 구현과 실제 TTS 재생은 아직 팀원 연동 검증이 필요합니다.

`top3`는 화면 카드, `queue`는 TTS 허용 전체 큐, `alerts`는 별도 우선 큐입니다. `playback_order`대로 재생하되 항목의 `tts_eligible`, `data_mode`, `verification_status`를 지키세요. 실제 AI가 없는 현재 설명 응답은 항상 `ai_mode=MOCK`입니다. 서버는 사용자의 위치·경로·질문 이력을 저장하지 않습니다.
