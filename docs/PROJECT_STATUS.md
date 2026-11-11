# Project status

**2026-11-11 KST / feature 0.1.0.** 서버 프로토타입과 실제 서울시 수집→SQLite→HTTP 응답 경로가 작동합니다. 실제 뉴스와 학교 AI/차량 연동까지 완성된 상태는 아닙니다.

## 최신 재검증 결과 (2026-11-11, 18시대 KST)

시작 커밋 d8f5c96에서 기존 **49 passed**를 재현했습니다. 검토 중 상세/설명이 오래된 교통정보를 허용하는 문제를 재현하여 fdd7e2f에서 수정했고, 응답 계약/차량 연결 도구를 보강한 최종 작업 트리에서 **64 passed**를 확인했습니다. Ruff check/format, pip check, compileall 통과. 상위 Starlette TestClient deprecation warning 1건은 남아 있습니다.

[현재 측정 보고서](verification/2026-11-11-revalidation.json)와 [차량 앱 연동 안내](VEHICLE_INTEGRATION.md)를 우선 참고하세요. 기존 API_VALIDATION_RESULTS/HTTP_SMOKE_RESULTS/examples는 초기 시각의 증거로 보존했습니다.

기술·학습 기록도 [기술 선택 근거](TECH_DECISIONS.md), [날짜별 개발 로그](DEVELOPMENT_LOG.md), [학습/회고](LESSONS_LEARNED.md)로 누적합니다. 구현 코드·측정·문서상 비교·미수행 실험을 구분하며 이후 작업도 AGENTS의 기록 지침을 따릅니다.

| 분류 | 항목 | 근거/범위 |
|---|---|---|
| 구현 완료 | 4개 endpoint와 응답 타입, SQLite, 규칙 추천/TOP3/별도 큐, 권리 차단 | 기존49 + 추가15 테스트. OpenAPI의 네 성공 응답 타입과 저장 명세 일치 검사. 큐/상세/설명에서 유효성 일치 |
| 구현 완료 | 앱용 HTTP 계약 검사와 실행 안내 | 서버 DB/API 키 없는 check_vehicle_api.py. 실제 Uvicorn HTTP에서 MOCK/LIVE/MIXED 모두 성공. 오류403/404/422, 모드·권리·만료 검사 |
| 부분 구현 | 공공 데이터 수집 | 현재 HTTP200 행사5·날씨1·교통5 정규화. sample/첫 페이지이며 전체 수집·자동 갱신은 없음. 날씨는 POI009 한 장소 |
| 부분 구현 | 긴급 경로 처리 | 직접 제공한 동일 SEOUL_TOPIS 링크에서 LIVE alert1. DEMO 경로에서 SIMULATED alert1. 실차 경로 취득/지도 링크 매핑 미검증 |
| 부분 구현 | 뉴스/TourAPI, 팝업, AI | 공식 스키마 어댑터/수동 입력/LLMProvider는 있으나 인증 실수신·실제 등록·실제 학교 AI는 미확인. 현재 뉴스/TourAPI 키 없음 |
| 미구현/미검증 | 실제 자동차 이동시간/실차 경로·TTS/학교 AI/ITS | Routing은 인터페이스와 fixture뿐. 학교 endpoint 미제공. ITS 미구현. 앱/SDK 실행 증거 없음 |

실제 HTTP 재검증: no-navigation LIVE 화면1/일반큐1/alert0, MOCK+수동DEMO 화면3/큐5/alert1, MIXED+수동DEMO 화면3/큐6/alert1. 별도 수동 SEOUL_TOPIS 입력에서 실제 교통 alert1 확인. 모두 설명 ai_mode=MOCK입니다. 이 기록은 실차 연결/재생 완료를 뜻하지 않습니다.

유효성 수정: feed는 오래된/해제/미래 교통정보를 이미 제외했으나 detail의 tts_eligible와 explain이 이를 놓쳤습니다. 같은 규칙을 공유하여 상세 음성 자격 false, 설명409로 일치시켰습니다. 유효한 상세 조회와 권리 미확인 뉴스403은 유지합니다.

## 저장소

- 기존 Private `Notice-Me/notice-me`를 사용했습니다. 새 Organization/Repository는 만들지 않았습니다.
- 초기 GitHub CLI 인증 및 권한 확인/clone 완료. 초기에는 연결 플러그인이 404였지만 이번 재검증에서는 연결 도구로 PR #1을 읽었고 CLI 조회도 성공했습니다.
- 최초 초기화 커밋 **7346168**만 main에 push했습니다. 이후 모든 서버 변경은 **feat/server-content-feed**에 있습니다.
- 기능 변경은 PR 검토 대상이며 main 병합/auto-merge는 실행하지 않습니다. 차량 앱 담당자는 이 기능 브랜치의 계약/OpenAPI를 확인하세요.
- 기존 신청서/동의서와 개인정보는 저장소 밖 원위치에 보존하고 업로드하지 않았습니다.

## 초기 구현 및 실제 검증 기록 (최신 분류는 위 표)

| 기능 | 상태 | 실제 확인 |
|---|---|---|
| FastAPI 4 endpoints | 구현 | health/feed/detail/explain, 실제 Uvicorn HTTP 200 |
| SQLite | 구현 | 소스 metadata upsert/재조회, 재시작 보존, 모드 격리. 위치/경로/질문 이력 저장 안 함 |
| 서울시 문화행사 | 실호출 성공 | sample 5건 수집. LIVE 행사 이동시간이 미검증이므로 추천 제외 |
| 서울시 도시데이터 | 실호출 성공 | POI009 날씨 LIFE 1건. 생활/날씨 관심사 요청에서 화면/음성 큐 응답 |
| 서울시 돌발 | 실호출 성공 | 원본4/정규화4건. 같은 SEOUL_TOPIS link와 유효성 일치 시 우선 alerts |
| TOP3 / 전체 큐 | 구현 | 별도 생성. 실제 MIXED HTTP에서 top3=3, queue=6. fixture와 실자료 표시 구분 |
| 긴급 우선순위 | 구현 | 실제 교통정보+수동 테스트 경로 링크에서 alert=1. Mock은 SIMULATED 표시. 실제 차량 경로를 읽은 검증은 아님 |
| 만료·중복·관심사·점수근거 | 구현 | 규칙별 테스트. 교통처럼 공통 데이터셋 URL인 별개 레코드는 보존 |
| 권리 검사 | 구현 | 근거 없는 뉴스의 TTS/요약/설명 차단. 별도 뉴스 라이선스 확보는 안 됨 |
| FreeNewsAPI | 공식 스키마 기반 어댑터, 실검색 미검증 | 키 없음. 무인증 HTTP401. 관심사 검색의 실제 기사 수/중복률 미측정 |
| The News API / GNews 비교 | 검증 스크립트 | 키 없음. 각각 HTTP401/400. GNews 응답은 키 미전송 명시. 24h/7d 통계는 null |
| TourAPI | 공식 스키마 기반 어댑터, 실수신 미검증 | 키 없음. 무인증 HTTP401. 행사별 홈페이지 상세 보강 미구현 |
| 국가교통정보센터 | 미구현/미호출 | 상세 공식 문서 연결 실패와 키 부재. 과거 URL 추측 구현 안 함 |
| 팝업 | 수동 공식 확인 입력 모듈 구현 | 실제 등록0. 자동 발견/크롤러 없음. confirmed=false 템플릿은 추천 제외 |
| LLMProvider | 인터페이스+deterministic mock | classify/summarize/explain. 실제 AI 응답 없음, ai_mode=MOCK |
| 자동차 이동시간 | 인터페이스만 | LIVE UNVERIFIED. MOCK에만 SIMULATED25분. 실제 길찾기/지오코딩 연동 없음 |
| Pleos 차량 앱/SDK/TTS 재생 | 팀원 영역, 미검증 | 서버 JSON 제공까지. GPS/내비/ETA/CarUxRestrictions/오디오 포커스/미디어 제어 실제 연동 필요 |

실제 호출은 [API_VALIDATION_RESULTS.json](API_VALIDATION_RESULTS.json), HTTP 응답 검증은 [HTTP_SMOKE_RESULTS.json](HTTP_SMOKE_RESULTS.json), 샘플 응답은 [examples](examples) 참조. 스냅샷 시각 이후에는 만료되거나 원천 자료가 바뀝니다. 현재 API 성공 여부는 재수집해 확인하세요.

## 초기 테스트 기록 (49개, 최신은 64개)

Windows / Python 3.11.9, [고정 의존성](../server/requirements.lock). 최종 기능 검증: **pytest 49 passed**, Ruff check/format 통과, pip check 의존성 충돌 없음. pytest에는 httpx 기반 TestClient에 관한 상위 Starlette의 deprecation warning 1건이 있으며 실패는 아닙니다.

검증 범위: 뉴스 URL/제목 중복, 서로 다른 사건 보존, 만료/미래/미검증 제외, 관심사 필수/지역과 무관한 관심사 뉴스, 목적지 관련성·점수 합, TOP3≤3, 큐>3 독립성, ETA 예산, 긴급 순서/route namespace/오래된 정보 제외, TTS 권리, API 401/403/429/500/timeout/잘못된 JSON/HTTP200 내부 오류, 실제 XML 소문자·HHMM, 일자·좌표 필드, DB 재조회, 팝업 확인 조건, AI의 근거 범위, 모드 격리·오류 입력. pytest의 외부 제공자는 MockTransport이며 실제 호출 보고서와 구분합니다.

HTTP smoke: live/mixed의 feed/detail/explain, rights/mode/queue 검증. 실제 LIVE 스냅샷은 top3=1, queue=1, alert=1; MIXED는 top3=3, queue=6, alert=1. `route_context=manually supplied test link`이며 실제 주행/내비 수집 성공을 의미하지 않습니다. 설명은 실자료에서도 AI가 MOCK입니다.

## 11/15 MVP 우선순위와 완료 기준

| 우선순위/목표일 | 작업 | 완료 기준과 담당 |
|---|---|---|
| P0 / 11/11~12 | **다음 최우선: 팀원 기기에서 HTTP 연결** | 서버가 LAN에서 실행, 팀원이 health→feed→detail→explain 호출. 서버/앱 버전·실제 기기/에뮬레이터 정보와 응답 상태 기록. localhost 검사만으로 완료하지 않음 |
| P0 / 11/12~13 | 앱 화면·TTS 최소 흐름 | top3 카드, queue/alerts 순서, 사용자 재생/다음/다시, 데이터 모드 표시. 앱 담당이 실제 TTS 재생 및 주행 UX/오디오 포커스 확인. 서버는 계약/오류 재현 지원 |
| P0 / 11/13 | 실제 공공자료 수집→응답 재현 | 시연 직전 수동 ingest, 유효 날씨 등 적어도 한 실제 소스의 JSON 제공. 만료/빈 데이터/소스 오류를 표시. 재수집 명령과 유효기간은 연동 안내에 기록 |
| P1 / 11/13~14 | 뉴스 인증·콘텐츠 확장 | FreeNewsAPI 무료 키를 본인이 발급해 로컬 .env에 설정, 24h/7d 검색 재검증. 권리 근거 없으면 뉴스 TTS 계속 차단. TourAPI/서울 정식 키의 실제 수신과 조건 확인 |
| P1 / 11/14 | 실제 경로·이동시간 | 무료 계정 조건/공식 schema/차량 경로 권한과 링크 매핑을 확인한 경우만 연결. 확보 전 LIVE 행사 제외, DEMO는 SIMULATED 유지 |
| P0 / 11/15 | 재현 가능한 MVP 시연 | 실제 공공정보 흐름과 명시적 모의 시연을 구분, 앱 연결·음성 재생 증거 확보. 미연동 기능을 완료로 발표하지 않음 |

학교 AI, 자동 팝업 발견, ITS 추가 소스, 전체 pagination/자동 스케줄러는 이 최소 시연의 선행조건으로 두지 않습니다. 원래의 전체 기획(실제 관심사 뉴스·60분 행사·실차 경로 등)을 완료했다는 의미는 아닙니다. 뉴스/행사까지 실자료로 포함하려면 인증·권리·라우팅이 여전히 필요합니다. `LLMProvider`는 공식 endpoint/인증/응답 문서를 받은 뒤 연결합니다.

개발 시연 서버는 인증/TLS/외부 배포/운영 모니터링을 아직 제공하지 않습니다. 고정 샘플 범위·단순 키워드 분류·표본 중복률은 실제 서비스 품질 검증을 대체하지 않습니다. 뉴스 전체 페이지 건수 측정, 실제 행사 경로시간, 자동 팝업 발견, 음성 재생 및 차량 안전 UX는 완료 목록에 넣지 않습니다.
