# 차량 앱 첫 구현 검증 — 2026-11-11 KST

서버 기준 `feat/server-content-feed` / `b22c1e2f509d87def5f10362a834d0906ef6b892`, 앱 브랜치 `codex/vehicle-feed-tts`.

## 확인한 범위

- AGP 9.5.1 / Gradle 9.6.0 / Android compile SDK 37 / target 34 / min 28 / Pleos TextToSpeech 3.3.1.
- macOS arm64, Android Studio JBR 25.0.4로 `assembleStandardDebug`, `assemblePleosDebug` 성공.
- `testStandardDebugUnitTest`: 단위 테스트 18개 통과. `NOTICE_TEST_BASE_URL` 지정 재검증에서 실제 MOCK HTTP 통합 테스트 1개 포함 **19개 통과, skip 0**.
- 실제 Uvicorn MOCK 서버의 health, feed, 각 음성 후보 detail을 앱과 동일한 `HttpContentApi`/`FeedJson`으로 요청/파싱. health=MOCK, TOP3=3, 후보/상세의 음성 자격 확인. JVM 실행이며 Android 기기 HTTP 성공을 뜻하지 않음.
- `lintStandardDebug`, `lintPleosDebug`: 오류 없이 완료. target 34/새 의존성 버전, 백업 속성, 앱 아이콘 등 경고가 남음. Pleos 전이 의존성 JNA 5.13.0의 x86_64 네이티브 라이브러리 16KB 정렬 경고도 있음. SDK 의존성을 임의로 교체하지 않았으며 출시/16KB 기기 호환성은 미검증.
- 서버 `pytest -q`: **110 passed**, 기존 Starlette/httpx deprecation 경고 1개. 서버 소스 변경 없음.
- Gradle wrapper 배포 SHA-256은 공식 배포 checksum과 일치 확인.

## 실패/미검증

설치된 일반 Android emulator 37.2.13, API 37 arm64 시스템 이미지로 작업 폴더에 별도 AVD를 만들어 두 번 실행했으나 APK 설치 전 emulator 프로세스가 종료코드 132로 종료됨. macOS 진단은 `EXC_BAD_INSTRUCTION / SIGILL / Illegal instruction: 4`. 원인은 확정하지 못했으며 기존 사용자 AVD는 수정하지 않음.

따라서 앱 화면 렌더링, Android 기기의 health/feed, 한국어 엔진·음성 출력, 실제 패스/다시 동작, 차량 오디오 포커스, Pleos 런타임 초기화는 **NOT_RUN**. 이 환경에는 Pleos 시스템 이미지가 없음. APK 빌드와 테스트용 SpeechPlayer 성공을 실제 TTS 성공으로 표시하지 않음.

이 구현은 수동 시연 좌표/관심사와 내비 비사용 요청을 사용함. 실제 GPS/경로, CarUxRestrictions, 백그라운드 재생/차량 버튼은 후속 범위. 긴급 우선순위는 테스트에서 검증했으나 실제 경로가 없어 앱의 기본 요청에서 alerts가 비어 있는 것이 정상.

## 다음 기기 검증

[vehicle-app README](../../vehicle-app/README.md)대로 Pleos APK를 설치하고 [VEHICLE_ACCEPTANCE](../VEHICLE_ACCEPTANCE.md)의 B~G를 기록. 서버와 같은 PC라면 10.0.2.2 후보를 검증하고, 다른 PC는 LAN 주소와 debug 호스트 허용을 설정. 첫 테스트는 MOCK으로, 실제 공공자료 시연은 원천 갱신 후 별도로 수행.
