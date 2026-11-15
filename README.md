# Notice Me

위치·내비 문맥·관심사를 바탕으로 소식을 고르고, 허가된 콘텐츠를 음성으로 안내하는 Pleos 차량 앱 MVP입니다.

**2026년11월15일은 현장 시연회가 아닌 1차 참가신청서(기획서) 접수일입니다.** GitHub·APK·영상은 선택 가산점 자료입니다. [공식 제출 안내](https://appdevchallenge.auto-hmg.io/guide/submission).

## 최종 소프트웨어

- **0.3.7 / versionCode13 / Pleos release**, 팀원 PR #16 UI6cdd8e3 채택
- **[apk/울산동천고듀오_NoticeMe_release.apk](apk/울산동천고듀오_NoticeMe_release.apk)** — 제출 APK는 이 파일 하나입니다.
- 24,951,759bytes, SHA256 `2a072c6b6f56e1025e7e7f40dc16aea85c98b351df32ce786a50c4ce29b73211`
- [APK manifest](apk/manifest.json) · [최종 검증 보고서](docs/FINAL_SUBMISSION_2026-11-15.md) · [공개 전 감사](docs/PUBLICATION_AUDIT_2026-11-15.md)
- APK의 원래 빌드 입력 commit은 `024d1b28f8b6649d20339266349e256933636d46`입니다. 최종 제출 commit은 소스·이 APK·문서·검증 결과를 포함한 마지막 commit이며, 접수 메일에 그 전체 SHA를 기재합니다. `git rev-parse HEAD`로 확인합니다.

## 구현 및 검증 범위

|구분|현재 상태|
|---|---|
|서버|FastAPI health/feed/detail/explain, SQLite, 수집·정규화, 관심사/위치 추천, 권리·만료 검사|
|차량 앱|서버 JSON 파싱, TOP3 카드, 화면과 독립된 음성 큐, 재생·다음·다시 듣기·중단|
|내비|Pleos NaviHelper 현재 위치·목적지·ETA 조회 및 서버 전달. 조회와 목적지 생성 권한은 별개|
|MOCK|자체 작성·SIMULATED 데이터로 서버↔앱↔실제 Pleos ON_DEVICE TTS 연결 검증. 실제 뉴스·행사가 아님|
|LIVE 날씨|기존0.3.3 기기 검증에서 서울시 고정 지역 날씨의 실제 brief/청취 확인. 최종0.3.7의 이번 MOCK 재검증과 구분|
|실제 뉴스·행사|뉴스 metadata 표시만. 본문·임의 요약·TTS 차단. 권리 미확인 행사 음성 및 실제 이동시간 미검증 행사 추천 차단|
|분할 화면|Pleos Connect2.1/API34/x86_64,2560×1440px/160dpi. 내비와 앱 각841×1210px 동시 표시 확인. 차량 정보 영역은 별도|
|미검증|실차/주행 안전성,400dp 미만·글자 확대 전체 조합,최종 APK의 최신 LIVE 날씨 재생,Market 승인|

이번 최종 구성에서 다시 실행한 테스트·설치·음성 및 서버 미연결 결과는 위 최종 검증 보고서에 기록합니다. 과거 docs/verification 기록은 해당 시점의 이력이며 현재 실행 결과와 혼동하지 않습니다.

## Windows에서 MOCK 서버 실행

Python3.11 이상이 필요합니다. 아래는 저장소 루트의 PowerShell에서 실행합니다. 기존 `.env`,DB,개인 설정은 복사/삭제하지 않습니다. MOCK에는 API 키가 필요하지 않습니다.

```powershell
cd server
# 최초 환경 구성 때만. 기존 .venv가 있으면 다시 만들지 않습니다.
if (-not (Test-Path .venv/Scripts/python.exe)) { py -3.11 -m venv .venv }
& ./.venv/Scripts/python.exe -m pip install -r requirements.lock
& ./.venv/Scripts/python.exe -m pip install -e . --no-deps

# 새 로컬 DB를 지정하여 기존 데이터베이스와 분리합니다.
$demoDir = Join-Path $env:LOCALAPPDATA ('NoticeMe/demo-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $demoDir | Out-Null
$env:NOTICE_DB_PATH = Join-Path $demoDir 'mock.sqlite3'
$env:NOTICE_DATA_MODE = 'mock'
$port = 8000  # 이미 사용 중이면8002 등 빈 포트를 선택하고 앱 주소도 맞춥니다.
& ./.venv/Scripts/python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port $port --no-access-log
```

새 터미널에서 `http://127.0.0.1:8000/api/v1/health`를 확인합니다. 포트를 바꿨으면 같은 번호를 사용합니다. API 문서는 `/docs`입니다. 서버를 종료하려면 실행 터미널에서 Ctrl+C를 누릅니다.

## APK 설치·연결

1. Pleos Connect2.1/API34 에뮬레이터를 실행하고 최종 APK를 설치합니다. 기존 앱과 서명이 다르면 삭제하지 말고 먼저 서명을 확인합니다.
2. Notice Me의 설정에서 **같은 PC 서버는 `http://10.0.2.2:8000`**, 위에서 포트를 바꿨으면 같은 번호를 입력합니다. `0.0.0.0`은 접속 주소가 아닙니다.
3. 관심사와 내비 위치 사용 여부를 확인하고 설정을 닫은 뒤 새로고침을 누릅니다. TOP3와 MOCK 표시를 확인하고 재생합니다.
4. 기본 내비와 나란히 띄울 때는 Pleos 시스템 창 바를 사용합니다. 창 바 drag로 분할하고 두 앱 사이 창 바 tap으로 위치를 교환할 수 있습니다. 앱이 임의로 다른 앱의 창을 강제하지 않습니다.

Release HTTP 허용은 `10.0.2.2`, `127.0.0.1`, `localhost`뿐입니다. 다른 서버 호스트는 HTTPS가 필요합니다. 공용 서버는 배포하지 않았습니다. Pleos SDK/서비스·공식 권한이 있는 환경이 필요하며 일반 휴대전화의 Android TTS 동작을 Pleos 검증으로 보지 않습니다.

**APK 안에 FastAPI 서버·실제 DB·API 키는 없습니다.** MOCK도 내장 오프라인 데모가 아니므로 서버가 필요합니다. 서버 미연결/잘못된 응답 시 오류를 표시하고 기존 큐를 중단합니다. 앱이 화면에서 사라지는 onStop에서도 TTS를 중단하므로 최소화 후 백그라운드 재생을 보장하지 않습니다. 시스템 창 크기 전환 뒤 새로고침이 필요할 수 있습니다.

## LIVE 실행과 권리

LIVE는 별도 수집한 실제 SQLite 자료를 조회합니다. 이미 있는 원본 DB 대신 사본을 지정하고 필요한 제공자만 최소 호출로 갱신하세요. [LIVE 날씨 절차](docs/LIVE_WEATHER_DEMO.md) · [출처와 권리](docs/DATA_SOURCES.md).

날씨는 현재 위치/목적지 전체가 아닌 고정 관측 지역 자료이며 원천 관측·만료 시각을 표시합니다. 유효하고 허가된 실제 날씨만 LIVE TTS 대상입니다. 앱의 약15초 idle feed 갱신은 DB 조회이며 외부 데이터 수집이 아닙니다. 목적지 ETA를 행사장 자동차 이동시간으로 대체하지 않습니다.

## 빌드와 검사

Android SDK Platform37/Build Tools36.0.0, 프로젝트 Gradle wrapper, JDK17 이상이 필요합니다. 이 PC에서는 Android Studio JBR25 환경을 사용합니다. 개인 SDK 경로는 `ANDROID_HOME` 또는 로컬 `local.properties`로만 지정합니다. Pleos SDK의 사용·배포 조건은 공식 계정 안내를 확인해야 합니다.

```powershell
cd vehicle-app
./gradlew.bat :app:assemblePleosRelease :app:assembleStandardRelease
$env:NOTICE_TEST_BASE_URL='http://127.0.0.1:8000' # 실행 중인 MOCK 포트로 변경
./gradlew.bat :app:testPleosDebugUnitTest :app:testStandardDebugUnitTest :app:lintPleosRelease :app:lintStandardRelease
```

프로젝트가 제공하는 단위 테스트 task는 debug variant입니다. release 빌드/서명/실행 검증과 구분합니다. `assemblePleosRelease`의 unsigned 출력은 제출 APK가 아니며, 새 배포본은 저장소 밖의 같은 release 키로 별도 서명·검증해야 합니다. 키와 암호는 Git·로그·채팅으로 공유하지 않습니다. Standard flavor는 일반 Android TTS를 사용하는 별도 패키지이며 Pleos 검증을 대신하지 않습니다.

서버 검사는 `server/`에서 `.venv/Scripts/python.exe -m pytest -q`, `-m ruff check app tests scripts`, `-m ruff format --check app tests scripts`, `-m pip check`를 실행합니다.

## 미구현 및 후속 개발

STT·Gleo·학교 AI·공용 서버 배포·실제 자동차60분 이내 행사 추천·새 팝업 자동 수집·관심사 OR 프로필 API는 완료된 기능이 아닙니다. 공식 권한·데이터 권리·비용·라우팅을 확인한 후 별도 개발합니다. 최종 추천 목표(긴급/안전→지역/개인 관심→화제→일반)와 장거리 음성 큐 확장은 현재 전체 구현과 구분합니다. 컴팩트 시안 PR #18과 이전 APK는 이번 제출 소스에 포함하지 않습니다.

11/15 접수 후2차 PT 전까지 고도화할 수 있습니다. GitHub A안은 접수 메일에 저장소 URL·최종 commit을 적고, 별도 승인 후11/16까지 public 전환해11/23까지 유지하는 계획입니다. 공개 전 커밋 작성자 정보와 SDK 배포 조건 등 감사의 남은 사항을 확인합니다. 신청서·동의서·메일 발송·main 병합·공개 전환은 사용자가 최종 검토합니다.
