# FreeNewsAPI 오류 조사와 결과 보존

2026-11-11 KST. 사용자 실행 결과와 이번 추가 호출을 구분합니다. [기계 판독 증거](verification/2026-11-11-freenews-investigation.json), [최신 프로젝트 상태](PROJECT_STATUS.md), [권리 정책](DATA_SOURCES.md)을 함께 봅니다. 원본 `server/reports/validation.json`은 덮어쓰지 않았습니다.

## 1. 기존 검증 JSON에서 확인한 결과

원본 checked_at은 2026-11-11T10:18:02Z(19:18 KST)이며 FreeNewsAPI 키 로딩은 true입니다.

| 검색어/기간 | 원본 상태 | 반환 기사 레코드 | 추가 페이지 | 전체 검색 건수 |
|---|---|---:|---|---|
| 애니메이션24h | HTTP500 | 미측정 | 미측정 | 미제공/미측정 |
| 애니메이션168h | HTTP500 | 미측정 | 미측정 | 미제공/미측정 |
| 과학 IT24h | SUCCESS | **0** | 없음 | null |
| 과학 IT168h | TIMEOUT | 미측정 | 미측정 | 미제공/미측정 |
| 예술24h | SUCCESS | **5** | 없음 | null |
| 예술168h | SUCCESS | **첫 페이지10** | 있음 | null |

`SUCCESS`는 요청/응답 해석 성공이며 기사 수가 양수라는 뜻이 아닙니다. `reported_total=null`을0으로 바꾸지 않습니다. 예술168h는 제공자의 has_more=true에 따르면10건보다 더 있으며, 전체 pagination을 수행하지 않아 정확한 총수를 모릅니다. 기간이 겹치므로5+10을 고유 기사15건이라고 더할 수도 없습니다. 표본 중복률0.0은 받은 페이지의 제목 유사도 측정일 뿐 전체/동일 사건 중복률을 보증하지 않습니다.

기존 validate는 건수/필드 이름만 보고서에 남기고 원문 기사 metadata를 DB에 저장하지 않았습니다. 이번 조사 시작 시 FreeNews 콘텐츠 테이블은0건이었습니다. 원본 보고서만으로 당시 기사 목록/고유 기사 수를 복원할 수는 없습니다.

## 2. 공식 요청 형식과 코드 비교

[현재 공식 OpenAPI](https://www.freenewsapi.io/docs/openapi.json)와 [문서 진입점](https://www.freenewsapi.io/docs/)을 조회했습니다. schema hash는 증거 JSON에 남겼습니다.

| 요소 | 공식 문서 | 현재 NewsProvider |
|---|---|---|
| URL | `https://api.freenewsapi.io/v1/news` | 동일 |
| 인증 | x-api-key 헤더 | .env의 키를 헤더로 전달, 값 출력 안 함 |
| 검색 | in_title, 제목 검색 | 동일. 제거된 q/in_body/in_subtitle 사용 안 함 |
| 필터 | language/country 문자열 | ko/KR. 같은 필터의 예술 요청은 실제200 |
| 시간 | date-time 문자열 | timezone-aware ISO8601, HTTPX query 인코딩 |
| 정렬 | recent/archive | recent |
| 페이지 | offset/cursor, 상호 배타 | 첫 페이지, 두 옵션을 함께 보내지 않음 |
| 개수 | meta.returned/page_size/has_more | 보존. 공식 FreeNews schema에는 전체 found가 없음 |

이번 비교에서 요청 형식 불일치는 찾지 못했습니다. 이 사실은 제공자 내부의 버그가 없다는 뜻도, 모든 입력 조합이 정상이라는 뜻도 아닙니다. 검색어를 임의 번역/분리하거나 시간 표현을 근거 없이 바꾸는 수정은 하지 않았습니다. 특히 과학 IT의0건은 **해당 제목 검색 조건**의 결과이며 모든 과학/IT 뉴스가 없다는 결론이 아닙니다.

## 3. 추가 실제 호출: 목록3회, 상세2회

목록 조사는 원본 JSON의 같은 window_end와 동일한 필터/정렬을 사용했습니다. 재시도 없이 connect5초/read20초로 세 경우만 조회했습니다.

| 통제 호출 | 실제 관측 | 의미 |
|---|---|---|
| 애니메이션24h | 500, 약0.844초. JSON 메시지 Internal Server Error | 오류 재현. 구체적 내부 원인 정보 없음 |
| 예술24h | 200, 약1.422초,5건 | 같은 인증/필터/시간 형식의 대조 요청 성공 |
| 과학 IT168h | 200, 약10.844초,0건 | 더 긴 대기로 완료한 관측. 과거 TIMEOUT 원인 확정은 아님 |

애니메이션168h, 예술168h, 과학 IT24h를 다시 전부 호출하지 않았습니다. 500의 내부 원인을 확정하려면 제공자의 로그/상세 오류 정보가 필요합니다. 이번 응답에는 일반 메시지만 있어 SQL/인코딩/데이터 오류 중 무엇인지 판단할 근거가 없습니다. 제공자에 메시지를 보내거나 내부 시스템을 탐색하지 않았습니다.

기존 TIMEOUT에는 connect/read/write/pool 구분이나 정확한 요청 경과시간이 없었습니다. 이번10.844초는 연결 등을 포함한 전체 경과시간이므로 “기존 read10초가 반드시 원인이었다”고 단정하지 않습니다. 다만 대기 정책을 구분해 기록하고 확대할 근거가 됩니다. [HTTPX timeout 원리](https://www.python-httpx.org/advanced/timeouts/).

받아 둔 예술5건의 목록 metadata를 재검색 없이 보존한 후, 그중2건에만 `/details`를 호출해 실제 원문 URL을 얻었습니다. 두 건 모두 정규화/SQLite 저장 성공. 새 목록 호출0회, 상세2회로 총 추가 호출은 **5회**입니다. 마지막 실제 응답의 일일 무료 잔여는4,988이었습니다. 이는 관측 시점 값이며 현재 잔여를 보증하지 않습니다.

이 실자료를 사용하는 FastAPI TestClient에서 화면2건, 해당 뉴스의 음성 큐0건, 설명403/403을 확인했습니다. 실제 네트워크를 통한 뉴스 API 호출과 내부 ASGI 검사는 구분하며, 이번에 실차/TTS를 실행한 것은 아닙니다. 기사 본문/요약문은 저장·재배포하지 않았고 두 항목은 LIVE + LICENSE_UNVERIFIED입니다.

## 4. 적용한 오류 처리 정책

| 항목 | 정책 |
|---|---|
| connect/write/pool | 각각 최대5초 대기 |
| read | 기본20초 inactivity 대기, NOTICE_NEWS_READ_TIMEOUT_SECONDS 설정 |
| 요청 전체 | HTTP 시도당30초 상한. CLI 전체 제한시간은 아님 |
| 재시도 | GET의 TIMEOUT/NETWORK_ERROR, HTTP502/503/504에 최대1회 |
| 백오프 | 1×2^index초 + 0~0.25초 jitter. 기본 최대1회 재시도라 첫 대기만 적용 |
| 반복하지 않음 | 400/401/403/429/500, 잘못된 JSON/schema |
| rate/quota | FreeNews 요청 시작 간격0.6초 이상. 429 또는 일일 잔여0 관측 시 해당 job의 후속 요청 중단 |
| 요청 예산 | 기본20회, 재시도/상세 조회까지 포함. --max-requests로 더 작게 제한 가능 |
| 관측 | 각 시도 결과·경과시간·timeout 단계·응답 hash. URL/인증 헤더/에러 본문은 기록 안 함 |

500은 현재 특정 질의에서 재현되어 자동 반복 대상에서 제외했습니다. 일시적500이 나중에 회복될 가능성은 있지만 이 정책은 그 재시도 기회를 포기합니다. 반대로20초 대기와 재시도는 느린 요청을 완료시킬 수 있으나 실행시간/무료 할당량/제공자 부하를 늘립니다. GET이라도 timeout 시 서버가 처리 중일 수 있고 재시도가 또 한 번의 유료/무료 할당량 요청으로 계산될 수 있어 보수적으로1회만 허용합니다. 유료 전환은 없습니다.

HTTPX read timeout은 전체 요청시간과 다르므로 asyncio.timeout으로 별도 전체 상한을 둡니다. 각 시도에서 상태를 초기화해 이전200을 다음 timeout의 HTTP 상태로 잘못 보고하지 않습니다. quota로 요청을 보내지 않은 경우에도 실제429 응답을 받았다고 만들어내지 않고 HTTP 상태는 null로 남깁니다. 전역 다중 프로세스/다른 앱의 일일 사용량을 통합 관리하는 장치는 아직 없습니다.

## 5. 성공 결과 보존과 재현 명령

검색별 성공/실패와 허용된 기사 metadata는 news_searches에 append하고, 검증 JSON은 매 검색 뒤 임시 파일→교체로 checkpoint합니다. 이후 검색어나 상세 조회가 실패해도 앞선 자료를 삭제하지 않습니다. 수집은 목록 metadata를 먼저 commit하고 상세 URL을 일부 보강합니다. 수집 JSON은 종료 시 작성하지만 중간 검색 결과는 DB에 남습니다. 일반 HTTP 실패는 다른 기사를 계속 처리하되 인증/할당량/예산 한도에서는 후속 상세를 멈춥니다. 중단/재개를 위한 자동 cache 재사용 CLI는 아직 없으며 이번 재사용은 저장된 진단 결과를 명시적으로 가져온 것입니다.

기존 seed/ingest/validate는 유지했습니다. 불필요한 공공/다른 제공자 호출을 피하려면 server 폴더에서 새 명령을 사용하세요. 아래는 **다시 실행할 때만** 외부 요청을 소비합니다.

```powershell
# 특정 TIMEOUT 경우만, 재시도 포함 최대2회
.venv\Scripts\python.exe -m app.cli validate-news --provider freenews --keyword '과학 IT' --window-hours 168 --max-requests 2 --report reports/freenews-targeted.json
# 뉴스만 수집: 목록/상세/재시도 전체 최대4회, 성공 metadata는 중간 저장
.venv\Scripts\python.exe -m app.cli ingest-news --keyword '예술' --max-requests 4 --report reports/freenews-ingest.json
```

validate-news의 기본 대상은 FreeNewsAPI뿐입니다. keyword/window를 생략하면 기존3검색어×24/168h이며, 같은 옵션을 중복 지정해도 동일 질의는 한 번만 수행합니다. validate-news는 metadata 관측을 저장하고, feed용 원문 URL 보강은 ingest-news가 수행합니다. `.env`의 실제 키와 기존 값은 수정하지 않았습니다.

## 6. 검증과 남은 문제

기존64 + 새 회귀35, **pytest99 통과**. Ruff/format, pip check, compileall 통과. 상위 Starlette TestClient deprecation warning1건은 남아 있습니다. OpenAPI 스냅샷 일치 테스트도 통과해 차량 API의 요청/응답 계약을 유지했음을 확인했습니다.

[재시도 테스트](../server/tests/test_news_resilience.py)는 단계별 timeout, 복구 후 시도 수, 502/503/504, 반복하지 않는500/인증/429, 예산/잔여0/전체 상한/metadata whitelist를 검사합니다. [job 테스트](../server/tests/test_news_jobs.py)는 검색/상세 실패와 처리 중단 이후 DB/JSON 보존, 건수 해석, 중복 질의 제거, 뉴스 전용 CLI를 검사합니다. 실제 API의 TIMEOUT 재시도 복구를 강제로 유발해 검증한 것은 아니며 재시도 분기는 MockTransport로 확인했습니다.

남은 문제: 애니메이션500의 내부 원인, 정확한168h 전체 기사 수/고유 기사 수, 원문 뉴스 TTS/AI 라이선스, 미측정 실차/학교 AI/라우팅. 이번 수정은 500을 해결했다고 주장하지 않고 관측·오류 격리·성공 자료 보존을 개선합니다. [공식 약관](https://www.freenewsapi.io/terms.php)은 뉴스 권리가 원저작권자에게 있고 필요한 허가를 별도 확보해야 한다고 명시하므로 기존 차단을 유지합니다.
