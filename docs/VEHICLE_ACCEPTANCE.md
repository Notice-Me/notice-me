# Pleos 연동 확인표

2026-11-11. 이 문서는 **앞으로 팀원이 실행한 결과를 채울 양식**입니다. 아래 앱/기기 단계는 모두 NOT_RUN이며 서버 단독 결과로 완료 처리하지 않습니다. [서버 실행·주소·규격](VEHICLE_INTEGRATION.md), [API 계약](API_CONTRACT.md), [서버 측 실제 HTTP 증거](verification/2026-11-11-vehicle-handoff.json)를 사용합니다.

## 첫 연결에서 합의할 값

| 항목 | 기록할 값 |
|---|---|
| 서버 | feat/server-content-feed의 커밋, 실행 PC, 포트, configured_data_mode |
| 앱 | 앱 브랜치/커밋, APK 빌드 타입, target/min SDK, Pleos SDK 버전 |
| 기기 | Pleos AVD 이미지/Android API 또는 실차/Devbox 종류. 개인 식별번호 제외 |
| 주소 | 서버와 같은 PC의 표준 AVD면 10.0.2.2 후보, 다른 PC/실차면 서버의 도달 가능한 LAN 주소 |
| 입력 | 첫 재현은 문서의 고정 테스트 좌표/관심사. 실제 GPS·내비와 구분 |
| TTS | 선택 모드, 한국어 엔진/locale, 권한·초기화·오디오 이벤트 결과 |

LAN 주소 등 로컬 접속값은 팀 내 로컬 기록에만 넣고 공개/저장소 보고서에는 환경 종류만 남깁니다. 서버/API 키를 차량 앱에 복사하지 않습니다. 다른 장소의 PC에서 접속할 외부 서버 주소는 아직 없습니다.

## 실행 순서와 완료 기준

| 단계 | 실행·기대 동작 | 담당 | 실제 결과 |
|---|---|---|---|
| A | 서버 실행, 팀원 PC에서 TCP8000 및 health200. 서버와 에뮬레이터가 같은 PC면 PC health부터 확인 | 서버+앱 | NOT_RUN |
| B | **앱의 HTTP 클라이언트**로 health200. PC curl/브라우저 성공만으로 대체하지 않음 | 앱 | NOT_RUN |
| C | MOCK feed200, top3 0~3 카드, 빈 값/null 허용, MOCK/SIMULATED 표시 | 앱 | NOT_RUN |
| D | playback_order를 queue/alerts의 id로 연결. 긴급 먼저, top3와 큐를 따로 관리 | 앱 | NOT_RUN |
| E | 재생 전 최신 feed·detail 검사, TTS_ALLOWED/근거/tts_eligible/유효성 충족 항목의 brief만 전달 | 앱 | NOT_RUN |
| F | 실제 TTS 권한·초기화·언어·합성/재생 이벤트 성공 및 음성 출력 확인 | 앱 | NOT_RUN |
| G | 사용자 중단/다음/다시와 오디오 포커스·주행 UX 제약 처리 | 앱 | NOT_RUN |
| H | LIVE 실제 날씨 카드/brief 수신 및 허용 콘텐츠 재생. 수집시각·만료·모드 기록 | 서버+앱 | NOT_RUN |
| I | MIXED에서 항목별 LIVE/MOCK 구분, 모의 긴급정보를 실제 사고라고 표시하지 않음 | 앱 | NOT_RUN |
| J | 권리 미확인 뉴스는 화면에 있어도 TTS 호출0회, 상세 tts_eligible=false, explain403 | 앱 | NOT_RUN |
| K | 404 항목 제거, 409/만료 상세의 false에서 재생 중단/재조회, 422 입력 수정, 연결 끊김·빈 큐 처리 | 앱 | NOT_RUN |

서버의 20시대 HTTP 검증은 MOCK 3/5/0, LIVE 3/1/0, MIXED 3/6/0(화면/일반 큐/alerts)이었습니다. DEMO 경로는 MOCK/MIXED alerts1입니다. 숫자는 당시 데이터이며 앱이 항상 같은 개수를 요구하면 안 됩니다. LIVE 화면의 실제 뉴스2건은 권리 미확인으로 TTS/설명에서 차단했습니다. **TTS_ALLOWED는 서버가 확인한 콘텐츠 자격이며 실제 오디오 출력 성공 표시는 아닙니다.**

## 서버와 앱의 남은 작업

| 서버 담당 | 앱 담당 |
|---|---|
| 시연 시간에 접근 가능한 주소/실행 유지, 원천 날씨 갱신과 만료 확인 | 기기에서 base URL/HTTP 권한·debug 설정 확인 |
| 계약·권리·유효성 유지, 오류 응답 재현 지원 | JSON DTO/null/시각 처리, top3/queue/alerts 매핑 |
| 실자료 부족·소스 오류/빈 피드의 diagnostics 제공 | TTS SDK 권한/초기화/모드/한국어 지원·실제 오디오 확인 |
| 향후 실제 라우팅·지도 링크 매핑, 스케줄러·운영 배포 | GPS/내비/ETA·경로 취득, 재생 제어/오디오 포커스/주행 UX |

학교 AI·뉴스 TTS 권리·실제 행사 이동시간·ITS는 첫 MOCK 카드→허용 brief TTS의 선행조건이 아닙니다. 이 항목들이 완료됐다는 뜻도 아닙니다.

## 결과를 남기는 형식

날짜/시간대, 서버·앱 커밋, 기기/SDK 버전, 시도한 주소의 종류, HTTP 상태, 모드/카드/큐 개수, TTS 모드·초기화/재생 결과, 오류 코드와 해결/미해결을 기록합니다. 화면 표시와 실제 오디오 재생은 각각 판정합니다. 인증키·원문 뉴스·사용자 위치/경로·기기 고유번호는 저장소에 기록하지 않습니다.

## 2026-11-11 앱 코드/빌드 사전검증 추가

[앱 검증 기록](verification/2026-11-11-vehicle-app.md)에 APK 빌드·클라이언트 테스트·로컬 서버 HTTP 결과를 남겼습니다. 위 B~K의 **기기 실행 판정은 계속 NOT_RUN**입니다. 새 코드의 JVM 검증으로 해당 표를 PASS로 바꾸지 않았습니다.
