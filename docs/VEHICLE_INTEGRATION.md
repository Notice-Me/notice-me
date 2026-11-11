# 차량 앱 연동 시작 안내

기준 브랜치 `feat/server-content-feed`, API v1. 첫 대상은 **Pleos SDK 에뮬레이터·실차**입니다. 2026-11-11 20시대 서버 HTTP 재검증은 [측정 JSON](verification/2026-11-11-vehicle-handoff.json), 팀원의 실제 실행·완료 판정은 [연동 확인표](VEHICLE_ACCEPTANCE.md)를 사용합니다. 서버 HTTP 성공과 Pleos 앱/SDK·오디오 재생 성공은 별도입니다.

## 1. 서버 실행

최초 clone이면 저장소 루트에서 `git switch feat/server-content-feed` 후 [README](../README.md)의 Python 설치 절차를 실행합니다. 이후 명령은 **server 폴더**에서 실행합니다. 기존 `.env`는 덮어쓰지 마세요.

```powershell
cd server
$env:NOTICE_DATA_MODE='mock'
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --no-access-log
```

모드 변수는 실행하는 PowerShell 창에만 적용됩니다. SQLite 위치는 기본 `server/data/notice_me.db`입니다. 피드 요청마다 외부 API를 호출하지 않습니다. mock/mixed 서버 시작 시 fixture를 갱신하고 모의 교통정보는 10분 뒤 제외됩니다. 모의 교통정보를 다시 시연할 때는 서버를 재시작합니다.

## 2. 앱에 넣을 주소

| 접속 환경 | base URL |
|---|---|
| 서버 PC에서 테스트 | `http://127.0.0.1:8000` |
| 서버와 같은 PC의 Android/Pleos AVD | 표준 Android AVD의 첫 후보 `http://10.0.2.2:8000`; Pleos 환경에서 health로 검증 |
| 팀원 PC의 에뮬레이터 → 다른 PC의 서버 | `http://<서버 PC의 LAN IPv4>:8000`; 10.0.2.2는 **팀원 PC 자신**을 가리킴 |
| 실차/Devbox → 접근 가능한 동일 네트워크의 서버 | `http://<서버 PC의 LAN IPv4>:8000`; 해당 장치의 네트워크 도달성 검증 필요 |

`0.0.0.0`은 서버의 수신 설정이며 앱의 접속 주소로 사용하지 않습니다. 실제 기기의 localhost는 그 기기 자신입니다. `ipconfig`로 서버 PC의 해당 네트워크 IPv4를 확인하고, `/api/v1/health`가 HTTP 200인지 먼저 검사하세요. 연결 실패 시 주소·동일 네트워크·포트·Windows 방화벽 허용 범위를 확인합니다. 이 작업에서 방화벽이나 외부 공개 설정을 자동 변경하지 않았습니다.

표준 에뮬레이터 주소의 근거는 [Android 공식 네트워크 주소 문서](https://developer.android.com/studio/run/emulator-networking-address)입니다. Pleos 배포 에뮬레이터가 같은 네트워크 구성을 쓰는지는 미검증이므로 해당 환경에서도 health 호출로 확인하세요.

Android 앱은 INTERNET 권한과 개발용 HTTP 허용 설정을 점검합니다. API 28 이상 대상에서는 기본적으로 평문 HTTP가 차단되므로 [공식 Network Security Configuration](https://developer.android.com/privacy-and-security/security-config)에 따라 **debug 빌드의 테스트 서버 주소에 한정해** 설정합니다. 프로젝트에 기존 networkSecurityConfig가 있으면 그 설정을 확인하고, 출시용 보안 설정을 일괄 완화하지 않습니다. 현재 서버는 개발 네트워크의 프로토타입으로 인증/TLS/공개 배포가 준비되지 않았습니다.

첫 에뮬레이터 시연은 팀원 PC에 서버를 함께 실행하면 기기 간 방화벽 변수를 줄일 수 있습니다. 팀원은 키를 공유받지 않아도 MOCK 서버를 실행할 수 있습니다. 서버 담당 PC를 공유할 때는 현재 LAN IPv4·포트·모드·브랜치/커밋·실행 시간을 팀원에게 전달하세요. 아직 외부망에서 접속할 배포 주소는 없습니다. 개발 서버를 실행하는 창은 연결 시험 동안 유지합니다.

팀원 PC PowerShell에서 먼저 아래 두 단계를 확인한 뒤 **에뮬레이터/실차의 앱 HTTP 코드로 같은 health를 호출**합니다. PC의 성공이 기기 성공을 대신하지 않습니다.

```powershell
$noticeServer = 'http://<서버 PC의 LAN IPv4>:8000' # 같은 PC의 PC 검사라면 127.0.0.1
Test-NetConnection -ComputerName '<서버 PC의 LAN IPv4>' -Port 8000
Invoke-RestMethod "$noticeServer/api/v1/health"
```

TCP 실패는 서버 미실행·잘못된 주소·포트·네트워크/방화벽 범위부터 구분합니다. PC는 성공하고 앱만 실패하면 앱의 base URL·INTERNET 권한·debug HTTP 설정·기기 네트워크를 확인합니다. 같은 Wi-Fi 이름이어도 기기 간 통신이 제한될 수 있습니다. 방화벽 전체 해제나 포트의 인터넷 공개를 접속 해결책으로 사용하지 않습니다.

## 3. 주소만으로 검사하기

다른 PowerShell 창에서 실행합니다. 아래 도구는 서버의 SQLite/.env를 읽지 않으며 데이터 수집도 수행하지 않습니다. 검사 실행 환경에 Python과 httpx가 필요합니다(서버 설치 환경에 포함).

```powershell
cd server
.venv\Scripts\python.exe scripts/check_vehicle_api.py --base-url http://127.0.0.1:8000 --expect-mode MOCK --demo-route
```

health, feed, detail, explain, 403/404/422, 뉴스 권리 차단, 반환 모드, 네 성공 응답의 OpenAPI 타입을 검사합니다. queue뿐 아니라 재생 가능한 alerts의 권리 근거·유효기한·교통 freshness와 playback_order 전체 순서를 검사합니다. LIVE 화면에 보이는 권리 미확인 뉴스도 상세 음성 불가/설명403인지 확인합니다. 성공은 종료코드 0과 `status=SUCCESS`, 실패는 종료코드 1과 code입니다. 결과는 Git에서 제외된 `server/reports/vehicle-api-check.json`에 저장됩니다. 결과의 verification_scope=SERVER_HTTP_ONLY, pleos_sdk_verified=false, vehicle_tts_verified=false는 검증 범위를 나타냅니다.

이 도구는 **재생 가능한 콘텐츠까지 준비됐는지** 검사하므로 health200이어도 빈 피드/화면 전용 뉴스만 있으면 NO_ELIGIBLE_TTS_CONTENT로 실패합니다. 기본 연결 여부는 앞 단계의 health 결과와 구분하세요. 도구 성공도 Pleos 앱 연결·TTS 재생 증거는 아닙니다.

## 4. 요청과 응답을 앱에 매핑

전체 타입은 [OpenAPI](openapi.json), 필드/변경 이력은 [API_CONTRACT](API_CONTRACT.md), 복사 가능한 요청은 [vehicle-api.http](examples/vehicle-api.http)입니다. health와 detail에도 명시적인 응답 타입이 있습니다. JSON 라이브러리는 nullable 시각/좌표와 향후 추가 필드를 처리할 수 있게 설정하세요.

```http
GET /api/v1/feed?lat=37.57&lon=126.98&interests=art&interests=science&navigation_active=false
```

| 응답 | 앱 처리 |
|---|---|
| top3 | 화면 카드 최대 3개, 0~2개도 정상. 음성 큐와 개수/항목이 다를 수 있음 |
| queue | 권리/유효성/추천 필터를 통과한 전체 일반 음성 큐 |
| alerts | 경로 관련 긴급정보. queue와 분리하며 우선 처리 |
| playback_order | alerts와 queue를 id로 연결해 재생할 순서. 해당 항목의 tts_eligible 확인 |
| data_mode / 항목 data_mode | LIVE/MOCK/MIXED 배지. 항목은 LIVE 또는 MOCK |
| verification_status | SIMULATED는 명시적으로 모의 자료 표시; LIVE라고 바꾸지 않음 |
| explain.ai_mode | 현재 MOCK. 콘텐츠가 LIVE여도 실제 AI 응답으로 표시하지 않음 |
| diagnostics | 데이터 부족/권리 차단/소스 장애/미검증 이동시간을 UI에서 구분 |

화면에는 title/brief/source_name/source_url과 데이터 모드·모의 표시를 매핑합니다. 음성에는 id/brief/rights_status/rights_evidence_url/tts_eligible/expires_at를 사용하며 교통은 fetched_at와 traffic도 확인합니다. `estimated_speech_seconds`는 추정값이며 실제 재생 시간으로 사용하지 않습니다. id는 불투명 문자열로 취급하고 상세 URL의 path segment를 인코딩합니다.

등록 관심사는 반복 query 또는 쉼표 문자열입니다. 한글/슬래시는 HTTP 클라이언트의 query 인코딩을 사용합니다. 좌표가 null인 콘텐츠에는 내비 연결 버튼을 임의로 활성화하지 않습니다. 시각은 offset이 있는 ISO 문자열로 파싱합니다. 권리 미확인 뉴스의 brief는 비어 있을 수 있습니다.

내비 비사용 시 ETA·목적지·route_points·route_link_ids를 보내지 않습니다. 내비 사용 시 목적지 좌표는 두 값을 함께 보냅니다. `route_points=위도,경도`는 반복 query이고 가까운 도로라는 것만으로 alerts를 만들지 않습니다. 실제 긴급정보는 **같은 SEOUL_TOPIS 링크 체계**의 경로 ID가 필요하며 다른 지도 링크와의 매핑은 아직 확인하지 못했습니다. `DEMO`/`demo-link-1`은 모의 시연용 입력입니다.

## 5. 재생과 오류 처리

재생 후보는 최신 feed의 queue/alerts에서 고릅니다. top3에만 있는 뉴스 제목을 fallback TTS로 읽지 않습니다. 사용자 재생 시작 → playback_order에서 다음 id 선택 → 재생 직전 새 feed와 필요한 상세를 조회해 후보 포함/tts_eligible/유효기한 확인 → **허용된 항목의 brief**를 차량 TTS에 전달합니다. brief가 비어 있으면 해당 항목을 보류합니다. 학교 AI나 explain 호출은 첫 TTS 시연의 선행조건이 아닙니다. 상세 조회의 자격 검사는 경로·이동시간 필터를 대신하지 않습니다. 재생 중인 항목의 중단/다음/다시, 주행 UX 제한, 내비 오디오 포커스는 앱이 제어합니다.

| HTTP | 처리 |
|---|---|
| 200 + 빈 feed | 새 소식 없음/조건 미충족. 기존 큐를 계속 재생하지 말고 만료 여부 재검사 |
| 403 | 권리/가공 자격 없음. 요약·TTS 우회 금지 |
| 404 | 콘텐츠 없음 또는 현재 모드에서 숨김. 해당 항목 제외 |
| 409 | 만료/미래 정보 또는 오래되거나 해제된 교통정보. 큐에서 제외하고 새 feed 요청 |
| 422 | query/body 오류. 좌표 범위·좌표 쌍·내비 필드 확인 |
| 연결 실패/timeout | 연결 상태 안내. 마지막 큐의 만료·교통 freshness 검사 없이 계속 재생하지 않음 |

## 6. 실데이터 시연으로 전환

서버를 종료한 뒤 같은 server 폴더에서:

```powershell
.venv\Scripts\python.exe -m app.cli ingest --public-provider seoul_city --report reports/vehicle-weather-ingest.json
$env:NOTICE_DATA_MODE='live'
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --no-access-log
```

다른 창에서 `.venv\Scripts\python.exe scripts/check_vehicle_api.py --base-url http://127.0.0.1:8000 --expect-mode LIVE`를 실행합니다. 위 선택 수집은 날씨만 1회 호출하며 뉴스 검색·다른 공공 제공자는 호출하지 않습니다. 기존 전체 수집은 --public-provider를 생략하면 됩니다. 키 없이 가능한 날씨는 **광화문·덕수궁 sample**이고 모든 위치의 날씨를 수집하는 기능은 아닙니다. FreeNews 인증/일부 실제 metadata 수집은 이미 확인했으나 뉴스 TTS 권리는 미확인입니다. 행사 이동시간은 미검증이므로 실제 수집된 행사도 추천에서 제외됩니다. 실제 교통 링크를 주지 않으면 alerts가 비어 있는 것이 정상입니다.

날씨는 원천 갱신 후 1시간, 교통은 수집 후 10분 조건이 있습니다. 시연 시작 직전 재수집하고 장시간 시연 중에는 수동 ingest로 갱신하세요. 스케줄러는 아직 없으며 키/무료 할당량을 확인해 호출해야 합니다. 실자료+fixture를 같이 쓰려면 mode=mixed로 재시작하고 MIXED/SIMULATED 표시를 유지합니다.

세 모드 재현은 같은 명령의 NOTICE_DATA_MODE를 mock/live/mixed로 바꾸어 서버를 차례로 재시작하고, 검사 report 이름을 각각 다르게 지정합니다. MOCK/MIXED에서만 --demo-route를 추가해 모의 긴급정보 우선순위를 검사할 수 있습니다. 예: `scripts/check_vehicle_api.py --expect-mode MIXED --demo-route --report reports/vehicle-mixed.json`. 세 모드를 동시에 쓰면 포트도 구분하세요. 설정 mixed여도 실제 반환 항목이 한 모드뿐이면 feed.data_mode는 LIVE 또는 MOCK일 수 있으므로 --expect-mode는 관측할 콘텐츠 구성을 기준으로 선택합니다.

## 7. 팀원이 남길 연결 증거

앱 빌드/기기 또는 에뮬레이터 버전, 서버 브랜치·커밋, health/feed HTTP 상태, 카드/큐 개수, 화면의 데이터 모드 표시, TTS 재생 여부·다음/다시 동작을 기록합니다. API 키와 실제 사용자 위치·경로·개인정보는 로그나 저장소에 올리지 않습니다. 이 증거가 확보되기 전에는 서버 단독 검증과 앱 연결 완료를 구분합니다.

## 8. Pleos 앱 담당자의 SDK/TTS 준비

2026-11-11 공식 문서 확인 기준이며 **설치·빌드·실행 검증은 하지 않았습니다**. [Pleos 개발 시작](https://document.pleos.ai/en/docs/pleos-only/getting-started)은 Android Studio/Pleos 시스템 이미지/AVD 구성을 안내합니다. 팀원은 설치한 이미지·Android API·실제 SDK 의존성 버전을 기록하고 해당 버전 문서를 따릅니다.

[네트워크 권한](https://developer.android.com/develop/connectivity/network-ops/connecting)의 INTERNET과 [Pleos TTS 권한](https://document.pleos.ai/en/docs/pleos-only/connect-sdk-pleos/TextToSpeech/declaring-permissions)의 `pleos.car.permission.TTS_SERVICE`는 목적이 다릅니다. HTTP 성공이 TTS 초기화/권한 성공을 뜻하지 않습니다.

[Pleos TTS 문서](https://document.pleos.ai/docs/pleos-only/connect-sdk-pleos/TextToSpeech/intro)는 현재 v3.3.1 기준으로 ON_DEVICE/HYBRID/SERVER를 구분합니다. ON_DEVICE 단독은 서버 기반 TTS 앱 등록을 요구하지 않으므로 첫 무료 시연 후보로 제안합니다. 실제 기기의 한국어 엔진/초기화/재생 성공은 팀원이 확인해야 합니다. 기본 HYBRID와 SERVER의 서버 합성에는 별도 앱 등록·연결 조건이 있으므로 준비된 것으로 가정하지 않으며 유료 서비스를 활성화하지 않습니다.

앱 담당 구현 순서: HTTP JSON 파싱/카드 → 사용자 재생 버튼 → 최신 후보·권리 검사 → TTS 권한/초기화·언어·이벤트 확인 → brief 재생 → 중단/다음/다시·오디오 포커스·해제입니다. 각 단계는 [연동 확인표](VEHICLE_ACCEPTANCE.md)에 실제 결과를 남깁니다. FastAPI는 텍스트 JSON을 제공하며 음성 파일이나 SDK 세션을 만들지 않습니다.
