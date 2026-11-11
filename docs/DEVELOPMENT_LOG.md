# 개발 기록

날짜는 KST 기준입니다. 실제 수행한 작업·관측·검증 결과를 누적합니다. 기술 원리는 [TECH_DECISIONS](TECH_DECISIONS.md), 최신 완료/미완료와 일정은 [PROJECT_STATUS](PROJECT_STATUS.md), 학습 정리는 [LESSONS_LEARNED](LESSONS_LEARNED.md)로 연결합니다. 이력에 적힌 결과는 해당 시각의 결과이며 현재 제공자 상태를 보증하지 않습니다.

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

## 미해결 항목과 다음 기록

최우선은 팀원 기기의 health→feed→TTS 실제 연결 증거. FreeNews 인증/일부 metadata 수집은 확인했지만 애니메이션500·전체 pagination·뉴스 가공/재배포 권리는 남아 있음. 자동 수집 스케줄러, 자동차 이동시간·지도 링크 매핑, 학교 AI, ITS, 운영 인증/TLS 및 부하 검증도 남아 있음. 최신 우선순위와 담당/완료 기준은 [PROJECT_STATUS](PROJECT_STATUS.md#1115-mvp-우선순위와-완료-기준)를 유지함.

다음 작업은 날짜, 목적, 관측한 문제/원인, 수행한 시도, 결과/테스트 명령·파일·커밋, 미해결 문제만 짧게 추가한다. 아직 하지 않은 조치는 계획이라고 표시한다. 비밀값·개인 위치/경로·신청서 개인정보는 기록하지 않는다.
