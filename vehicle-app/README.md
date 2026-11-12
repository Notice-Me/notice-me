# Notice Me 차량 앱

2026-11-11 신규 Android/Kotlin 프로젝트. `health → feed → TOP3`, 사용자 재생, `playback_order` 기반 연속 TTS, 패스·다시 듣기·중단을 구현했습니다. **Pleos 0.2.2에서 같은 Mac의 MOCK 서버에 연결해 추천 3건 표시를 확인했습니다.** 재생 확인 중 에뮬레이터 연결이 끊겨 음성 출력과 재생 완료는 미확인입니다.

## 0.2.2 화면

추천은 구분선이 있는 한 열 목록으로 표시합니다. 오프화이트 바탕, 차콜 글자, 올리브색 재생 버튼을 사용합니다. 기사 설명이 비어 있으면 제목과 출처를 표시합니다. 설정은 상단에서 열고 재생 조작은 화면 아래에서 합니다.

## 빌드

Android Studio에서 이 `vehicle-app` 폴더를 엽니다. Android SDK Platform 37, Build Tools 36.0.0, JDK 17 이상이 필요합니다. Gradle wrapper 9.6.0 / AGP 9.5.1을 고정했습니다. SDK 경로는 Android Studio가 생성하는 `local.properties` 또는 `ANDROID_HOME`으로 지정합니다. API 키는 필요하지 않습니다.

```sh
./gradlew :app:assemblePleosDebug :app:assembleStandardDebug
./gradlew :app:testStandardDebugUnitTest :app:lintStandardDebug :app:lintPleosDebug
```

Windows에서는 `gradlew.bat`을 사용합니다. 결과는 `app/build/outputs/apk/pleos/debug/app-pleos-debug.apk`, `app/build/outputs/apk/standard/debug/app-standard-debug.apk`입니다.

- **pleosDebug**: Pleos TTS SDK 3.3.1, `ON_DEVICE`, 한국어, `pleos.car.permission.TTS_SERVICE`. Pleos 에뮬레이터/기기에서 사용합니다. HYBRID/SERVER 등록이나 유료 서비스를 사용하지 않습니다.
- **standardDebug**: 일반 Android TTS. 로컬 한국어 음성이 설치되어 있어야 합니다. Pleos 검증을 대신하지 않으며 화면에도 일반 Android임을 표시합니다. Pleos 앱 실패 시 자동으로 이 엔진으로 전환하지 않습니다.
- minSdk 28 / targetSdk 34. Pleos API 34 시연 대상이며 앱 마켓 출시 준비를 의미하지 않습니다.

## 처음 연결

1. [서버 안내](../docs/VEHICLE_INTEGRATION.md)에 따라 같은 PC에서 MOCK 서버를 `0.0.0.0:8000`으로 실행합니다. 새 macOS/Linux 환경 예시는 저장소 루트에서 다음과 같습니다.

   ```sh
   python3 -m venv .venv
   .venv/bin/pip install -r server/requirements.lock
   cd server
   NOTICE_DATA_MODE=mock ../.venv/bin/python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --no-access-log
   ```

2. Pleos 기기에는 `pleosDebug`를 설치합니다. 일반 Android AVD에서는 `standardDebug`를 사용합니다.
3. 앱의 서버 주소는 같은 PC의 표준 AVD라면 `http://10.0.2.2:8000`. 다른 PC라면 실제 서버 LAN IPv4를 사용합니다. `0.0.0.0`은 접속 주소로 사용할 수 없습니다.
4. **다른 PC의 HTTP 주소**는 `app/src/debug/res/xml/network_security_config.xml`의 `<domain-config>`에 해당 호스트/IP를 `<domain includeSubdomains="false">서버 IP</domain>`로 추가한 뒤 debug APK를 다시 빌드합니다. 출시 빌드는 HTTPS만 허용합니다. 기본 debug 허용 호스트는 `10.0.2.2`, `127.0.0.1`, `localhost`입니다.
5. 기본 위치 37.57 / 126.98은 광화문 시연 좌표입니다. 관심사 `art,science,weather`를 확인하고 **새로고침**을 누릅니다. 좌표·관심사는 메모리에서만 사용합니다. 서버 주소만 로컬 설정에 저장합니다.
6. **추천 소식**의 제목·출처와 모의 자료 표시를 확인하고 **재생**을 누릅니다. 카드 수 0~2개도 정상입니다. 서버 주소와 시연 좌표는 상단 **설정**에서 바꿀 수 있습니다.
7. **패스**는 현재 항목을 중단하고 최신 순서의 다음 미재생 후보를 읽습니다. **다시 듣기**는 현재 선택 항목을 처음부터 재검사/재생합니다. 해당 항목이 사라졌으면 읽지 않습니다. **중단** 후 재생은 새 세션을 처음부터 시작하며 다시 듣기는 선택 항목을 재생합니다.

설정을 변경하면 연결/큐를 무효화합니다. 앱이 화면에서 벗어나거나 오디오 포커스를 잃으면 중단하며 자동 재개하지 않습니다. 현재 앱은 **정차 시연용**입니다. GPS, 내비 경로, CarUxRestrictions, 백그라운드 미디어 서비스, 차량 버튼 연동은 후속 작업입니다. 실제 주행용으로 완료 처리하지 마세요.

## 재생 계약

`top3`는 화면 전용 목록이고 음성 권한의 근거가 아닙니다. 최신 `queue + alerts`에 있는 고유 id를 `playback_order`로 정렬합니다. 각 항목 직전에 최신 feed와 detail을 조회하여 `tts_eligible`, TTS_ALLOWED, 권리 근거, 검증 상태, 미래/만료, 교통 ACTIVE/10분 freshness를 확인합니다. SDK 초기화 직후에도 유효기간을 다시 확인합니다. 허용된 최신 detail의 **brief만** 읽고 제목이나 explain을 대체 음성으로 쓰지 않습니다.

detail의 403/404/409는 해당 후보를 제외하고 피드를 갱신합니다. 연결 실패/잘못된 JSON은 기존 큐를 중단하며, 422는 입력 오류로 안내합니다. 빈 피드는 정상적인 빈 상태입니다. MOCK/SIMULATED 표시를 유지합니다. 동시 명령은 이전 네트워크/TTS 작업을 취소하고 재생별 SDK 인스턴스로 늦은 이벤트를 격리합니다.

## 검증

단위 테스트는 권리/만료/빈 피드/응답 파싱/한글 query·id 인코딩/서버 오류/순서/패스/다시/취소를 검사합니다. 실제 로컬 MOCK 서버를 실행한 뒤 아래 명령으로 앱과 동일한 HTTP 클라이언트의 health/feed/detail을 JVM에서 검사할 수 있습니다.

```sh
NOTICE_TEST_BASE_URL=http://127.0.0.1:8000 ./gradlew :app:testStandardDebugUnitTest --rerun-tasks
```

PowerShell은 `$env:NOTICE_TEST_BASE_URL='http://127.0.0.1:8000'` 설정 후 실행합니다. 변수가 없으면 외부 서버 통합 테스트 1개만 skip됩니다. 이 결과는 Android 네트워크 보안 정책 또는 기기 음성 출력 검증이 아닙니다.

[검증 기록](../docs/verification/2026-11-11-vehicle-app.md), [기기 인수 확인표](../docs/VEHICLE_ACCEPTANCE.md)를 확인하세요. 서버 계약 변경은 없습니다.
