# 실제 날씨·내비 문맥 인수 — 2026-11-13 KST

## 기준과 협업

서버는 [PR #6](https://github.com/Notice-Me/notice-me/pull/6) `1f86b95`의 별도 실행본, 앱은 최신 main `5664368`에서 만든 `feat/vehicle-live-weather-context`, 최종0.3.3/versionCode8이다. main의 팀원 NaviHelper 3.0.5·현재 위치/목적지/ETA·15초 갱신을 재사용했다. 서버/앱은 별도 feature PR이며 승인 전 병합하지 않는다. 두 PR은 main의 서로 다른 위치에 문서를 추가해 중복 수정을 줄였다.

## 실제 실행 결과

Windows11의 기존 Pleos Connect2.1 / API34 x86_64 AVD, Pleos ON_DEVICE TTS3.3.1을 사용했다. 기본 내비 서비스에서 현재 위치 좌표/지역명과 경로 미사용 상태를 실제 수신했다. 위치/경로 이력은 GitHub에 올리지 않는다. 서버의 실제 feed 요청200과 앱의 내비 지역 표시를 확인했다. 경로 전체/도로 링크를 읽거나 만들지 않았다. 계정의 실제 GPS/실차 검증을 뜻하지 않는다.

실제 seoul_city1회 수집 자료: POI009 광화문·덕수궁, 11/13 00:00 KST 관측11.5도, 만료01:00 KST. LIVE TOP3=날씨1+뉴스 metadata2, 음성 큐=날씨1. 앱에 LIVE·고정 관측 지역·관측/만료 KST·출처·원문 링크와 읽기 전용/추천 제외 안내를 표시했다. 내비의 현재 위치와 고정 날씨 지역이 달라도 목적지 날씨로 바꾸어 안내하지 않는다.

실제 `health→feed→detail` 요청200, 앱 PID의 Pleos `doSpeak` 문장과 서버 detail.brief가 정확히 일치했다. 사용자가 **“날씨 안내가 들렸음”**으로 실제 청취 확인했다. 하드코딩 예문이나 일반 Android TTS가 아니다. LIVE 재생·패스(남은 날씨가 없으면 종료)·다시 듣기·중단을 기기에서 확인했다. 잡음 품질 개선은 사용자 결정으로P2이며 해결했다고 기록하지 않는다.

안전성 실기기 시험은 원본이 아닌 소유한 시연 DB 사본에서만 수행했다. 날씨 expires_at을 잠시 과거로 바꾸고 다시 듣기를 누르니 재생 불가/최신 날씨 없음 안내, 새 TTS 호출0회를 확인했다. 원래 행을 정확히 복원했다. 서버를 종료하고 새로고침하니 연결 실패/카드 제거, 새 TTS 호출0회였다. 뉴스는 화면에 남아도 음성 큐에 들어가지 않았다. LIVE 이후 같은 주소의 별도 MOCK 서버로 바꿔 모의 표시·TOP3·패스/다시/중단을 다시 확인했다. 앱 새로고침은 외부 수집을 일으키지 않는다.

## 목적지·ETA 검증 경계

현재 위치/경로 미사용은 실제 기기 확인. 00:38 KST 사용자가 기본 내비에서 목적지와 안내를 직접 설정한 뒤 별도 SDK 조회에서 ROUTE_GUIDING·유효 목적지 좌표·ETA를 수신했다. 00:39 최신 앱 새로고침에서 목적지·남은 시간·음성 큐1 표시을 확인했고 실제 서버 feed200 요청에 navigation_active=true, 목적지 좌표 쌍·eta_minutes가 포함됐다. 개인 목적지 이름/좌표·경로는 이 기록에 보관하지 않는다. 기본 내비의 안내 종료 후 SDK SAFE_GUIDING/유효 목적지 없음, 앱 새 조회의 경로 미사용·목적지/ETA 제거 요청을 확인했다. 취소 직후 이전 표시가 남은 구간이 있어 즉각 반영 지연은 측정 완료로 보지 않는다. 실제 목적지 변경/주행 중 ETA 변화는 미검증이며, 오래된 콜백·미래 콜백·잘못된 좌표는 단위 테스트로 확인했다.

기본 내비에서 영문 목적지 검색은 결과가 없었다. 저장소 밖 별도 instrumentation에서 [공식 requestRoute 예제](https://document.pleos.ai/docs/pleos-only/connect-sdk-pleos/NaviHelper/destinations)를 실행했으나 `NAVI_ROUTE_SEARCH` 권한이 없어 SecurityException으로 검증 프로세스가 종료됐다. 제품 앱의 경로 조회 권한 `NAVI_ROUTE`는 정상이며, 이 실패를 앱의 기존 위치 조회 실패나 목적지 경로 생성 성공으로 기록하지 않는다. 권한을 임의 추가·grant하거나 보안 설정을 변경하지 않았다. 사용자가 기본 내비에서 설정한 경로를 읽는 방식으로 추가 검증할 수 있다.

공식 [NaviHelper 소개](https://document.pleos.ai/docs/pleos-only/connect-sdk-pleos/NaviHelper/intro)는 콜백이 Navigation 앱 구현·상태에 따라 달라진다고 명시한다. SDK3.0.5의 실제 navi-data 클래스를 검사했으며 CurrentLocationInfo에는 원천 GPS 관측 timestamp가 없다. 추가한 receivedAt/30초 검사는 앱이 수신한 콜백 재사용 한계이지 GPS 원천 신선도 보증이 아니다. 경로 미사용·경로 정보 미수신·모의 주행 상태를 구분하며, 수신 실패는 수동 좌표 사용으로 표시한다. 목적지 ETA는 각 행사장 자동차 이동시간과 다르다.

## 자동 검사와 환경 실패

- 최신 앱 Pleos/standard APK 빌드 성공.
- 두 flavor 각각26개 테스트 통과(총52회, 각 HTTP/JSON7 + Controller13 + LIVE 정책5 + 실제 로컬 MOCK HTTP1), 실패·오류·skip0. 이 중 HTTP 통합은 JVM이며 실제 기기 증거와 구분한다.
- 현재 checkout의 개인 local.properties는 이전 환경 구성의 Windows 경로 escape 오류가 남아 있다. 이를 덮어쓰지 않고 추적 소스/변경 소스만 별도 ASCII 경로로 복사해 Lint를 실행했다. 두 flavor 오류0, Pleos 경고12/standard4. 대상API·아이콘/백업·전이 네이티브16KB 정렬 등 경고는 남아 있다. SDK를 임의 교체하지 않았다.
- 첫 emulator 실행은 검은 화면/화면 갱신 문제와 car_service dump timeout이 있었다. AVD 삭제·설정 변경 없이 종료 후 보이는 창으로 cold start해 회복했다. 이 관측만으로 근본 원인을 확정하지 않는다.
- 에뮬레이터 표시 timezone은 America/Los_Angeles지만 UTC 시계는 서버와 맞았다. 앱의 원천 시각은 명시적 KST로 표시하며 개인 timezone을 바꾸지 않았다.

## 권리·범위와 다음 작업

[FreeNews 공식 약관](https://www.freenewsapi.io/terms.php)을11/13 재확인했다(표시 갱신11/12). 연구/개발/대시보드 등 이용과 원저작권자 소유, 원문 대체 재배포 금지를 확인했다. 현재 화면은 제목·출처·발행시각·원문 링크 metadata만이며 원문·임의 요약·음성은 제공하지 않는다. 앱은 NEWS brief를 표시하지 않고, 서버가 잘못 허용해도 LIVE 뉴스/행사를 읽지 않는다. metadata 표시를 기사 AI/TTS 권리 확보로 확대하지 않는다. TourAPI 행사는 실제 길찾기 조건 미충족으로 계속 추천 제외다.

현재 위치/목적지/ETA의 실제 전달과 LIVE 고정지역 날씨 시연은 확인했다. 남은 것은 실제 목적지 변경/주행 중 ETA 변화 인수와 합동 시연 버전 고정이다. P1은 좌표별 날씨/실제 행사 라우팅·권리/자동 갱신이다. 공식 후보 조사와 수동 갱신 절차는 [서버 날씨 문서](https://github.com/Notice-Me/notice-me/blob/feat/server-live-weather-policy/docs/LIVE_WEATHER_DEMO.md)에 있다. 음성 잡음은P2다.

로컬 원본 .env/DB/개인 local.properties는 유지한다. AVD·앱 데이터 초기화 없이 APK install-r를 사용했다. 실제 위치·경로·키·뉴스 본문·원본 DB·단말 로그/스크린샷은 커밋하지 않는다. 수집은 별도 DB 사본이며 이후 재시연에는 원천 만료를 다시 확인해야 한다.

실제 뉴스 metadata에는 지역 좌표가 없어 목적지 지역 뉴스 추천 효과는 미검증이다. 목적지 우선 점수와 ETA 예산은 합성 단위 테스트로 확인했으며, 현재 실자료 시연은 관심사 뉴스와 고정 관측 날씨다. [개인 위치를 제외한 기계 판독 결과](2026-11-13-live-weather-vehicle.json).

## 최종 버전과 동시 협업 확인

초기0.3.2에서 사용자 청취·내비·안전성 시험 후, 팀원의 새 화면 PR #7이0.3.2/code7을 사용함을 발견했다. 중복을 피하려고 같은 기능을0.3.3/code8로 다시 빌드·두flavor각26테스트·설치했고, 최종 앱 PID에서 동일 LIVE brief와 onDone을 재확인했다. 사용자의 직접 청취 응답은 초기0.3.2의 동일 날씨 brief에 대한 것이다.

서버 PR #6은00:29 KST junnha가37d13aa로 main에 병합했다. 이번 작업자는 병합하지 않았다. 앱은5664368에서 시작해 게시 전 최신 main37d13aa로 rebase했다. PR #7의 UI 스타일을 덮어쓰거나 포함하지 않았다. 별도파일에 3-way 비교만 실행했으며 MainActivity.kt와 build.gradle.kts에 각각 충돌1구간이 있었다. 두 PR을 함께 반영할 때 팀원 UI와 고정지역/시각/출처/날씨전용 방어를 모두 유지하고 높은 최종 버전 번호로 조정하는 검토가 필요하다.

## PR #7의 main 반영 후 최종 통합 (00:59 KST)

게시 직후 원격을 다시 확인하니 junnha가 PR #7을00:49 KST main94de875에 병합해 PR #8에 충돌이 표시됐다. 이미 게시한 기능 브랜치에 최신 origin/main을 일반 merge하고 MainActivity/버전의 두 충돌만 수동 해결했다. main이나 팀원 브랜치를 수정하지 않았고 force push도 하지 않는다. 팀원 tripSummary/레이아웃/차콜 재생 영역·다음 버튼과 중복 모의표시 감소를 보존하고, 고정 지역/시각/링크/NEWS 표시 제한·LIVE 음성 방어를 함께 유지했다. 버전은0.3.3/code8이다. 앞 절의 PR #7 미포함/추가 검토는 최초 게시 시점 이력이다.

통합 APK 두 flavor 빌드·각26테스트·사본 Lint0오류를 재확인했다. 첫 재시험은 MOCK 전용 JVM 테스트의 URL을 LIVE8000으로 지정해 실패했으며, 테스트용 MOCK18080을 다시 켜고 올바른 URL로 재실행해52회 모두 통과했다. 테스트 기대나 정책을 약화하지 않았다. 최종 새 레이아웃을 실제 기기에서 확인하고 LIVE 날씨·다음(패스)/다시/중단, 동일 brief/onDone도 다시 확인했다. 이 결과가 최종 PR의 상태다. 수집 재호출은 없으며 관측00:00 자료는01:00에 만료된다. 재시연에는 새 관측을 수동 갱신해야 한다.
