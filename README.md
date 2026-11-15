# Notice Me

위치·목적지·관심사 문맥을 활용해 소식을 추천하고 음성으로 안내하는 **Pleos 차량 앱 MVP**입니다. 2026년 11월 15일 1차 참가신청서 제출을 위한 개발본이며, APK·소스는 추가 검토 자료입니다. 현재 앱은 **정차 시연용**입니다.

기준 소스는 PR #8·#9·#10이 병합된 main `0fe84f9`입니다. 차량 앱 **0.3.3 / versionCode 8**, Pleos TTS **3.3.1 ON_DEVICE**, NaviHelper **3.0.5**를 사용합니다. 미병합 자동화 PR #11·UI PR #12·#13은 이 제출본에 포함하지 않습니다. 실제 검증 결과와 APK 경로·해시는 [제출 준비 보고서](docs/SUBMISSION_MVP_2026-11-15.md)를 확인하세요.

## 구현·검증 상태

| 항목 | 현재 구현 | 검증 범위·한계 |
|---|---|---|
| FastAPI·SQLite | health/feed/detail/explain, 모드 분리, 만료·권리 검사 | 서버 회귀 검사 및 기존 HTTP 검증. explain은 deterministic MOCK |
| 추천·관심사 | 규칙 점수, 한영일 치이카와 별칭, 구체 관심사/형식 결합, 중복 제거 | 점수 근거 제공. 독립 관심사 OR 프로필은 [제안](docs/INTEREST_PROFILE_PROPOSAL.md) 단계 |
| 화면·음성 큐 | 최대 TOP3 화면과 별도 queue/alerts/playback_order | TOP3만으로 재생하지 않음. 목적지 ETA는 재생 예산에 사용 |
| Pleos HTTP·TTS | health → feed → detail → 최신 brief의 Pleos ON_DEVICE 재생 | 11/13 에뮬레이터에서 서버 brief 일치·청취·패스/다시/중단 검증. 이번 재검증은 제출 보고서에 별도 표시 |
| 내비 문맥 | 현재 위치·목적지·ETA 조회/서버 전달, 미수신 시 설정 좌표 표시 | 기존 Pleos 에뮬레이터 검증. 경로 전체·실차·주행 중 ETA 변화는 미검증 |
| 실제 날씨 | 서울시 POI009 광화문·덕수궁 고정 지역 | LIVE 음성의 유일한 실제 콘텐츠. 관측 후 1시간 만료, 별도 수집 필요 |
| 뉴스·행사 수집 | FreeNews metadata, 서울시 공공자료, TourAPI 수집기 | 수집 성공과 추천·음성 허용은 별개. 뉴스 본문/요약/TTS는 제공하지 않음 |
| 행사·팝업 | 공식 확인 입력 경로와 추천 게이트 | 실제 자동차 이동시간 미검증이면 LIVE 추천 제외. 검증된 실제 팝업 추천은 미완료 |
| 안전 처리 | 만료/권리 재검사, 연결 실패 시 큐 제거, 오디오 포커스 손실/화면 이탈 시 중단 | 주행용 UX 인증·실차 적합성 완료를 뜻하지 않음 |

**미구현:** 실제 자동차 길찾기, STT 음성 명령, Gleo 연동, 학교 AI/BAZE 연결, 실제 생성형 요약, 앱에서 목적지 생성, 자동 콘텐츠 수집, 위치별 날씨. 음성 잡음의 원인과 개선도 미해결입니다. 일반 Android TTS flavor의 성공을 Pleos 검증으로 표시하지 않습니다.

## 현재 정책과 최종 기획의 구분

현재는 유효성·권리·실제 행사 이동시간 게이트를 적용하고, 관심사/지역/신선도/검증 근거의 규칙 점수로 추천합니다. 동일 체계의 경로 링크가 확인된 교통 alerts는 일반 음성보다 앞에 배치합니다. 현재 앱은 도로 링크/전체 경로를 전송하지 않아 **실제 경로 기반 긴급 안내가 완성된 것은 아닙니다**. LIVE 음성은 허용된 날씨만, MOCK은 명확히 표시한 합성 콘텐츠입니다.

최종 목표인 **긴급·안전 > 지역·개인 관심사 > 화제 > 일반 소식**의 단계별 정책, 장거리에서 개인 관심사·화제 소식으로 큐 확장, 공식 웹/SNS/허용된 제공자에서 팝업 후보 발견·검증은 후속 개발입니다. 현재 기능으로 주장하지 않습니다.

## 서버 실행 — 키 없이 MOCK 확인

Python 3.11+가 필요합니다. PowerShell에서 저장소 루트 기준:

```powershell
if (!(Test-Path -LiteralPath 'server/.venv/Scripts/python.exe')) { py -3.11 -m venv server/.venv }
& ./server/.venv/Scripts/python.exe -m pip install -r server/requirements.lock
& ./server/.venv/Scripts/python.exe -m pip install -e ./server --no-deps
cd server
$env:NOTICE_DATA_MODE='mock'
$env:NOTICE_DB_PATH=Join-Path $env:TEMP ('notice-me-mock-' + [guid]::NewGuid().ToString() + '.sqlite3')
& ./.venv/Scripts/python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

기존 venv가 있으면 재생성하지 않고 사용하세요. 이 예시는 매 실행 별도 MOCK DB를 사용하며 기존 `.env`·DB를 덮어쓰지 않습니다. `.env` 복사는 필수가 아닙니다. API 문서는 `http://127.0.0.1:8000/docs`입니다. MOCK도 **FastAPI 서버가 필요**하며 앱 내부 오프라인 데이터가 아닙니다.

같은 PC의 Pleos Android 에뮬레이터에서 앱 서버 주소는 **`http://10.0.2.2:8000`**입니다. `0.0.0.0`은 접속 주소가 아닙니다. 다른 PC/차량에서 연결하려면 네트워크 접근과 debug HTTP 허용 호스트가 맞아야 합니다. 기본 허용은 `10.0.2.2`, `127.0.0.1`, `localhost`이며 임의 LAN 주소는 그대로 접속되지 않을 수 있습니다. [상세 연결 안내](docs/VEHICLE_INTEGRATION.md).

## LIVE 날씨

LIVE는 이미 수집한 데이터만 읽습니다. 앱의 약 15초 갱신은 SQLite 조회이며 외부 API 수집이 아닙니다. 시연 직전 별도 DB 사본을 지정하고 **날씨 제공자 하나만** 갱신합니다.

```powershell
# server/에서 실행. NOTICE_DB_PATH는 원본이 아닌 사용할 시연 DB 사본으로 먼저 지정
& ./.venv/Scripts/python.exe -m app.cli ingest --public-provider seoul_city --report reports/weather-new.json
$env:NOTICE_DATA_MODE='live'
& ./.venv/Scripts/python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

날씨의 관측·만료·고정 지역을 확인하세요. 만료되면 큐 0건이 정상이며 데이터를 만들거나 수집시각으로 만료를 연장하지 않습니다. 현재 위치/목적지의 날씨라고 안내하지 않습니다. 실제 뉴스 metadata는 화면 전용이며, Type3 행사 음성 및 이동시간 미검증 행사 추천은 차단합니다. [날씨 정책·DB 사본 안내](docs/LIVE_WEATHER_DEMO.md), [출처·권리](docs/DATA_SOURCES.md).

## APK 빌드·설치·외부 실행 한계

JDK 17+, Android SDK Platform 37 / Build Tools 36.0.0, 프로젝트의 Gradle wrapper를 사용합니다. 개인 SDK 경로는 `vehicle-app/local.properties` 또는 `ANDROID_HOME`으로 지정하고 커밋하지 않습니다.

```powershell
cd vehicle-app
./gradlew.bat :app:assemblePleosDebug :app:assembleStandardDebug
# 로컬 MOCK 서버가 실행된 상태: JVM HTTP 통합 테스트도 포함
$env:NOTICE_TEST_BASE_URL='http://127.0.0.1:8000'
./gradlew.bat :app:testPleosDebugUnitTest :app:testStandardDebugUnitTest :app:lintPleosDebug :app:lintStandardDebug
```

- Pleos APK: `vehicle-app/app/build/outputs/apk/pleos/debug/app-pleos-debug.apk` — Pleos TTS/내비 서비스·공식 권한이 있는 환경 필요.
- 일반 Android APK: `vehicle-app/app/build/outputs/apk/standard/debug/app-standard-debug.apk` — 별도 패키지, 일반 Android TTS 사용. Pleos 기기 검증의 대체물이 아님.
- 제출 복사본·서명/버전·SHA256·기준 commit은 [제출 보고서](docs/SUBMISSION_MVP_2026-11-15.md)와 [검증 JSON](docs/verification/2026-11-14-submission.json)에 기록합니다. APK는 Git에 커밋하지 않습니다.
- 제출본은 **debug 서명 테스트 APK**입니다. 스토어 출시용 release 서명/배포 인증 완료를 뜻하지 않습니다.
- APK 안에 서버·API 키·실제 DB가 없습니다. 서버 미연결 시 연결 오류를 표시하며 카드·음성을 제공하지 않습니다. APK 단독 설치만으로 모든 기능이 실행되는 형태가 아닙니다.

추가 실행 절차와 재생 계약은 [차량 앱 README](vehicle-app/README.md)를 확인하세요.

## 서버 검사

```powershell
cd server
& ./.venv/Scripts/python.exe -m pytest -q
& ./.venv/Scripts/python.exe -m ruff check app tests scripts
& ./.venv/Scripts/python.exe -m ruff format --check app tests scripts
& ./.venv/Scripts/python.exe -m pip check
```

외부 API의 실제 호출은 별도로 기록하며 MockTransport/fixture 통과를 실호출 성공으로 표시하지 않습니다. APK 빌드·JVM 시험·에뮬레이터 실행·사람의 청취·실차 검증도 각각 구분합니다.

## 제출·보안·협업

저장소는 비공개입니다. **GitHub 링크만 제출하면 심사자가 열 수 있다는 보장이 없습니다.** 공개 전환·외부 접근 허용·실제 제출은 사용자가 결정합니다. 소스 ZIP은 기록한 commit의 추적 파일만 포함하고 `.env`·키·DB·개인 설정·신청서 원본·팀원 개인정보를 넣지 않습니다. 위치/목적지/질문 이력은 저장하지 않으며 검증 로그·기기 화면은 자동 공개하지 않습니다.

기능 브랜치에서 테스트 후 PR을 만들고 사용자 승인 전 main 병합·자동 병합·force push를 하지 않습니다. ChatGPT와 사용자가 기획·기술 판단을 하고 Codex가 구체 구현·검증을 수행합니다. 별도 멀티 AI 자동화 시스템은 확장하지 않습니다.

관련 문서: [API 계약](docs/API_CONTRACT.md) · [OpenAPI](docs/openapi.json) · [개발 현황](docs/PROJECT_STATUS.md) · [기술 결정](docs/TECH_DECISIONS.md) · [개발 로그](docs/DEVELOPMENT_LOG.md) · [학습 기록](docs/LESSONS_LEARNED.md).
