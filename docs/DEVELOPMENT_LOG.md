# 개발 기록

## 2026-11-13 — 서버 관심사 P0·공식 팝업·라우팅 조사

fetch --prune 후 main94de875 및 전체 원격 브랜치/PR을 확인했다. main에 서버 PR #6·차량 PR #7이 병합됐고 차량 PR #8은 열려 있었다. 새 feat/server-interest-content에서 서버/문서만 수정했다. 미공개 UI 작업을 추정하지 않고 Kotlin/vehicle-app 변경0을 확인했다. [구현 전 계약 검토](INTEREST_CONTRACT_REVIEW.md) 후 관심사 모듈·뉴스 분류·추천·행사 중복을 수정했다.

문제/해결: 공유 venv의 editable 설치가 다른 checkout을 가리켜 처음 pytest 수집2오류가 났다. PYTHONPATH를 현재 server로 지정해 해결했다. 행사 중복 분기를 삽입할 때 기존 뉴스 제목 중복 검사가 잘못 이동하여 기존 테스트1실패/158통과를 관측했다. 기존 테스트를 바꾸지 않고 분기를 복원한 뒤159통과, 새 행동 검증31개를 더해190통과했다. 한영일16조합·팝업 오탐·검색어 오염·권리/날씨/라우팅·중복·HTTP를 검증했다. 일본어 결과 출력에서cp949 오류가 있었으나 JSON 파일은 저장/검증 완료 상태였고 최종 HTTP 검사는 UTF-8 출력을 사용했다.

최종 pytest190/0실패, 기존 Starlette/httpx 경고1. Ruff check/format·pip check 통과. 원본과 별도 SQLite backup 사본으로97LIVE행/치이카와제목0 확인. 01:48 KST Uvicorn LIVE3/1/0, MOCK 모의경로3/5/1, health→feed→detail→explain200, 뉴스2건 음성false/403,404/422/타입 명세 확인. 01:00 날씨는02:00에 만료되므로 이 결과는 측정 시각에 한정한다. 현재 위치·목적지 이력을 저장하지 않았다. 원본.env/DB/개인 local.properties는 SHA256동일3개, vehicle-app diff0. 기존8000 서버와 에뮬레이터는 조작하지 않고 별도 검증 서버를 사용했다. [측정 JSON](verification/2026-11-13-server-interest.json).

외부 콘텐츠/라우팅 API 호출0, 새 실제 행사0. 공식 사업 소개는 현재 개최 증거가 부족해 후보로만 남겼다. 카카오/TMAP의 무료 한도와 인터페이스 연결 조건·수동 취소 격리 미구현을 [후속 조사](POPUP_ROUTING_RESEARCH.md)에 분리했다. 실제 Pleos/TTS·Kotlin 빌드·길찾기·학교 AI는 이번에 검증하지 않았다. 사용자 직접 수행은 요구/우선순위 지정이며 코드·테스트/문서 조사는 Codex가 수행했다. 새 AI 교차검증이나 사용자 숙련도 향상을 만들어 기록하지 않는다.

## 2026-11-13 — 실제 날씨 서버 P0

git fetch/prune 후 팀원 내비 PR #4가 main에 이미 병합됨을 확인했다. 최신 main에서 feat/server-live-weather-policy를 생성했다. 날씨 관측 모델, LIVE 날씨 전용 음성 정책, 현재 위치보다 목적지/제공된 경로 우선 점수, 한국어 날씨 alias, OpenAPI를 보강했다. 원본 DB backup 사본에서 seoul_city1회 HTTP200·00:00 관측11.5도/01:00만료. LIVE3/1/0, MOCK 모의경로3/5/1 실제HTTP 통과. 초기4실패/155통과 원인과 수정, 최종검증·미실행·무료 호출량은 [상세 기록](LIVE_WEATHER_DEMO.md). 원본 .env/DB/팀원 코드는 덮어쓰지 않았다. 기기 증거는 서버 HTTP 성공과 구분한다.

날짜는 KST 기준입니다. 실제 수행한 작업·관측·검증 결과를 누적합니다. 기술 원리는 [TECH_DECISIONS](TECH_DECISIONS.md), 최신 완료/미완료와 일정은 [PROJECT_STATUS](PROJECT_STATUS.md), 학습 정리는 [LESSONS_LEARNED](LESSONS_LEARNED.md)로 연결합니다. 이력에 적힌 결과는 해당 시각의 결과이며 현재 제공자 상태를 보증하지 않습니다.

## 2026-11-13 — 관심사 후속 설계·실제 콘텐츠 확보 시도

fetch/prune와 GitHub API로 main94de875, PR #8/84cad04·#9/7c73072 OPEN/미병합 및 변경 파일을 확인했다. clean 상태에서 최신 origin/main 기반 feat/server-profile-content-plan 생성. #9를 병합/중복 구현하지 않고 프로필 OR·상세 검색 AND 계약을 먼저 제안했다. 차량 UI/Kotlin과 server 실행 코드는 수정하지 않았다. [변경안](INTEREST_PROFILE_PROPOSAL.md).

실제 조사: 대원미디어가 팝콘D플레이 운영 주체임을 공식 공지로 확인하고 무민 잠실 진행·치이카와 클리닉 예정 공지를 찾았다. 주소/좌표/개별 운영사·권리/변경 확인 부족으로 수동 등록0. 서울문화포털 상세는 timeout이 반복되어 원문 확인 성공으로 기록하지 않았다. 대체 공식 예매 공지에는 시간 충돌이 있어 보류했다. 기존 수집기를 sample/재시도0/총예산2로 실행해 문화행사 HTTP200/INFO-000/5건과 날씨1건 수신. 별도 SQLite backup 사본에만 저장했고98LIVE행이 됐다. 수신 행사 중 새ID1개, 나머지는 재확인이다. [출처·누락·측정](CONTENT_SOURCE_FOLLOWUP.md).

실행한 검증: current main PYTHONPATH를 고정해 pytest159 통과. PR #9를 git archive로 분리한 소스 사본에서도190 통과(각 기존 Starlette/httpx 경고1). main Ruff/check/format37개/pip check 통과. 별도18084/18085 Uvicorn에서13:49 LIVE3/1/0·MOCK모의경로3/5/1,health/feed/detail/explain200·뉴스2건403·404/422·명세 확인. 공공행사5건 상세200/tts=false,feed 제외·DRIVING_TIME_UNVERIFIED, 제안 POST404 확인. #9 matcher에서는 실제 지브리 메타데이터의 anime=true/혼합 취향=false를 재현했으며 새 OR 기능 통과로 기록하지 않았다. [증거 JSON](verification/2026-11-13-profile-content.json).

관측값 기반 한계: 날씨13:40/14:40만료,고정 POI009이며 원본/실행 중 앱 서버는 갱신하지 않았다. 콘텐츠 총2회 외 뉴스/Tour/라우팅0, 새로운 계정 인증/키/결제 없음. 세 개인 파일 hash 보존과 vehicle-app/server diff0을 확인한다. 새 기능/API·실제 팝업 추천·실제 경로·학교 AI·Pleos/TTS/Kotlin 실행은 이번 미구현/미검증이다. 사용자 요구/우선순위와 Codex의 조사·테스트 수행을 구분하며 팀원 합의·개인 학습 성과·AI 교차검증을 만들어 기록하지 않는다.

## 2026-11-11 — 초기 구현 기록 확인

**기록의 성격:** 기존 Git 커밋과 저장된 보고서로 확인한 초기 작업입니다. 당시의 모든 시도를 이번 회차에 다시 실행한 것은 아닙니다.

- 기존 private 저장소를 사용한 초기화 커밋: 7346168. 기본 디렉터리/컨텍스트/계약을 main에 반영.
- 서버 최초 기능 커밋: d8f5c96. FastAPI 4개 endpoint, SQLite, 추천/권리 검사, 수집기, 테스트, 문서와 PR #1.
- 당시 보고: pytest49, 서울 문화행사5/날씨1/교통4, 실제 Uvicorn HTTP 성공. [초기 실제 API 기록](API_VALIDATION_RESULTS.json), [초기 HTTP 기록](HTTP_SMOKE_RESULTS.json).
- 남은 조건: 뉴스/TourAPI 인증, 실제 이동시간/학교 AI/차량 경로·TTS 등은 미완료로 기록되어 있었음.

## 2026-11-11 — 현재 환경에서 기준 상태 재검증

**목적:** 11/15 MVP 연동 전에 과거 보고와 현재 상태를 구분하고, 기존 기능을 재작성하지 않고 필요한 결함을 찾음.

**수행:** 지정된 PROJECT_CONTEXT/STATUS/API_CONTRACT/DATA_SOURCES와 PR #1의 변경/테스트를 조회. 작업 브랜치·원격·head 일치를 확인. 이번에는 연결 도구의 PR 조회와 GitHub CLI 조회가 모두 성공했음. PR은 OPEN, mergedAt/autoMerge는 없음. 개인 키 값은 출력하지 않음.

**재실행:** Python3.11.9에서 pytest49 통과, Ruff check/format, pip check 통과. 외부 제공자 테스트는 MockTransport라는 점을 확인함. 뉴스3종/TourAPI/ITS 키는 설정되지 않았고 서울 키는 sample임을 값 없는 설정 상태로 확인.

**실제 수집:** 18시대 KST에 기존 ingest CLI로 서울 행사5·날씨1·교통5 수신/정규화, 각 HTTP200. TourAPI는 MISSING_KEY로 정상 수신을 검증하지 못함. 뉴스 무인증 호출을 이번에 반복하지 않았고 실제 뉴스 검색/기사 수/중복률을 측정하지 않음. 갱신은 기존 SQLite에 upsert했으며 이전 자료를 무단 삭제하지 않았음.

**근거:** [재검증 JSON](verification/2026-11-11-revalidation.json). 초기의 교통4와 현재 sample5는 다른 시각의 수신 결과임. 데이터는 정적 fixture가 아니므로 동일 개수를 보장하지 않음. 원천 이용조건 전문 전체를 새로 검토한 회차는 아니며 뉴스 권리 차단은 그대로 유지.

## 2026-11-11 — feed/detail/explain의 유효성 불일치 수정

**문제와 원인:** 수집 후11분이지만 종료예정은 아직 남은 교통정보를 만들었을 때 feed alerts=0, detail tts_eligible=true, explain HTTP200이었음. feed에 있던 교통 freshness/상태 검사가 다른 두 endpoint에는 없었기 때문임. 유효기간이 남아 있다는 사실만으로 현재 재생 가능한 교통정보라고 판단할 수 없었음.

**실제로 시도한 해결 순서:**

1. 임시 DB와 TestClient에서 문제를 재현. 실제 교통 통제 상황이라고 주장하는 대신 자체 fixture로 조건을 고정함.
2. [유효성 회귀 테스트](../server/tests/test_content_availability.py)10개를 먼저 추가. 수정 전 결과는 **6 failed / 4 passed**. 오래됨·해제·통제 종료·미래 발생·통제 필드 누락·미래 발행에서 불일치를 확인.
3. [availability.py](../server/app/availability.py)의 공통 함수를 feed/detail/explain에 적용. 상세 조회 자체는 유지하면서 tts_eligible=false, 설명409로 처리. 뉴스 권리 미확인403 유지.
4. 기존49+신규10, **59 passed**. 수집 후정확히10분의 경계와 11분 조건도 검사.

**변경 근거:** 커밋 fdd7e2f, [API 계약의 유효성 변경](API_CONTRACT.md), 위 회귀 테스트. 초기 실패 stdout을 별도 파일로 보관한 것은 아니며, 이 세션에서 실행한 결과와 재현 조건을 기록함. 최종 JUnit은 로컬 server/reports에, 집계는 재검증 JSON에 보존.

**남은 범위:** 공통 유효성 검사는 실차 경로 관련성이나 자동차 이동시간 검사를 대체하지 않음. 실제 라우팅/학교 AI는 연결하지 않음. 결정 이유는 [TD-04](TECH_DECISIONS.md#td-04-설명-가능한-규칙과-단일-유효성-기준).

## 2026-11-11 — 차량 앱 계약과 실행 검사 보강

**발견:** 기존 health/detail은 정상 JSON을 반환했지만 OpenAPI의 성공 응답 schema는 `{}`였음. 앱 담당자가 명세만으로 해당 응답 모델을 확인하기 어려웠음.

**수행:** HealthResponse/ContentDetail을 명시하고 top3의 maxItems=3을 schema에 추가. 기존 URL·요청·JSON 필드 유지. 네 응답 모델과 기록된 OpenAPI 일치 테스트2개를 추가해 **61 passed**. 키/외부 통신 없이 명세를 내보내는 [export_openapi.py](../server/scripts/export_openapi.py)를 작성함.

**연결 도구:** [check_vehicle_api.py](../server/scripts/check_vehicle_api.py)는 서버 DB/.env를 읽지 않고 HTTP로 health/feed/detail/explain, 오류403/404/422, 권리/기한/모드/schema를 검사. 실제 앱 연결 여부나 TTS 재생은 판단하지 않음. 잘못된 기대 모드/빈 LIVE 응답을 성공으로 오인하지 않는 테스트3개 포함, 최종 **64 passed**.

**실제 Uvicorn HTTP 관측:**

응답 계약/연결 도구 변경: 커밋 00104b0. 테스트는 해당 커밋 전의 최종 작업 트리에서 실행했고, 이후에는 기술·학습 문서만 추가했습니다.

| 시나리오 | 화면 / 일반큐 / alerts | 구분 |
|---|---|---|
| LIVE, 내비 미사용 | 1 / 1 / 0 | 실제 공공 날씨, 실제 뉴스 성공을 뜻하지 않음 |
| MOCK, 수동 DEMO 경로 | 3 / 5 / 1 | 모두 MOCK, 교통 SIMULATED |
| MIXED, 수동 DEMO 경로 | 3 / 6 / 1 | 실자료+fixture, 교통 SIMULATED |
| LIVE, 수동 SEOUL_TOPIS 링크 | alert1 | LINK_MATCH 확인. 실차 내비에서 받은 경로가 아님 |

모든 시나리오의 설명 ai_mode는 MOCK. 실제 차량/에뮬레이터 앱 실행·오디오 재생은 수행하지 않았음. [실측 집계](verification/2026-11-11-revalidation.json), [팀원 실행 안내](VEHICLE_INTEGRATION.md), [복사할 요청](examples/vehicle-api.http). 기술 이유는 [TD-01/TD-05](TECH_DECISIONS.md).

## 2026-11-11 — 기술 근거·학습 기록 추가

**사용자 요구:** 발표/면접/회고에 쓰기 위해 선택 이유, 문제/시도/검증, 학습 내용을 사실 기반으로 누적.

**수행:** 이 문서와 TECH_DECISIONS/LESSONS_LEARNED를 한국어로 작성. Python/FastAPI/SQLite 등 사용자 지정 조건과 구현자가 선택한 httpx/직접 SQL/공통 검사 등을 구분함. SQLite·HTTPX/Requests·Pydantic·pytest·Protocol 등의 공식 문서를 읽어 원리를 설명했으나 PostgreSQL/다른 프레임워크 성능 실험은 수행하지 않았다고 명시. 실제 설치한 기술과 문서상 대안을 구분함. AGENTS에 이후의 누적 기록 지침 추가.

**영향:** 문서 추가로 서버 기능이나 데이터 이용권한을 확대하지 않음. 새 코드가 없으므로 문서만을 위한 중복 기능 테스트는 추가하지 않고 링크·비밀정보·변경 파일을 점검. Gemini/Claude 교차검증은 사용자 계획이며 아직 수행 결과가 없음.

## 2026-11-11 — FreeNewsAPI 인증 후 오류 조사/성공 자료 보존

**입력:** 사용자가 로컬 .env에 키를 설정한 뒤 reports/validation.json을 생성. API 키 로딩 true를 값 출력 없이 재확인했습니다. 기존 사용자 보고서를 덮어쓰지 않았습니다.

**관측과 원인 구분:** 원본에서 과학 IT24h는 SUCCESS지만0건, 예술24h는5건, 예술168h는10건/has_more=true였습니다. 전체 found는 미제공입니다. 공식 OpenAPI를 현재 NewsProvider와 비교해 형식 차이는 발견하지 못했습니다. 같은 window로 목록3회만 추가 호출하여 애니메이션24h500, 예술24h200/5건, 과학 IT168h200/0건(약10.844초)을 관측. 500 응답은 Internal Server Error뿐이어서 내부 원인은 미확정입니다. 과거 TIMEOUT의 단계도 기록되지 않아 사후 원인을 확정하지 않았습니다.

**실제 변경:** 제한적 재시도/단계별 timeout/시도당 deadline/백오프/호출 예산을 추가했습니다. 500/인증/429는 반복하지 않습니다. 검색별 metadata와 오류를 news_searches에 append하고 JSON checkpoint를 저장하며, 상세 실패가 정상 기사를 버리지 않도록 했습니다. validate-news/ingest-news로 무관한 API 호출을 피합니다. 기존 coverage_note가 인증 성공 상황에도 키 없는 설명을 쓰던 문제도 수정했습니다. API v1/뉴스 권리 정책은 유지했습니다.

**실수집 확인:** 목록 재조회 없이 받아 둔 예술5건 metadata를 보존하고2건만 details 호출/정규화/SQLite 저장. 이번 총 추가 호출5회, 마지막 응답 일일 잔여4,988. 두 LIVE 뉴스는 LICENSE_UNVERIFIED로 ASGI TestClient의 화면에는 표시되지만 음성 큐0건, 설명403/403입니다. 본문/설명문을 저장·LLM 전달하지 않았습니다. 실차/TTS 실행은 하지 않았습니다.

**검증:** 기존64→최종99 passed, Ruff/format/pip check/compileall 통과. timeout 단계, 제한된 재시도/백오프, 반복하지 않는500/인증/429, 호출 예산, 잘못된 schema, 후속 검색/상세 실패·처리 중단 뒤 DB/JSON 보존, 뉴스 전용 CLI 등을 MockTransport로 확인. 상위 TestClient 경고1건 유지. [증거 JSON](verification/2026-11-11-freenews-investigation.json), [조사/재현 명령](FREENEWS_INVESTIGATION.md), [TD-09](TECH_DECISIONS.md#td-09-뉴스-실패-격리와-소량-재시도-2026-11-11-추가).

**남은 문제:** 애니메이션500의 제공자 내부 원인, 정확한168h 전체/고유 기사 수, 뉴스 TTS/AI 권리. 이번 결과를500 해결이나 전체 뉴스 검색 안정성 검증으로 표현하지 않습니다.

## 2026-11-11 — Pleos 연동 준비 우선 전환 (20시대 KST)

**요구/현재 상태:** 사용자에게 첫 환경이 Pleos SDK 에뮬레이터·실차임을 확인했습니다. feature5626e46, 기존 pytest99를 재검증했고 원격 PR은 OPEN/미병합이었습니다. API/기존 인계 도구를 재사용했습니다. 새 앱 코드나 SDK 실행 결과는 없습니다.

**문제/수정:** HTTP 검사 도구가 playback_order의 일부 포함만 검사하고 alerts의 권리 근거를 직접 검사하지 않던 한계를 보강했습니다. 전체 재생 순서·권리·교통 freshness와 LIVE 권리 미확인 뉴스의 상세 false/설명403을 검사합니다. 보고서에 서버 HTTP 한정/SDK·TTS 미검증 값을 추가했습니다. 기존 API JSON은 변경하지 않았습니다. 선택 수집 옵션 --public-provider seoul_city로 시연 날씨만 갱신할 수 있게 했습니다.

**실제 데이터/HTTP:** 서울시 sample 도시데이터만1회 호출해200/날씨1건을 저장했고 원천 기준 만료는2026-11-11T11:50Z였습니다. FreeNews 추가 호출0회. 실제 수집 DB의 백업과 시작 fixture로 Uvicorn을 실행해 MOCK3/5/0, LIVE3/1/0, MIXED3/6/0(화면/큐/alerts), DEMO 입력 MOCK/MIXED alert1을 확인했습니다. LIVE 뉴스2건은 상세 음성 자격 false/설명403입니다. localhost TCP와 서버 PC 자신의 LAN 주소 health200은 확인했으나 다른 기기의 접속 증거는 없습니다. 검증 서버는 종료했습니다. [측정](verification/2026-11-11-vehicle-handoff.json).

**발생한 문제/해결:** 추가 테스트가 TOP3에 권리 미확인 뉴스가 항상 있을 것이라고 가정해1 failed/109 passed가 나왔습니다. 실제 순위는 관심사/점수에 따라 달라지므로 검사하려는 잘못된 응답을 명시적으로 구성하도록 테스트를 수정했습니다. 별도 HTTP 보조 검증은 Windows의 임시 DB 정리에서 WinError32로 두 차례 종료 실패했습니다. 잠금의 내부 원인은 확정하지 않았고 검사 DB를 Git 제외 reports에 보존하여 최종 HTTP 보고서를 생성했습니다. 외부 제공자를 반복 호출하지 않았습니다.

**최종 검증/인계:** pytest110 passed(기존99+신규11), Ruff/format/pip check/compileall 통과, 기존 TestClient 경고1건. OpenAPI paths/components 일치. 접속 주소·PC→앱 단계 구분·권리/오류 처리·Pleos 공식 SDK 권한/TTS 모드 문서를 검토해 [연동 안내](VEHICLE_INTEGRATION.md)와 [미실행 확인표](VEHICLE_ACCEPTANCE.md)를 갱신했습니다. PROJECT_STATUS/CONTEXT의 FreeNews 미인증 표현을 현재와 초기 이력으로 분리했습니다. 기술 이유는 [TD-10](TECH_DECISIONS.md#td-10-서버-http-준비와-pleos-기기tts-완료를-따로-판정-2026-11-11).

**미완료:** 팀원 앱 HTTP 호출/DTO·화면·TTS SDK 초기화/실제 음성·오디오 포커스·실차 UX. 원격 접속 주소/서버 상시 실행, 자동 갱신·외부 배포/인증/TLS도 아직 없습니다. 이번 결과를 Pleos 연동 완료로 표시하지 않습니다.

## 2026-11-11 — TourAPI 현재/예정 행사 실수집 (23시대 KST)

사용자가 발급한 키로 성공한 원본268/10/2/유효0 보고서를 확인했습니다. 원본 raw 행은 저장되지 않아 같은 요청을1회 재조회했고 total268과 정규화2개 id가 일치했습니다. 기본값 선택안함8건을 비어 있지 않다는 이유로 버렸고 그중 예정2건이 있었습니다. 공식 Swagger와 허용된 매뉴얼 다운로드 절차(추가 CAPTCHA 없음)로 국문v4.4의 기본값을 확인했습니다. 원본 보고서/키 값은 수정·출력하지 않았습니다.

KST 오늘~90일, 수정일순C, 페이지50/상한3/시도예산3을 구현했습니다. 행별 제외·주의 사유, 페이지별 DB commit/관측, 후속 오류/중단 보존, 기존 취소 항목 격리를 추가했습니다. 첫 실수집은50+27건 뒤 응답 numOfRows=27을 간격으로 잘못 사용해3페이지 SCHEMA_MISMATCH/PARTIAL이 됐습니다. 누적 건수로 종료하도록 고치고 회귀 테스트 후 실제2회 상한으로 재검증했습니다.

최종200/SUCCESS, raw/total77, 날짜 유효76(진행 중36/예정40), 미확인 온라인1건 보류.76건 모두 Type3라 brief 비움/권리 미확인을 유지했습니다. 원천 HTTP→SQLite 후 내부 ASGI에서 LIVE 행사 노출0/이동시간 미검증 진단, 표본 상세200·TTS false·설명403을 확인했습니다. ASGI를 실제 차량/오디오 검증으로 기록하지 않았습니다. 전체 데이터 호출6회이며 FreeNews/다른 제공자0회, 재시도0회입니다.

최종 pytest147 passed(기존110+신규37), Ruff/format/pip check/compileall 통과, 기존 TestClient 경고1건. 실제 호출 이후 숫자0 상태의 방어 분기를 보강했고 mock 테스트로 검증해 네트워크 반복을 줄였습니다. [측정/실패/개별 제외](TOURAPI_INVESTIGATION.md), [기술 이유](TECH_DECISIONS.md). 남은 것은 미확인 상태1건, 행사별 홈페이지/세부분류, 실제 라우팅/권리·앱 연결, 자동 갱신/전역 할당량 관리입니다.

## 미해결 항목과 다음 기록

최우선은 팀원 기기의 health→feed→TTS 실제 연결 증거. FreeNews 인증/일부 metadata 수집은 확인했지만 애니메이션500·전체 pagination·뉴스 가공/재배포 권리는 남아 있음. 자동 수집 스케줄러, 자동차 이동시간·지도 링크 매핑, 학교 AI, ITS, 운영 인증/TLS 및 부하 검증도 남아 있음. 최신 우선순위와 담당/완료 기준은 [PROJECT_STATUS](PROJECT_STATUS.md#1115-mvp-우선순위와-완료-기준)를 유지함.

다음 작업은 날짜, 목적, 관측한 문제/원인, 수행한 시도, 결과/테스트 명령·파일·커밋, 미해결 문제만 짧게 추가한다. 아직 하지 않은 조치는 계획이라고 표시한다. 비밀값·개인 위치/경로·신청서 개인정보는 기록하지 않는다.

## 2026-11-11 — 차량 앱 최초 구현

- 빈 `vehicle-app` 확인 후 `codex/vehicle-feed-tts`에서 Android 프로젝트 생성. 서버 소스/계약 변경 없이 health/feed/TOP3, 출처·모드·diagnostics, 음성 큐/재생 제어 구현.
- Pleos 공식 SDK 3.3.1 다운로드/메서드 검사 후 ON_DEVICE 어댑터 구현. 일반 Android 어댑터는 별도 flavor로 구분.
- 최초 빌드에서 임시 debug keystore 경로 지정 때문에 서명 파일 부재로 실패. 사용자 홈 변경 대신 검증 환경의 ANDROID_USER_HOME을 작업 폴더로 지정하고 프로젝트는 표준 debug 서명 생성 방식으로 복원. 두 APK 빌드 성공.
- 앱 테스트 18개 + 실제 로컬 MOCK 서버 HTTP 통합 1개 통과. 서버 회귀 테스트 110개 통과. 두 flavor Lint 오류 0(경고 있음).
- 일반 AVD 실행은 프로세스 SIGILL/132로 실패. 앱 설치/화면/TTS 실행 증거를 만들지 못했으므로 NOT_RUN으로 기록. 기존 사용자 AVD는 수정하지 않음.
- 결과/한계/재현 명령: [검증](verification/2026-11-11-vehicle-app.md), [앱 README](../vehicle-app/README.md). 서버 주소와 Pleos 런타임에서의 인수 검증이 남음.

## 2026-11-12 — 차량 앱 0.2.0 화면 정리

- 최신 서버 커밋 `887237f`를 포함한 앱 브랜치에서 빌드했습니다. 추천을 출처·제목·설명 순서의 단일 목록으로 바꾸고 구분선으로 항목을 나눴습니다. 오프화이트, 차콜, 올리브색을 사용하며 서버 설정은 접힌 상태로 시작합니다.
- 시연 자료, 우선 안내와 읽기 전용 표시는 유지했습니다. 설명 없는 실제 뉴스는 제목과 출처를 표시합니다. 앱에서 사용하는 서버 API 계약과 음성 자격 검사 방식은 유지했습니다.
- Pleos 및 일반 Android debug APK 빌드와 Lint, 로컬 MOCK 서버 통합을 포함한 앱 테스트 19개를 완료했습니다. 연결된 에뮬레이터나 기기가 없어 새 화면의 실제 렌더링과 음성 출력은 미검증입니다.


## 2026-11-12 — Pleos 내비 위치 연동

- NaviHelper 3.0.5의 현재 위치와 경로 상태를 새로고침 때 조회합니다. 경로 안내 중인 경우 목적지 좌표를 기존 feed 계약으로 전달합니다. 현재 위치를 받지 못하면 설정 좌표로 연결하고 화면에 표시합니다.
- Pleos 및 일반 Android debug APK 빌드 성공. 앱 테스트 19개 통과, 별도 서버를 쓰는 선택 테스트 1개 제외. Pleos Connect v2.1.0에서 현재 위치의 지역명과 MOCK 추천 3건을 오른쪽 분할 창에서 확인했습니다. 활성 경로에서 목적지 조회는 미검증입니다.

## 2026-11-12 — 내비 도착 시간 기반 음성 큐

- NaviHelper의 목적지 잔여 시간을 초에서 분으로 변환해 기존 feed의 `eta_minutes`에 보냅니다. 화면이 열려 있을 때 15초마다 대기 상태의 큐를 갱신하고 각 재생 후보 조회 직전에도 다시 읽습니다.
- Pleos 0.3.1의 오른쪽 분할 화면에서 안내 중인 목적지와 내비의 25분, 앱의 약 25분 및 음성 큐 5건을 함께 확인했습니다. 앱 프로세스의 반복 목적지 콜백도 확인했습니다.
- 동일한 로컬 MOCK 피드에서 25분/1분/30초에 일반 음성 큐 5/2/0건, 화면 추천은 각각 3건을 확인했습니다. APK 빌드와 실제 로컬 HTTP를 포함한 앱 테스트 20개 통과. 전체 음성 재생 시간과 실차 도착 시점은 미측정입니다.

## 2026-11-13 — 차량 실제 날씨·내비 문맥 인수

- fetch 후 팀원 PR #4 반영을 확인했고, 중간에 협업 규칙 PR #5가 반영돼 앱 브랜치는 최신 main5664368에서 만들었다. 서버는 별도 PR #6이며 병합하지 않았다.
- 0.3.3에 고정 날씨 지역/시각/원문 링크/진단·LIVE 날씨 음성 방어·idle 실패 초기화·내비 콜백/경로 상태 검사를 추가했다. 기존 TTS/오디오·TOP3/queue/playback_order를 유지했다.
- 실제 Pleos에서 LIVE 날씨11.5도 brief 전달 일치와 사용자 청취, 현재 위치·목적지/ETA 전달, 만료/서버 단절 신규TTS0, MOCK 제어를 확인했다. 두 APK/각26개 테스트와 소스 사본 Lint0오류.
- 환경 검은 화면은 AVD 삭제 없이 보이는 창 cold start로 회복. 별도 instrumentation의 목적지 생성은 NAVI_ROUTE_SEARCH 부재로 실패해 권한을 추가하지 않았다. 사용자가 기본 내비에서 안내를 시작한 뒤 SDK ROUTE_GUIDING과 앱 feed의 목적지/ETA를 확인했다.
- 사본 DB만 변경·복원했고 키/개인 위치/목적지·단말 로그를 커밋하지 않는다. 실제 수집은 seoul_city1회, 다른 콘텐츠 제공자0회. 내비 내부 검색/경로 서비스 호출량은 계측하지 않았다. 근거·남은 한계: [2026-11-13 기기 검증](verification/2026-11-13-live-weather-vehicle.md).


2026-11-13 최종 보완: 원격 main에 외부 병합된 UI PR #7(94de875)을 기능 브랜치에 반영하고 두 충돌을 해결했다. 팀원 레이아웃과 날씨·권리 방어를 보존했으며 두 APK/각26테스트·Lint0오류·실제 기기 재생 제어와 brief 일치를 재검증했다. MOCK 테스트 URL 오지정 실패와 수정도 [최종 인수 기록](verification/2026-11-13-live-weather-vehicle.md)에 남겼다. main/타인 브랜치 push·force push·PR 병합은 수행하지 않았다.

2026-11-13 01:03 최종 수동 갱신: 검증 중 첫00:00 관측이 실제01:00에 만료돼01:02 LIVE2/0을 확인했다. 검토 가능한 상태를 남기려고 seoul_city만1회 더 호출해01:00 관측10.8도/02:00만료를 시연 DB 사본에 저장했다. 총 콘텐츠 호출은 서울시2회, 뉴스/Tour0회다. 최신 brief/Pleos doSpeak 일치와 onDone·큐1을 재확인했다. 초기1회라는 앞의 기록은 해당 검증 시점의 이력이다. 15초 feed에서 수집하지 않았고 자동 수집은 추가하지 않았다. 원본 DB/.env는 그대로다.

## 2026-11-15 · Pleos 화면 개편

추천 목록, 설정, 연결 상태, 하단 플레이어의 스타일을 맞췄다. Pleos 디버그 빌드 성공, Standard 테스트 25개 통과 및 1개 건너뜀. 에뮬레이터의 기본 호스트 주소에서 연결에 실패해 포트 역방향 연결을 설정한 뒤 로컬 MOCK 서버의 소식 3건과 고정 플레이어를 분할 화면에서 확인했다. 실제 차량 및 음성 출력은 이번 변경에서 검증하지 않았다.

## 2026-11-15 최종 접수본 통합 및 공개 전 감사

origin/main09b106b와 PR1~18을 갱신·확인한 뒤 독립 브랜치에 PR16 UI와 PR17 release설정/동일APK를 선별 통합했다. PR14의 유효 제출 안내를 반영했고 PR15APK/PR18compact/PR11자동화는 포함하지 않았다. 기존main·팀원worktree·개인파일·원본키/AVD는 보호했다.

새venv/별도DB로 README를 재현하고 pytest190·Ruff·format38·pipcheck를 실행했다. 두release빌드/각26테스트/ReleaseLint오류0, 기존서명·hash·설치와 실제TOP3/음성큐/4제어/ON_DEVICE brief대조/onDone/사용자 한국어 청취를 재확인했다. 시스템창바로 내비가운데·앱오른쪽을 확인했다. 이번서버만 정지해 카드제거/재생불가·복구를 검증했다. 원천API/라우팅/외부AI 호출0.

공식portable Gitleaks 전체이력+전blob/3APK/18PR 검사,13PNG검토, 작성자이메일 노출/동의 확인과 의존성70개 고지를 진행했다. 스캐너경고2건은 검증hash로 분류했다. 문서·안전한JSON·MOCK스크린샷만 추가하며 raw로그·키·DB·신청서는 제외했다. Public/mainmerge/메일은 수행하지 않았다. 상세 문제·한계와 근거는 [최종보고](FINAL_SUBMISSION_2026-11-15.md), [감사](PUBLICATION_AUDIT_2026-11-15.md).
