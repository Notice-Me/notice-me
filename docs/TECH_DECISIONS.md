# 기술 선택 근거

## TD-16. 제출용 증거와 실행 의존성을 제품 기능과 분리 (2026-11-14)

사용자 지시로 11/15의 성공 기준을 현장 전체 시연이 아닌 기획서 접수+추가 APK/소스로 확정했다. 기존 서버/차량 API와 팀원 UI를 보존하고 같은 main 소스의 debug APK를 빌드·서명/버전/설치·SHA256으로 식별한다. 새 내장 MOCK 모드는 서버 detail/권리/모드 계약을 새로 검증해야 하므로 이번에는 구현하지 않고 키 없는 기존 MOCK 서버와 무음 화면 영상을 제공한다.

문제: 원본 개인 local.properties의 drive separator 때문에 assemble/test 후 Lint 단계가 실패했다. 개인 설정 수정이나 Lint 규칙 비활성화 대신 추적 소스만 동일 사본으로 옮기고 ANDROID_HOME을 지정해 두 Lint 오류0을 확인했다. 원본 APK/테스트 결과와 사본 Lint 결과를 구분한다. debug 서명은 설치/무결성 증거이며 release/스토어 인증과 다르다. 외부 심사자는 서버/Pleos 서비스·권한·HTTP 접근이 필요하고 private GitHub 링크는 열리지 않을 수 있다.

실행 근거: 서버190, 두 flavor각26, MOCK 실제 청취/SDK, LIVE 날씨 SDK brief 일치·onDone, 날씨1회만 실제 호출. 출시 경고·음질·실차·내일의 날씨 신선도는 해결되지 않았다. [제출 보고서](SUBMISSION_MVP_2026-11-15.md), [검증 JSON](verification/2026-11-14-submission.json). 새로운 AI 자문/자동화나 성능 벤치마크는 수행하지 않았다.

## TD-14. 구체 취향은 제목 증거와 형식 문맥을 함께 검사 (2026-11-13)

사용자가 요구한 구체 취향을 기존 넓은 태그 교집합만으로 처리하면 일반 애니메이션·근처 뉴스가 치이카와를 대체한다. 서버 내부 불변 InterestProfile(category/topic/format/keyword)을 선택하고 기존 interests 배열·응답 모델을 유지했다. 실제 학교 AI·임베딩/본문 검색 대안은 권리·설정·일정에 비해 요구가 커 구현 실험 없이 제외했다. 동의어 사전과 NFKC/단어 경계는 무료·결정적·회귀 재현이 쉽지만 제목에 없는 행사/별칭을 놓친다.

topic/keyword OR + format OR 간 AND를 선택해 구체 취향을 좁힌다. 팝업은 store/캐릭터/행사 문맥, 캐릭터굿즈는 캐릭터 근거도 필요하다. broad-only fallback은 보존하고 explicit weather와 긴급 경로는 별도로 유지했다. 과거 뉴스 검색어가 태그를 오염시키므로 신규 분류는 제목만 사용하고 구체 요청은 기존 태그도 제목으로 재검증한다. 기사 본문/LLM·신규 요청 이력 저장은 없다.

행사 중복은 같은 정규화 제목·동일 일정·검증 상태와 동일 장소/가까운 알려진 좌표 조건으로만 합친다. 다른 지점/회차/불명확 장소는 보존한다. 뉴스 중복 기존 조건은 유지한다. 이 변경의 실제 회귀 실패와 해결,190개/HTTP 검증은 [개발 로그](DEVELOPMENT_LOG.md), 설계·대안·길안내 미구현은 [계약 검토](INTEREST_CONTRACT_REVIEW.md)와 [P1 조사](POPUP_ROUTING_RESEARCH.md). 추천 일치가 TTS 권리나 이동시간 허가를 주지 않는다.

## TD-13. 권리 허가와 이번 LIVE 음성 범위를 분리 (2026-11-13)

사용자가 LIVE 날씨만 음성으로 요청했으므로 기존 권리 검사 외에 voice_allowed를 두었다. queue와 detail이 다른 권한을 주는 대안은 우회 재생 위험이 있어 같은 정책을 사용한다. weather는 nullable 추가 필드라 옛 DB를 유지하며, 갱신 전 자료는 fail closed한다. 원천 시각1시간 TTL과 고정 지역을 명시해 현재/목적지 날씨로 오인하지 않는다. NAV ETA와 행사 길찾기는 분리한다. 자동 수집 대신 수동 갱신을 선택해 시연 범위와 호출량을 제한하되 장시간 운영은 해결하지 못한다. 실제 호출·처음 실패·회귀와 향후 대안은 [날씨 시연](LIVE_WEATHER_DEMO.md). 대규모 프레임워크/외부 공급자 교체 실험은 하지 않았다.

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

## TD-15. 프로필과 상세 검색을 명시적으로 분리하는 계약 제안 (2026-11-13)

사용자 요청은 이번에는 구현보다 먼저 호환 방안을 제안하는 것이다. #9의 구체 관심사 matcher에 치이카와·science·anime를 그대로 넣으면 실제 지브리 제목이 빠지는 것을 별도 사본에서 재현했다. 기존 배열을 OR로 바꾸면 치이카와 AND 팝업을 넓히므로 채택하지 않았다. GET에 mode를 추가하는 대안은 구 서버가 모르는 query를 무시할 수 있다. 기존 GET을 유지하고 새 POST의 profile OR/filter AND·구 서버404를 권고했다. 이는 **설계 제안**이며 구현/성능 비교가 아니다. [필드·날씨/긴급 경계·인수 기준](INTEREST_PROFILE_PROPOSAL.md).

새 기능 구현을 선행하지 않고 공식 출처를 조사한 결과, 실제 공지라도 주소·좌표·개별 운영사·재사용/변경 확인이 부족했다. 공식 티켓 공지 자체에도17시/19:30 상충이 있어 임의 선택하지 않았다. KOGL1 공공 메타데이터5건은 기존 수집기로 검증했지만 기존 라우팅 게이트를 풀지 않았다. [관측·누락·권리](CONTENT_SOURCE_FOLLOWUP.md). 무료 길찾기는 키·사용조건/과금 상태가 미확인이라 조사/소량 시험 계획만 작성했다. 이는 쿼터 우회·유료 사용·실측 이동시간 확보가 아니다. [연결 조건과 동기/비동기 대안](ROUTING_TRIAL_PROPOSAL.md).

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

## TD-09. 뉴스 실패 격리와 소량 재시도 (2026-11-11 추가)

**실제 근거:** 사용자가 설정한 키의 검증 JSON은 과학 IT24h=0건, 예술24h=5건, 예술168h=첫10건/추가 페이지 있음이었습니다. 애니메이션24h는 같은 시간 범위로500을 재현했고 상세 원인은 제공되지 않았습니다. 과학 IT168h는 대기를 늘린 관측에서 약10.844초 후0건을 받았지만 과거 timeout 단계를 복원할 수는 없습니다. [전체 조사와 통계](FREENEWS_INVESTIGATION.md).

**선택과 작동:** 뉴스 read20초/connect·write·pool5초, HTTP 시도 전체30초를 구분합니다. GET timeout/일부 네트워크 오류/502·503·504에만 최대1회 재시도하며1초+jitter로 대기합니다. 500·인증·429·schema 오류는 반복하지 않습니다. 요청 간격/시도 예산/일일 잔여0 상태를 검사하고, 시도마다 timeout 종류·상태·경과시간만 기록합니다. HTTPX의 read timeout은 전체 요청 제한과 다르므로 외부 전체 deadline을 함께 사용합니다. [HTTPX 공식 timeout 설명](https://www.python-httpx.org/advanced/timeouts/).

**검토한 대안:** 모든500 반복은 복구 기회가 있지만 이번 재현 질의에서는 추가 호출만 소비할 수 있어 제외했습니다. 재시도0회는 할당량을 아끼지만 일시적502/네트워크 오류 복구 기회를 줄입니다. timeout 무제한 확대는 작업 종료가 불명확해 채택하지 않았습니다. 모든 정책을 실제 서비스 부하로 비교한 실험은 아니며, 실제 관측과 MockTransport 테스트를 근거로 선택했습니다. GET도 제공자 할당량은 다시 소비할 수 있습니다.

**자료 보존:** 검증 결과를 한꺼번에 마지막에 쓰던 구조에서 검색별 DB append/JSON checkpoint로 바꿨습니다. ingestion도 목록 metadata를 먼저 저장하고 일부 기사 URL을 보강합니다. 후속 실패/중단이 성공 결과를 지우지 않도록 했습니다. 새 뉴스 전용 CLI로 무관한 공공/다른 제공자 호출을 생략하고 중복 query 옵션도 제거합니다.

**검증과 한계:** 신규35개를 포함해 pytest99 통과. 실제 추가 호출은 목록3·상세2로 끝냈고, 받은 목록을 재사용해 실제 뉴스2건을 저장했습니다. TTS/설명 권리는 확보하지 않아 두 건 모두 차단했습니다. 정책의 재시도 실패/복구 분기는 MockTransport로 확인했으며 실제 API timeout을 강제로 유발한 검증은 아닙니다. 20회는 한 CLI 실행의 예산으로, 다른 프로그램을 포함한 전역 일일 사용량 관리가 아닙니다. 애니메이션500 내부 원인은 여전히 미확정입니다.

## TD-10. 서버 HTTP 준비와 Pleos 기기/TTS 완료를 따로 판정 (2026-11-11)

**요구와 관측:** 11/15 MVP의 다음 병목은 Pleos 에뮬레이터·실차 연결입니다. 서버 API와 SDK/오디오 출력은 서로 다른 통신·권한 경로입니다. 기존 연결 검사 도구는 재생 id가 후보의 일부인지 확인했지만 전체 순서·긴급 항목의 권리 근거 검사는 부족했습니다. 서버가 잘못된 큐를 생성했다는 관측은 아니며 검사 도구의 검출 범위를 보강한 것입니다.

**선택과 원리:** 차량 API v1을 유지하고 기존 HTTP 검사에서 queue/alerts의 권리·만료·교통 freshness, 긴급 우선 전체 playback_order, LIVE 화면 뉴스의 상세/설명 차단을 확인합니다. 보고서에 SERVER_HTTP_ONLY와 SDK/TTS 미검증 값을 명시합니다. health200은 서버/DB 접근이고 실제 재생 후보 준비·앱 연결·TTS 출력과 별개입니다. 학교 AI 없이도 허용 brief를 차량 TTS에 전달할 수 있으므로 explain을 첫 재생의 선행조건으로 두지 않습니다.

**접속 대안과 트레이드오프:** 첫 에뮬레이터 시도는 팀원 PC에 서버도 실행하거나 도달 가능한 LAN을 사용하도록 안내했습니다. 공개 클라우드 배포보다 준비가 작지만 실행 PC·방화벽·동일 네트워크에 의존하며 외부망 접속은 해결하지 못합니다. 표준 AVD의10.0.2.2는 AVD가 실행되는 PC이므로 다른 PC의 서버 주소와 구분해야 합니다. [Android 공식 주소](https://developer.android.com/studio/run/emulator-networking-address), [FastAPI 실행/바인딩](https://fastapi.tiangolo.com/deployment/manually/). 서로 다른 기기에서의 연결 성능 비교는 수행하지 않았습니다.

**무료 수집과 SDK 경계:** 기존 ingest에 선택적 --public-provider를 추가해 날씨만 갱신하며 기본 전체 수집 동작은 유지합니다. 실제로 서울시 날씨1회/FreeNews0회를 추가 호출했습니다. Pleos 공식 문서의 ON_DEVICE TTS는 첫 시연 후보로만 제안했고 SDK 의존성 설치나 모드 실행은 하지 않았습니다. HYBRID/SERVER 등록과 실제 한국어 엔진 지원을 확보했다고 기록하지 않습니다. [Pleos 문서·권한·앱 절차](VEHICLE_INTEGRATION.md#8-pleos-앱-담당자의-sdktts-준비).

**검증/한계:** pytest110, 실제 Uvicorn5시나리오, 서버 PC의 자기 LAN 주소 health200. 실제 수집 뉴스2건의 TTS 자격 false/설명403을 재확인했습니다. 이 검사는 원격 팀원·Pleos SDK·음성 출력 성공을 입증하지 않습니다. [측정 JSON](verification/2026-11-11-vehicle-handoff.json), [팀원 확인표](VEHICLE_ACCEPTANCE.md). 기기 네트워크/권한/TTS 준비를 완료한 뒤에만 MVP 연결 완료를 판정합니다.

## TD-11. TourAPI의 상태·날짜·페이지와 추천 자격을 구분 (2026-11-11)

공식 Swagger/국문 매뉴얼v4.4와 동일 요청 재조회에서 progresstype의 기본값 선택안함을 확인했습니다. 필드 존재 여부로 취소를 판단하던 코드를 값별 정책으로 바꿨습니다. 빈 값/기본값을 허용하고 취소·연기·미확인 값은 사유를 남겨 보류합니다. 실제 온라인1건은 다른 필드로 임의 해석하지 않았습니다. [조사/공식 근거](TOURAPI_INVESTIGATION.md).

**날짜·정렬 선택:** KST 오늘~90일과 로컬 기간 겹침 검사를 사용합니다. 과거30일과 첫10건만 보면 종료 항목이 앞에 몰립니다. 실제로는 오늘 시작 범위 요청에서도2022년에 시작한 진행 중 행사가 반환돼 임의365일 lookback 확대를 채택하지 않았습니다. 수정일 기준 C는 명세가 있는 옵션이며 행사 시작순은 정규화 후 로컬로 정렬합니다. 범위를 줄여 호출을 아끼지만90일보다 먼 예정 행사/전시 전체를 수집한 것은 아닙니다.

**페이지·보존 원리:** totalCount와 누적 수신량으로 종료하며 마지막 응답 numOfRows를 페이지 간격으로 사용하지 않습니다. 첫 실수집의50+27 뒤 불필요한3페이지를 확인해 수정했습니다. 기본3페이지/3시도·간격1초·재시도0회로 제한하며 불완전하면 PARTIAL을 표시합니다. SQLite에 페이지/행별 판단과 성공을 먼저 commit하고 새 취소/만료/불명확 관측은 기존 레코드를 삭제하지 않고 UNVERIFIED로 격리합니다. 상세 소스 상태는 event_pages에 남습니다. 총수 변경·중복은 원자적 snapshot이 아님을 드러내며 전역 일일 사용량 관리는 미구현입니다.

**검증/트레이드오프:** 최종 실호출2회에서77→76건(진행 중36/예정40), 날짜 유효76건을 확인했습니다. 조사 전체는6회이며 첫 실패도 포함합니다. pytest147, 권리·LIVE 라우팅 제외 회귀 확인. Type3는 TTS/가공 허가로 확대하지 않고 brief를 비웁니다. 수집 성공과 추천 가능/음성 출력은 별개입니다. 페이지별 DB 저장은 감사/중단 복구 근거를 남기지만 관측 테이블이 누적되며 자동 보관 정리·전체 동기화는 아직 없습니다.

## 앞으로의 갱신 기준

기술/저장 구조/계약/검증 정책이 바뀌었을 때 해당 결정에 날짜와 근거를 추가합니다. 수행하지 않은 대안 실험은 미수행으로 남깁니다. 변경하지 않은 기술의 설명을 매 작업마다 복제하지 않고 개발 로그에서 해당 TD 항목과 테스트/커밋을 연결합니다.

## 2026-11-11 — 차량 앱 시작과 재생 취소 설계

사용자는 화면 표시/음성 우선 구현과 11/15 시연을 요청했고 앱 코드가 없다고 확인했습니다. Kotlin/Android Views, 두 speech flavor, AGP/Gradle 고정은 구현자가 선택했습니다. 기존 UI 자산이 없어 Compose 추가 구성 대신 기본 Views로 카드/설정/컨트롤을 구현했습니다. 장점은 작은 의존성과 단순한 첫 화면이며, 차량별 주행 UX 검증은 별도 작업입니다.

Pleos 3.3.1 공식 문서/AAR에 따라 ON_DEVICE를 명시했습니다. HYBRID 기본 모드는 앱 등록/서버 의존성이 생기므로 첫 시연에서 제외했습니다. 일반 Android flavor는 로컬 한국어 엔진만 사용하고 Pleos 실패를 숨기는 자동 fallback을 두지 않습니다.

음성 큐는 화면 카드와 분리하고 재생 직전 최신 feed/detail/시간을 검사합니다. 캐시 재생은 오프라인 사용성이 좋지만 만료/권리/교통 freshness를 보장할 수 없어 채택하지 않았습니다. coroutine 취소와 세션별 SDK 생성/해제로 패스·다시 때 늦은 완료 콜백이 새 항목을 넘기는 문제를 방지합니다. 초기화 비용과 항목 간 지연은 실제 기기 측정이 필요합니다. 오디오 포커스 해제 후 이전 콜백은 active 플래그로 무시합니다.

검증은 [기록](verification/2026-11-11-vehicle-app.md) 참조. 차량 주행 제한·미디어 세션까지 구현한 것으로 해석하지 않습니다.

## TD-14. 팀원 내비 코드를 유지하고 지역·시각·음성 범위를 명시 (2026-11-13)

내비 문맥 조회를 다시 작성하는 대신 기존 NaviHelper/currentQuery/15초 idle 갱신을 유지했다. nullable weather 파싱과 앱 쪽 LIVE 날씨 전용 검사는 서버 구버전/잘못된 큐에서도 읽기 전용 콘텐츠가 재생되는 것을 막는다. LIVE/MOCK·고정 관측 지역·원천시각/만료·원문 링크·diagnostics를 표시하고 NEWS brief는 표시하지 않는다. idle 갱신 실패 때 옛 카드/연결 허가도 제거한다. UI/모델 변경 없이 TTS만 켜는 대안은 지역 오인·권한 혼동이 있어 제외했다. TTS 엔진/오디오 코드는 변경하지 않아 잡음 개선 범위로 확장하지 않았다.

SDK CurrentLocationInfo에 원천 GPS 시각이 없어 receivedAt/30초는 콜백 재사용만 제한한다. routeStatus로 미사용/미수신/실제/모의 안내를 구분하되 도로 링크나 행사 소요시간을 생성하지 않는다. 단위26개/각flavor, 실제 SDK/HTTP/청취, 권한이 없어 실패한 별도 목적지 생성 실험은 [2026-11-13 기기 검증](verification/2026-11-13-live-weather-vehicle.md). 새 권한을 부여하지 않고 사용자가 기본 내비에 설정한 경로를 읽어 실제 목적지/ETA 전달을 확인했다.


2026-11-13 최종 보완: 원격 main에 외부 병합된 UI PR #7(94de875)을 기능 브랜치에 반영하고 두 충돌을 해결했다. 팀원 레이아웃과 날씨·권리 방어를 보존했으며 두 APK/각26테스트·Lint0오류·실제 기기 재생 제어와 brief 일치를 재검증했다. MOCK 테스트 URL 오지정 실패와 수정도 [최종 인수 기록](verification/2026-11-13-live-weather-vehicle.md)에 남겼다. main/타인 브랜치 push·force push·PR 병합은 수행하지 않았다.
