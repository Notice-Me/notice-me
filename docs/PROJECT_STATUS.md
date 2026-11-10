# Project status

**2026-11-11 KST / feature 0.1.0.** 서버 프로토타입과 실제 서울시 수집→SQLite→HTTP 응답 경로가 작동합니다. 실제 뉴스와 학교 AI/차량 연동까지 완성된 상태는 아닙니다.

## 저장소

- 기존 Private `Notice-Me/notice-me`를 사용했습니다. 새 Organization/Repository는 만들지 않았습니다.
- GitHub CLI 인증 및 read/write/admin 권한 확인, 빈 저장소 clone 완료. 연결 플러그인은 404여서 CLI 사용.
- 최초 초기화 커밋 **7346168**만 main에 push했습니다. 이후 모든 서버 변경은 **feat/server-content-feed**에 있습니다.
- 기능 변경은 PR 검토 대상이며 main 병합/auto-merge는 실행하지 않습니다. 차량 앱 담당자는 이 기능 브랜치의 계약/OpenAPI를 확인하세요.
- 기존 신청서/동의서와 개인정보는 저장소 밖 원위치에 보존하고 업로드하지 않았습니다.

## 구현 및 실제 검증

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

## 테스트

Windows / Python 3.11.9, [고정 의존성](../server/requirements.lock). 최종 기능 검증: **pytest 49 passed**, Ruff check/format 통과, pip check 의존성 충돌 없음. pytest에는 httpx 기반 TestClient에 관한 상위 Starlette의 deprecation warning 1건이 있으며 실패는 아닙니다.

검증 범위: 뉴스 URL/제목 중복, 서로 다른 사건 보존, 만료/미래/미검증 제외, 관심사 필수/지역과 무관한 관심사 뉴스, 목적지 관련성·점수 합, TOP3≤3, 큐>3 독립성, ETA 예산, 긴급 순서/route namespace/오래된 정보 제외, TTS 권리, API 401/403/429/500/timeout/잘못된 JSON/HTTP200 내부 오류, 실제 XML 소문자·HHMM, 일자·좌표 필드, DB 재조회, 팝업 확인 조건, AI의 근거 범위, 모드 격리·오류 입력. pytest의 외부 제공자는 MockTransport이며 실제 호출 보고서와 구분합니다.

HTTP smoke: live/mixed의 feed/detail/explain, rights/mode/queue 검증. 실제 LIVE 스냅샷은 top3=1, queue=1, alert=1; MIXED는 top3=3, queue=6, alert=1. `route_context=manually supplied test link`이며 실제 주행/내비 수집 성공을 의미하지 않습니다. 설명은 실자료에서도 AI가 MOCK입니다.

## 남은 작업과 11/15 우선순위

1. FreeNewsAPI 무료 키를 본인이 발급해 .env에 입력 → validate로 한국어/한국 corpus 및 3키워드의 24h/7d 표본·전체 통계 재확인. 뉴스 TTS는 별도 권리 확보 전 계속 차단.
2. 차량 팀원이 기능 브랜치의 API_CONTRACT/OpenAPI/example로 GPS→feed 카드/큐를 연동. MOCK/LIVE/MIXED와 SIMULATED/ai_mode 표시 유지.
3. 서울 키로 sample 범위 확대, TourAPI 활용신청 후 정상 수신과 취소/연기 enum·항목권리 검증. 자동 수집기는 현재 한 페이지 수집이며 전체 pagination/스케줄러는 없음.
4. 무료 범위에서 실제 자동차 이동시간 provider와 링크 체계 매핑 검증. 이전까지 LIVE 행사는 추천하지 않음. 영업시간/ETA 실제 TTS 길이와 재생 세션은 차량 연동 후 보강.
5. 학교 AI의 공식 endpoint/인증/응답 문서가 제공되면 LLMProvider 구현. 토큰만으로 endpoint를 추측하지 않음.

개발 시연 서버는 인증/TLS/외부 배포/운영 모니터링을 아직 제공하지 않습니다. 고정 샘플 범위·단순 키워드 분류·표본 중복률은 실제 서비스 품질 검증을 대체하지 않습니다. 뉴스 전체 페이지 건수 측정, 실제 행사 경로시간, 자동 팝업 발견, 음성 재생 및 차량 안전 UX는 완료 목록에 넣지 않습니다.
