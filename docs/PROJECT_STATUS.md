# Project status

## 2026-11-13 P0 실제 날씨 서버

최신 main `eaa5741`(팀원 NaviHelper/ETA PR #4 포함)을 기준으로 서버 기능 브랜치에서 작업했다. 실제 seoul_city1회로 광화문·덕수궁00:00 관측을 별도 DB 사본에 저장했고00:10 LIVE3/1/0 HTTP를 확인했다. 뉴스2건은 음성/설명 차단, 행사는 실제 이동시간 미검증 제외 유지. LIVE 음성은 날씨만, MOCK은 기존대로 유지한다. 서버 테스트·실기기 결과와 갱신 절차는 [날씨 시연](LIVE_WEATHER_DEMO.md). 앱의15초 요청은 외부 수집이 아니다. 자동 갱신/좌표별 날씨/실제 행사 라우팅·AI는 미완료. 잡음 개선은 사용자 결정으로P2다. 아래의 이전 상태·숫자는 당시 이력이다.

**2026-11-11 KST / feature 0.1.0.** 서버 프로토타입과 실제 서울시 수집→SQLite→HTTP 응답 경로가 작동합니다. 실제 뉴스와 학교 AI/차량 연동까지 완성된 상태는 아닙니다.

## 차량 앱 구현 추가 (2026-11-11, 23시대 KST)

`vehicle-app` 신규 Android 프로젝트에 health/feed 연결, TOP3 카드, Pleos ON_DEVICE/일반 Android TTS, 재생·패스·다시·중단을 구현했습니다. 두 debug APK 빌드, 앱 테스트 19개(실제 로컬 MOCK HTTP 포함), 서버 테스트 110개 통과. **기기 화면/음성 출력은 미검증**입니다. 설치된 일반 에뮬레이터가 APK 설치 전 SIGILL로 종료되었고 Pleos 이미지는 없습니다. 수동 위치·관심사 시연용이며 GPS/내비/주행 UX 연동은 남았습니다. [앱 실행](../vehicle-app/README.md), [검증과 잔여 경고](verification/2026-11-11-vehicle-app.md).

## 최신 TourAPI 검증 (2026-11-11, 23시대 KST)

사용자 인증 후 기존268/10/2/유효0 결과를 확인했습니다. [조사와 제외10행](TOURAPI_INVESTIGATION.md), [증거 JSON](verification/2026-11-11-tourapi-investigation.json). 공식 매뉴얼의 progresstype 기본값 선택안함까지 버리던 조건을 수정하고, KST 오늘~90일/수정일순/상한 있는 pagination을 적용했습니다.

최종 실제 HTTP200/SUCCESS, **2회 호출·raw77/total77·정규화/날짜 유효76(진행 중36/예정40)**. 온라인 상태1건은 의미 미확정으로 보류했습니다. 전체 조사 호출은 재조회1+첫 수집3+수정 후2=6회, 다른 제공자0회입니다. 첫 수집의 불필요한3페이지/SCHEMA_MISMATCH도 실패 이력으로 기록했고 마지막 numOfRows가 반환 건수인 경우를 수정했습니다. 계정의 현재 잔여량은 확인하지 않았습니다.

76건 모두 Type3/권리 미확인으로 brief 비움·음성/설명 차단을 유지합니다. **실제 자동차 이동시간 미검증이므로 LIVE 행사 추천0건**입니다. 실제 원천 수집→SQLite와 내부 ASGI 검사는 확인했으나 새 실차/길찾기/TTS 검증은 없습니다. 개별 원문 홈페이지·자동 갱신·전시 세부분류는 미구현입니다.

기존110 + Tour 회귀37, **pytest147 통과**. API/OpenAPI 계약 유지. 페이지별 관측/제외 사유를 DB에 보존하고 새 취소·만료·미확인 상태는 기존 자료를 삭제하지 않고 격리합니다. 최우선 P0는 여전히 앱 담당자의 Pleos 실제 연결/재생 확인입니다.

## 앞선 차량 연동 준비 검증 (2026-11-11, 20시대 KST)

첫 대상은 사용자 확인에 따라 **Pleos SDK 에뮬레이터·실차**입니다. 서버 HTTP 준비와 실제 기기 연결을 분리합니다. 실행/주소/필드는 [차량 연동 안내](VEHICLE_INTEGRATION.md), 팀원이 채울 완료 판정은 [연동 확인표](VEHICLE_ACCEPTANCE.md), 실제 측정은 [증거 JSON](verification/2026-11-11-vehicle-handoff.json)입니다.

| 실제 Uvicorn HTTP 시나리오 | TOP3 | 일반 음성 큐 | alerts | 결과 |
|---|---:|---:|---:|---|
| MOCK / 내비 없음 | 3 | 5 | 0 | 통과 |
| MOCK / 수동 DEMO 링크 | 3 | 5 | 1 | 통과, 모의 긴급정보 |
| LIVE / 내비 없음 | 3 | 1 | 0 | 통과, 실제 뉴스2건은 음성 불가 |
| MIXED / 내비 없음 | 3 | 6 | 0 | 통과 |
| MIXED / 수동 DEMO 링크 | 3 | 6 | 1 | 통과, 모의 긴급정보 |

health/feed/detail/explain200, 권리 미확인 뉴스의 상세 음성 불가/설명403, 404/422, OpenAPI 명세 일치를 확인했습니다. LIVE의 재생 가능 항목은 서울시 실제 날씨1건입니다. 원천 날씨만 1회 선택 갱신했고 FreeNews 및 다른 공공 API 추가 호출은0회입니다. HTTP 피드 검사는 외부 제공자를 호출하지 않습니다. 콘텐츠와 설명의 모드는 별개이며 설명 ai_mode는 계속 MOCK입니다.

서버 PC→자신의 LAN 주소에서 health200을 확인했지만 **팀원 기기·Pleos 앱·실차·TTS 출력은 모두 미검증**입니다. 임시 검증 서버는 종료했으므로 상시 실행 주소가 준비된 것은 아닙니다. 팀원 접속 시험 시간에 서버 실행과 네트워크 도달성을 확인해야 합니다. 외부망 공개 배포/인증/TLS는 없습니다.

기존99 + 신규11, **pytest110 통과**. 검사 도구가 alerts의 권리 근거/유효성/교통 freshness, 누락 없는 긴급 우선 재생 순서, LIVE 권리 미확인 뉴스도 검사합니다. 검사 보고서에 SERVER_HTTP_ONLY/SDK=false/TTS=false를 명시합니다. 200 빈 피드/화면 전용 뉴스만 있는 경우를 TTS 준비 완료로 판정하지 않습니다. 계약 v1의 URL·JSON·권리 정책은 유지했습니다.

## FreeNews 검증 이력 (2026-11-11, 19시대 KST)

사용자의 키 로딩과 실제 인증 요청을 확인했습니다. [조사 결과](FREENEWS_INVESTIGATION.md)와 [증거 JSON](verification/2026-11-11-freenews-investigation.json)을 참고하세요. 원본 검증은 과학 IT24h=0건, 예술24h=5건, 예술168h=첫10건/추가 페이지 있음입니다. 애니메이션24h500은 재현했으나 내부 원인은 미확정입니다. 과학 IT168h는 대기를 늘린 동일 window에서10.844초 후0건을 받았고, 과거 TIMEOUT의 단계는 알 수 없습니다.

목록 조사3회+받아 둔 목록의 상세2회로 추가 호출5회만 수행했습니다. metadata5건 보존, 원문 URL이 있는 실제 뉴스2건 저장. ASGI TestClient에서 화면2건/뉴스 음성0건/설명403·403 확인. LICENSE_UNVERIFIED를 유지했고 실차/TTS를 실행하지 않았습니다. 원본 사용자 JSON은 그대로 보존했습니다.

수집기에는 read20초/연결5초/HTTP시도 전체30초, 선택 오류에 최대1회 재시도, 기본 뉴스 시도 예산20회, 검색별 DB/JSON 보존을 추가했습니다. 기존64+새35, **pytest99 통과**, Ruff/format/pip check/compileall 통과, 상위 TestClient 경고1건. 차량 API와 OpenAPI 계약은 유지합니다. 뉴스 인증/일부수신은 이제 확인됐지만500·정확한 전체 건수·재배포 권리는 해결되지 않았습니다.

## 앞선 재검증 기록 (2026-11-11, 18시대 KST)

시작 커밋 d8f5c96에서 기존 **49 passed**를 재현했습니다. 검토 중 상세/설명이 오래된 교통정보를 허용하는 문제를 재현하여 fdd7e2f에서 수정했고, 응답 계약/차량 연결 도구를 보강한 최종 작업 트리에서 **64 passed**를 확인했습니다. Ruff check/format, pip check, compileall 통과. 상위 Starlette TestClient deprecation warning 1건은 남아 있습니다.

[18시대 측정 보고서](verification/2026-11-11-revalidation.json)는 당시의 증거입니다. 최신 차량 준비 결과는 문서 맨 위를 참고하세요. 기존 API_VALIDATION_RESULTS/HTTP_SMOKE_RESULTS/examples도 초기 시각의 증거로 보존했습니다.

기술·학습 기록도 [기술 선택 근거](TECH_DECISIONS.md), [날짜별 개발 로그](DEVELOPMENT_LOG.md), [학습/회고](LESSONS_LEARNED.md)로 누적합니다. 구현 코드·측정·문서상 비교·미수행 실험을 구분하며 이후 작업도 AGENTS의 기록 지침을 따릅니다.

## 현재 구현 분류 (23시대 검토 기준)

| 분류 | 항목 | 근거/범위 |
|---|---|---|
| 구현 완료 | 4개 endpoint와 응답 타입, SQLite, 규칙 추천/TOP3/별도 큐, 권리 차단 | pytest147 및 앞선 실제 HTTP5시나리오. OpenAPI 네 성공 응답 타입/저장 명세 일치, 큐·상세·설명 유효성 검사 |
| 구현 완료 | 서버 HTTP 계약 검사와 앱 인계 안내 | DB/키 없는 check_vehicle_api.py, 뉴스/긴급 권리·재생 순서 검사. Pleos 실제 연결은 미검증 |
| 부분 구현 | 공공 데이터 수집 | 이번 날씨1건 실제 갱신. 앞선 행사5·교통5 수신은 당시 이력이며 현재 신선도를 뜻하지 않음. sample/첫 페이지, 자동 갱신 없음 |
| 부분 구현 | 긴급 경로 처리 | 과거 수동 SEOUL_TOPIS 링크에서 LIVE alert1 확인, 이번 DEMO에서 SIMULATED alert1. 실차 경로 취득/지도 링크 매핑 미검증 |
| 부분 구현 | FreeNews | 인증·일부 실제 metadata/URL 수신 확인. 실제 뉴스2건이 LIVE 화면에 있지만 권리 미확인으로 음성/설명 차단. 500 내부 원인/전체 건수 미확정 |
| 부분 구현 | TourAPI | 실제 날짜 유효76건 수집/저장. 90일/페이지·시도 예산 범위. 권리·이동시간 미검증으로 추천/TTS 제외, 원문 홈페이지·자동 갱신 미구현 |
| 부분 구현 | 팝업, AI | 수동 입력/LLMProvider 구현. 실제 팝업 등록·학교 AI는 미검증 |
| 미구현/미검증 | 실제 자동차 이동시간/실차 경로·TTS/학교 AI/ITS | Routing은 인터페이스와 fixture뿐. 학교 endpoint 미제공. ITS 미구현. 앱/SDK 실행 증거 없음 |

18시대 HTTP 이력: no-navigation LIVE 화면1/일반큐1/alert0, MOCK+수동DEMO 화면3/큐5/alert1, MIXED+수동DEMO 화면3/큐6/alert1. 별도 수동 SEOUL_TOPIS 입력에서 실제 교통 alert1 확인. 모두 설명 ai_mode=MOCK입니다. 현재 LIVE 화면3건과 다른 것은 이후 실제 뉴스2건이 추가됐기 때문입니다. 이 기록은 실차 연결/재생 완료를 뜻하지 않습니다.

유효성 수정: feed는 오래된/해제/미래 교통정보를 이미 제외했으나 detail의 tts_eligible와 explain이 이를 놓쳤습니다. 같은 규칙을 공유하여 상세 음성 자격 false, 설명409로 일치시켰습니다. 유효한 상세 조회와 권리 미확인 뉴스403은 유지합니다.

## 저장소

- 기존 Private `Notice-Me/notice-me`를 사용했습니다. 새 Organization/Repository는 만들지 않았습니다.
- 초기 GitHub CLI 인증 및 권한 확인/clone 완료. 초기에는 연결 플러그인이 404였지만 이번 재검증에서는 연결 도구로 PR #1을 읽었고 CLI 조회도 성공했습니다.
- 최초 초기화 커밋 **7346168**만 main에 push했습니다. 이후 모든 서버 변경은 **feat/server-content-feed**에 있습니다.
- 기능 변경은 PR 검토 대상이며 main 병합/auto-merge는 실행하지 않습니다. 차량 앱 담당자는 이 기능 브랜치의 계약/OpenAPI를 확인하세요.
- 기존 신청서/동의서와 개인정보는 저장소 밖 원위치에 보존하고 업로드하지 않았습니다.

## 초기 구현 및 실제 검증 이력 (현재 상태는 문서 상단)

아래는 최초49개 테스트 시점의 기록입니다. 당시 키 부재/자료 개수는 현재 설정·신선도를 나타내지 않습니다.

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
| FreeNewsAPI | 초기에는 공식 어댑터/실검색 미검증 | 당시 키 없음/무인증401. 이후 인증·일부 실수신 확인은 위19시대·최신 기록 참조 |
| The News API / GNews 비교 | 검증 스크립트 | 키 없음. 각각 HTTP401/400. GNews 응답은 키 미전송 명시. 24h/7d 통계는 null |
| TourAPI | 공식 스키마 기반 어댑터, 실수신 미검증 | 키 없음. 무인증 HTTP401. 행사별 홈페이지 상세 보강 미구현 |
| 국가교통정보센터 | 미구현/미호출 | 상세 공식 문서 연결 실패와 키 부재. 과거 URL 추측 구현 안 함 |
| 팝업 | 수동 공식 확인 입력 모듈 구현 | 실제 등록0. 자동 발견/크롤러 없음. confirmed=false 템플릿은 추천 제외 |
| LLMProvider | 인터페이스+deterministic mock | classify/summarize/explain. 실제 AI 응답 없음, ai_mode=MOCK |
| 자동차 이동시간 | 인터페이스만 | LIVE UNVERIFIED. MOCK에만 SIMULATED25분. 실제 길찾기/지오코딩 연동 없음 |
| Pleos 차량 앱/SDK/TTS 재생 | 팀원 영역, 미검증 | 서버 JSON 제공까지. GPS/내비/ETA/CarUxRestrictions/오디오 포커스/미디어 제어 실제 연동 필요 |

초기 실제 호출은 [API_VALIDATION_RESULTS.json](API_VALIDATION_RESULTS.json), 초기 HTTP 응답은 [HTTP_SMOKE_RESULTS.json](HTTP_SMOKE_RESULTS.json), 샘플은 [examples](examples) 참조. 스냅샷 이후에는 만료되거나 원천 자료가 바뀝니다. 재검증은 필요한 제공자만 선택 호출하고, 과거 성공을 현재 유효성으로 간주하지 않습니다.

## 초기 테스트 기록 (당시49개, 최신은147개)

Windows / Python 3.11.9, [고정 의존성](../server/requirements.lock). 최종 기능 검증: **pytest 49 passed**, Ruff check/format 통과, pip check 의존성 충돌 없음. pytest에는 httpx 기반 TestClient에 관한 상위 Starlette의 deprecation warning 1건이 있으며 실패는 아닙니다.

검증 범위: 뉴스 URL/제목 중복, 서로 다른 사건 보존, 만료/미래/미검증 제외, 관심사 필수/지역과 무관한 관심사 뉴스, 목적지 관련성·점수 합, TOP3≤3, 큐>3 독립성, ETA 예산, 긴급 순서/route namespace/오래된 정보 제외, TTS 권리, API 401/403/429/500/timeout/잘못된 JSON/HTTP200 내부 오류, 실제 XML 소문자·HHMM, 일자·좌표 필드, DB 재조회, 팝업 확인 조건, AI의 근거 범위, 모드 격리·오류 입력. pytest의 외부 제공자는 MockTransport이며 실제 호출 보고서와 구분합니다.

HTTP smoke: live/mixed의 feed/detail/explain, rights/mode/queue 검증. 실제 LIVE 스냅샷은 top3=1, queue=1, alert=1; MIXED는 top3=3, queue=6, alert=1. `route_context=manually supplied test link`이며 실제 주행/내비 수집 성공을 의미하지 않습니다. 설명은 실자료에서도 AI가 MOCK입니다.

## 11/15 MVP 우선순위와 완료 기준

| 우선순위/목표일 | 작업 | 완료 기준과 담당 |
|---|---|---|
| P0 / 11/11~12 | **다음 최우선: Pleos 에뮬레이터/기기에서 HTTP 연결** | 실행 PC/서버 주소를 합의하고 앱 코드로 health→feed→detail 호출. 서버/앱·기기/SDK 버전과 실제 HTTP 결과 기록. PC 검사만으로 완료하지 않음 |
| P0 / 11/12~13 | 앱 화면·TTS 최소 흐름 | top3 카드, queue/alerts 순서, 사용자 재생/다음/다시, 데이터 모드 표시. 앱 담당이 실제 TTS 재생 및 주행 UX/오디오 포커스 확인. 서버는 계약/오류 재현 지원 |
| P0 / 11/13 | 실제 공공자료 수집→응답 재현 | 시연 직전 ingest --public-provider seoul_city, 유효 날씨 등 적어도 한 실제 소스의 JSON 제공. 만료/빈 데이터/소스 오류 표시. 서버 HTTP 경로는 재현했고 앱 수신·재생은 확인해야 함 |
| P1 / 11/13~14 | 뉴스 오류·권리·콘텐츠 확장 | FreeNews 인증/일부 metadata, TourAPI 날짜 유효76건 수신 확인. 애니메이션500/뉴스 전체 건수·권리 미확정. TourAPI 권리/실제 라우팅과 서울 정식 키 조건은 추가 확인 |
| P1 / 11/14 | 실제 경로·이동시간 | 무료 계정 조건/공식 schema/차량 경로 권한과 링크 매핑을 확인한 경우만 연결. 확보 전 LIVE 행사 제외, DEMO는 SIMULATED 유지 |
| P0 / 11/15 | 재현 가능한 MVP 시연 | 실제 공공정보 흐름과 명시적 모의 시연을 구분, 앱 연결·음성 재생 증거 확보. 미연동 기능을 완료로 발표하지 않음 |

학교 AI, 자동 팝업 발견, ITS 추가 소스, 전체 pagination/자동 스케줄러는 이 최소 시연의 선행조건으로 두지 않습니다. 원래의 전체 기획(실제 관심사 뉴스·60분 행사·실차 경로 등)을 완료했다는 의미는 아닙니다. 뉴스/행사까지 실자료로 포함하려면 인증·권리·라우팅이 여전히 필요합니다. `LLMProvider`는 공식 endpoint/인증/응답 문서를 받은 뒤 연결합니다.

개발 시연 서버는 인증/TLS/외부 배포/운영 모니터링을 아직 제공하지 않습니다. 고정 샘플 범위·단순 키워드 분류·표본 중복률은 실제 서비스 품질 검증을 대체하지 않습니다. 뉴스 전체 페이지 건수 측정, 실제 행사 경로시간, 자동 팝업 발견, 음성 재생 및 차량 안전 UX는 완료 목록에 넣지 않습니다.

## 2026-11-13 — 내비 문맥과 LIVE 날씨 기기 검증

최신 main5664368에서 feat/vehicle-live-weather-context로 작업했다. 팀원 NaviHelper/15초 갱신을 유지하고 고정 날씨 지역·관측/만료·LIVE/MOCK·출처/링크·제외 안내와 LIVE 날씨 전용 방어를 보강했다. 두 APK/각26개 테스트, 소스 사본 Lint 오류0. 실제 Pleos에서 현재 위치·경로 미사용, 사용자가 설정한 실제 안내 경로의 목적지/ETA→서버feed200, LIVE 날씨→Pleos brief 일치·사용자 청취, 만료/연결 실패 신규TTS0, MOCK 제어를 확인했다. 이번 기록은 기존 미검증 이력을 대체하지 않고 최신 관측으로 추가한다. 경로 전체/실차·GPS 원천시각·좌표별 날씨·행사 라우팅·학교AI는 미검증/미연결. 상세와 남은 인수는 [2026-11-13 기기 검증](verification/2026-11-13-live-weather-vehicle.md). 잡음P2 유지.


2026-11-13 최종 보완: 원격 main에 외부 병합된 UI PR #7(94de875)을 기능 브랜치에 반영하고 두 충돌을 해결했다. 팀원 레이아웃과 날씨·권리 방어를 보존했으며 두 APK/각26테스트·Lint0오류·실제 기기 재생 제어와 brief 일치를 재검증했다. MOCK 테스트 URL 오지정 실패와 수정도 [최종 인수 기록](verification/2026-11-13-live-weather-vehicle.md)에 남겼다. main/타인 브랜치 push·force push·PR 병합은 수행하지 않았다.
