# 기술 선택 근거

작성 기준: 2026-11-11. 이 문서는 현재 코드에 적용한 선택과 그 이유를 설명합니다. 처음부터 사용자가 지정한 기술은 그렇게 표시하고, 경쟁 기술을 설치·벤치마크해서 선정한 것처럼 쓰지 않습니다. 대안의 장단점은 실제 구현 비교인지 공식 문서에 따른 개념 비교인지 구분합니다. 전체 기획은 [PROJECT_CONTEXT](PROJECT_CONTEXT.md), 완료 범위는 [PROJECT_STATUS](PROJECT_STATUS.md), 시행착오는 [DEVELOPMENT_LOG](DEVELOPMENT_LOG.md)에 기록합니다.

## 선택의 출발점

Python 3.11+, FastAPI, SQLite, pytest, .env는 사용자 요구사항입니다. HTTP 클라이언트는 httpx 또는 requests 중 선택할 수 있었고 구현은 httpx를 사용했습니다. 실제 실행 환경은 Python 3.11.9이며 설치 버전은 [requirements.lock](../server/requirements.lock)으로 남겼습니다. 다른 언어/웹 프레임워크/DB의 처리량을 측정한 실험은 없습니다.

| 결정 | 적용 상태 | 요구사항과 연결 |
|---|---|---|
| TD-01 FastAPI + Pydantic + OpenAPI | 사용 중 | 차량 팀원과 네 JSON endpoint를 공유하고 입력·응답 타입 검증 |
| TD-02 SQLite + 표준 sqlite3 + metadata JSON | 사용 중 | 무료 단일 서버 프로토타입, 수집 결과 재조회·모드 구분 |
| TD-03 httpx + 수집/조회 분리 | 사용 중 | 무료 호출량 관리, 타임아웃/인증 오류 처리, 외부 장애와 feed 조회 분리 |
| TD-04 규칙 추천 + 공통 유효성/권리 검사 | 사용 중 | TOP3/음성 큐/긴급정보 분리와 재현 가능한 판단 근거 |
| TD-05 pytest + MockTransport + 실제 HTTP 검사 | 사용 중 | 회귀 테스트와 실연동 증거를 별도로 확보 |
| TD-06 LLMProvider/Router 인터페이스와 명시적 Mock | 인터페이스/Mock만 | 학교 endpoint와 실제 도로 이동시간이 아직 없음 |
| TD-07 .env + SecretStr + 기능 브랜치 | 사용 중 | 키/개인정보 제외, 검토 전 main 병합 금지 |
| TD-08 출처별 정규화 + XML 파싱 | 사용 중 | 서로 다른 공식 API 필드/시각/좌표를 공통 콘텐츠로 변환 |

## TD-01. 응답 객체를 코드와 API 계약의 공통 기준으로 사용

FastAPI는 요청을 endpoint로 연결하고 Pydantic 모델로 입력·출력의 타입과 제약을 다룹니다. 이 모델이 JSON Schema/OpenAPI로 표현되므로 앱 개발자는 nullable 좌표·시각, enum, 배열 구조를 확인할 수 있습니다. 그러나 타입 검증이 뉴스의 사실성이나 저작권을 보증하지는 않으며 별도 도메인 검사가 필요합니다. [FastAPI 기능](https://fastapi.tiangolo.com/features/), [응답 모델](https://fastapi.tiangolo.com/tutorial/response-model/), [Pydantic 모델](https://docs.pydantic.dev/latest/concepts/models/).

**실제 비교한 방식:** 초기 health/detail은 Python dict를 반환하고 필드를 문서에 적었습니다. 동작은 했지만 OpenAPI의 성공 응답 schema가 `{}`였습니다. 현재는 HealthResponse/ContentDetail을 명시합니다. 수기 dict는 초기 코드가 짧다는 장점이 있었고, 모델 방식은 필드 정의와 유지 비용을 추가하는 대신 클라이언트가 확인할 타입과 응답 검증을 제공합니다. Flask/Django 서버를 구현해 성능 비교한 적은 없습니다.

**검증:** [test_api_contract.py](../server/tests/test_api_contract.py)에서 네 성공 응답의 타입과 top3의 maxItems=3, 기존 상세 필드를 확인합니다. 저장한 OpenAPI가 런타임 명세와 같은지도 검사합니다. 생성기는 [export_openapi.py](../server/scripts/export_openapi.py)입니다. 요청 URL·JSON 필드는 유지했습니다.

**한계:** 명세가 맞아도 차량 SDK/HTTP 설정/TTS는 별도 검증입니다. 모델 변경 시 계약 갱신과 저장 JSON 호환성을 함께 확인해야 합니다.

## TD-02. 별도 DB 서버 없이 metadata를 보존

SQLite는 애플리케이션이 로컬 DB 파일을 읽고 쓰는 방식입니다. Python 표준 sqlite3로 SQL을 실행합니다. 현재 테이블은 콘텐츠 id를 기본키로 두고 모드와 Pydantic JSON payload를 저장하며, 같은 id를 upsert합니다. 수집 기록은 별도 테이블입니다. 파일 하나로 초기화와 재조회를 할 수 있어 이 단일 서버 MVP의 운영 부담을 줄였습니다. [SQLite 적용 범위](https://sqlite.org/whentouse.html), [Python sqlite3](https://docs.python.org/3.11/library/sqlite3.html).

**문서상 비교만 한 대안:** PostgreSQL 같은 client/server DB는 여러 클라이언트의 동시 작업·중앙 운영에 맞지만 별도 서버와 운영 설정이 필요합니다. SQLite는 설치·이동이 단순한 대신 다중 쓰기/분산 운영 요구를 따로 평가해야 합니다. 실제 PostgreSQL 배포나 동시 접속 부하 비교는 하지 않았습니다. JSON payload는 필드 확장을 쉽게 시작하게 하지만 세부 필드별 SQL 검색/인덱싱과 schema migration은 더 설계해야 합니다. 정규화 테이블로 바꾸는 실험이나 ORM 도입도 하지 않았습니다.

**검증:** [storage.py](../server/app/storage.py), [저장 테스트](../server/tests/test_storage_popups_llm.py). 새 Store 인스턴스로 재조회, 동일 id 수정, 모드 격리, 특수문자가 있는 id의 parameter binding을 확인했습니다. context manager의 트랜잭션 commit/rollback과 연결 자원 정리는 별개이며 장시간 연결 수·부하를 측정한 기록은 없습니다. 사용자의 요청 위치·경로 이력은 저장하지 않고, 공공 콘텐츠의 장소 좌표는 콘텐츠 metadata로 저장합니다.

## TD-03. HTTPX를 사용하고 수집은 명시적 CLI로 실행

httpx.AsyncClient의 await 요청은 네트워크 I/O를 기다리는 동안 실행을 양보할 수 있고 MockTransport를 주입해 실패 응답을 재현할 수 있습니다. 실제 수집 코드는 제공자 순서대로 호출하며 이를 병렬 수집 성능 향상이라고 주장하지 않습니다. [HTTPX async](https://www.python-httpx.org/async/), [transport](https://www.python-httpx.org/advanced/transports/).

**문서상 비교:** requests의 Session도 연결 재사용을 지원하고 동기식 호출이 간단합니다. httpx는 현재의 async 수집 함수와 테스트 transport를 함께 사용할 수 있어 채택했습니다. requests를 설치해 같은 데이터로 응답시간/처리량을 비교한 실험은 없습니다. [Requests 고급 사용](https://requests.readthedocs.io/en/latest/user/advanced/).

**작동:** [SafeHTTP](../server/app/providers/base.py)가 timeout/HTTP 오류를 비밀값 없는 코드로 변환합니다. FreeNews 호출 간격을 두고, 수집기는 SQLite에 저장하며 feed는 그 저장 결과만 조회합니다. 매 feed마다 외부 API를 호출하는 대안은 구현하지 않았습니다. 조회와 수집을 분리하면 차량 조회가 API 할당량을 직접 소모하지 않는 대신 자료가 오래될 수 있어 재수집/만료 정책이 필요합니다.

**검증과 한계:** MockTransport로 401/403/429/500, timeout, 잘못된 JSON, XML 형식의 인증 오류 등을 검사했습니다. 실제 서울시 sample 호출도 별도 수행했습니다. 클라이언트를 요청마다 열고 닫는 현재 구조의 장시간 연결 재사용 성능과 전체 일일 호출량 제한 장치는 미검증/미구현입니다. 자동 스케줄러도 없습니다.

## TD-04. 설명 가능한 규칙과 단일 유효성 기준

기본 추천은 관심사/지역/최신성/출처/기한의 점수를 더합니다. top3와 권리를 통과한 전체 음성 큐를 별도로 만들고 교통 alerts를 앞에 둡니다. 가중치는 프로젝트 정책이며 학습된 최적값이 아닙니다. [정확한 점수 규칙](API_CONTRACT.md), [구현](../server/app/recommendation.py).

권리 상태, 원천 확인 상태, 자료의 유효성, 경로 관련성은 서로 다른 판단입니다. 예를 들어 원천 확인된 뉴스라도 TTS 권리가 없으면 음성/설명에서 차단합니다. 행사 이동시간을 모르면 거리로 바꾸어 허용하지 않습니다. 외부 모델에 모든 결정을 맡기는 추천기는 구현·비교하지 않았습니다.

**실제로 수정한 대안:** 초기에는 feed에만 교통 freshness 검사가 있었고 detail/explain에는 같은 조건이 없었습니다. 수집 후 11분인 교통정보의 detail은 tts_eligible=true, explain은 200이었습니다. 현재 [unavailable_reason](../server/app/availability.py)을 세 경로에서 공유합니다. 조건을 복제하는 방법은 각 endpoint만 수정하기 쉽지만 검사 차이가 생겼고, 공통 함수는 규칙 변경 영향이 넓어지는 대신 같은 기준을 유지하게 합니다. 회귀 테스트 10개로 경계/해제/기한/미래/누락 조건을 확인했습니다.

**한계:** 상세의 tts_eligible=true는 경로 관련성이나 행사 이동시간 검증의 대체가 아닙니다. 앱은 최신 feed 후보에서 재생 항목을 골라야 합니다. 실제 추천 적합도, 사용자 선호, 실제 TTS 길이는 측정하지 않았습니다.

## TD-05. 자동 테스트와 실통신 증거를 별도로 유지

pytest는 fixture/parameterization으로 여러 조건을 반복 검사하고, monkeypatch로 검사 시각을 고정해 10분 경계처럼 시간에 의존하는 동작을 재현합니다. MockTransport는 외부 통신을 대신하므로 키나 인터넷 없이 실패 조건을 검사할 수 있지만 실제 제공자 접근 가능성을 보증하지 않습니다. [pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html), [HTTPX transport](https://www.python-httpx.org/advanced/transports/).

실제 개발에서는 기존49 통과를 재현한 뒤 새 유효성 테스트에서 6실패/4통과를 확인하고 수정 후 총59, 계약 검사 후61, 차량 검사 도구의 실패 조건까지 포함해64 통과를 확인했습니다. 별도로 실행한 Uvicorn HTTP 검사는 MOCK/LIVE/MIXED와 실제 수집 자료를 확인합니다. [측정 보고서](verification/2026-11-11-revalidation.json).

Mock만 검사하는 방식은 반복 가능하지만 인증/원천 schema 변화를 놓칠 수 있고, 실제 API에만 의존하면 키/할당량/시각/장애에 따라 재현이 어렵습니다. 두 경로를 운영하는 대신 결과 파일과 의미를 분리해서 관리합니다. 실제 차량/부하/음성 재생 테스트는 아직 없습니다.

## TD-06. 미제공 AI/라우팅은 인터페이스와 Mock으로 한정

LLMProvider는 classify/summarize/explain에 필요한 메서드를 Protocol로 기술합니다. Protocol은 타입 계약이며 이를 작성했다고 실제 외부 서비스가 연결되는 것은 아닙니다. 현재 앱 생성 코드는 DeterministicLLM을 사용하며 실제 제공자로 교체할 때 생성/주입 코드와 공식 인증·응답 처리도 구현해야 합니다. [Python Protocol](https://docs.python.org/3.11/library/typing.html#typing.Protocol), [현재 코드](../server/app/llm.py).

학교 endpoint를 추측해 HTTP 코드를 작성하지 않았습니다. deterministic mock은 키워드와 저장 사실을 사용하고 임의 질문에 새 사실을 추가하지 않습니다. ai_mode=MOCK을 반환합니다. RoutingProvider도 인터페이스만 있고 실제 자료에는 UNVERIFIED, fixture 행사에만 SIMULATED25분을 적용합니다. [라우팅 코드](../server/app/routing.py).

**검증:** 미허가 자료 요약/설명 차단, 질문을 바꾸어도 저장 사실을 벗어나지 않는 응답, 모의 이동시간으로 LIVE 행사를 통과시키지 않는 조건을 테스트했습니다. **트레이드오프:** 키 없이 앱 계약 개발은 계속할 수 있지만 실제 AI 품질·경로시간 정확도를 입증한 것은 아닙니다. 외부 모델/지도 성능 비교는 하지 않았습니다.

## TD-07. 로컬 설정과 Git 검토 흐름

키는 .env/환경변수에서 읽고 SecretStr로 repr 노출을 제한합니다. 이는 파일 암호화나 권한 관리 자체가 아닙니다. .env/DB/가상환경/reports는 .gitignore 대상이며 개인 신청서는 저장소 밖에 보존했습니다. 설정이 있다는 사실과 인증 성공도 구분합니다. [config.py](../server/app/config.py), [.gitignore](../.gitignore), [키 안내](SETUP_API_KEYS.md).

기능 개발은 feat/server-content-feed와 PR #1로 검토합니다. main에는 초기화 커밋만 있고 병합은 명시 승인 대상입니다. 테스트와 업로드 파일/비밀정보 패턴을 push 전에 검사합니다. SecretStr repr와 provider 상태 출력에 비밀값이 없는 테스트도 있습니다. 전용 secrets manager·운영 인증/TLS·자동 CI는 구축하지 않았으며, 배포 이전에 추가 검토가 필요합니다. .gitignore만으로 이미 추적 중인 비밀 파일을 제거할 수 있다는 가정은 하지 않습니다.

## TD-08. 원천 schema와 의미를 확인한 뒤 정규화

서울시 도시/돌발 XML과 문화행사 JSON을 Content로 변환합니다. defusedxml은 외부 XML 파싱에 사용하고 이후 코드가 날짜/코드/필수 필드를 검사합니다. parser를 썼다는 이유만으로 모든 악성 입력 검증을 완료했다고 보지 않습니다. 공격 XML 보안 실험은 수행하지 않았습니다. [parser의 공식 저장소](https://github.com/tiran/defusedxml), [제공자 코드](../server/app/providers/seoul.py).

실제 AccInfo의 소문자 태그와 HHMM/HHMMSS를 처리하고, 좌표 체계 미확인 값을 WGS84로 추측하지 않았습니다. 등록일/원천 수정일/서버 수집일을 구분해 알 수 없는 updated_at은 null입니다. 공통 데이터셋 URL을 공유하는 다른 교통 id를 보존합니다. [필드/이용조건](DATA_SOURCES.md), [관측 형태 테스트](../server/tests/test_providers.py), [중복 테스트](../server/tests/test_recommendation.py).

이 선택은 불확실한 항목을 덜 노출하는 대신 추천 가능한 자료를 줄입니다. 현재 sample/한 페이지 수집, 실제 좌표 변환·취소 enum·라우팅 미확인 조건은 남아 있습니다. 무료 소스라는 이유로 뉴스 가공/TTS 권리를 확보했다고 취급하지 않습니다.

## 앞으로의 갱신 기준

기술/저장 구조/계약/검증 정책이 바뀌었을 때 해당 결정에 날짜와 근거를 추가합니다. 수행하지 않은 대안 실험은 미수행으로 남깁니다. 변경하지 않은 기술의 설명을 매 작업마다 복제하지 않고 개발 로그에서 해당 TD 항목과 테스트/커밋을 연결합니다.
