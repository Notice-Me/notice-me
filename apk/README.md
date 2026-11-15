# 공모전 제출 APK

[울산동천고듀오_NoticeMe_release.apk](울산동천고듀오_NoticeMe_release.apk)를 제출 후보로 준비했습니다. **실제 pleosRelease 빌드·독립 release 키 서명·non-debuggable 앱**이며 기존 debug APK의 파일명만 바꾼 것이 아닙니다.

- 버전: 0.3.3 / versionCode8 / package ai.noticeme.vehicle
- 파일 크기: 24,951,703byte (23.80MiB)
- APK SHA256: `7aa31e6b81220bac2ae76c6e86db670ac3d5b9ab06bbe2a622a1ba3aa54cb78d`
- APK 빌드 입력 commit: `b2f66f5c6de3a2ad1d54d59c7249ca7c22a656dd`. 최종 접수 commit은 이 APK·문서가 함께 있는 후속 commit이며 메일에는 그 최종 hash를 적습니다.
- 공개 인증서 SHA256: `e0bbf1e148be28c9047c1ee1a9360218fae113d7f0fba824766ccb263ec8752e`. 인증서 지문은 비밀키·비밀번호가 아닙니다.
- apksigner verify 성공(v3), zipalign 검사 통과. Pleos Connect2.1/API34/x86_64에 설치·실행하고 MOCK TTS·다음/다시/중단 및 실제 청취를 확인했습니다.
- 화면: 차량 전체 디스플레이2560×1440px/160dpi. 앱 영역은 시스템 패널·분할 상태에 따라 달라집니다. PR #13의 소형 창 UI는 이 APK에 포함하지 않았습니다.

## 실행

1. [저장소 README](../README.md)의 키 없는 MOCK 서버를 같은 PC의8000 포트에서 실행합니다.
2. Pleos Connect 에뮬레이터에 APK를 설치하고 Notice Me를 엽니다. 서버 주소는 `http://10.0.2.2:8000`입니다.
3. 새로고침 후 MOCK 표시와 TOP3를 확인하고 재생합니다. 위치·내비 정보 미수신 시 설정 좌표를 사용했다고 표시합니다.

APK 내부에 FastAPI/실제 DB/원천 API 키가 없습니다. **MOCK도 서버가 필요**하며 단독 오프라인 데모가 아닙니다. 서버 없이는 연결 오류와 카드 제거가 정상입니다. release도 로컬/에뮬레이터 주소3개에만 HTTP를 허용하고 다른 호스트는 HTTPS가 필요합니다. 클라우드 서버는 배포하지 않았습니다.

같은 package의 기존 debug 앱은 서명키가 달라 release로 덮어설치할 수 없습니다. 사용자 데이터 삭제/키 우회를 하지 말고 **별도의 새 AVD**에서 검증하세요. 이번에도 기존 debug 앱/AVD를 유지하고 전용 AVD를 만들었습니다. Windows aapt가 한글 파일 경로를 읽지 못하면 검사용 복사본만 ASCII 경로에 두고 SHA256 동일성을 확인하세요. 공식 제출 파일명은 유지했습니다.

실제 날씨는 고정 관측 지역/관측+1시간/원천 수집이 필요합니다. 이번 release 검증은 MOCK이며 LIVE 재수집은 하지 않았습니다. 실제 날씨·뉴스 메타데이터의 기존 구현과 이전 검증은 [제출 보고서](../docs/RELEASE_SUBMISSION_2026-11-15.md)에 구분합니다. 실차/주행 UX/App Market 승인·STT/Gleo/학교 AI/실제 행사 길찾기는 완료 항목이 아닙니다.

비밀키·비밀번호는 저장소 밖에서 관리합니다. 공개 전 확인 사항은 [보안·라이선스 검토](../docs/PUBLICATION_SECURITY_REVIEW_2026-11-15.md)와 [런타임 구성요소](../docs/verification/2026-11-15-runtime-components.json)를 확인하세요. SDK 원본 AAR/JAR나 SDK 소스를 재배포하는 저장소가 아닙니다.
