# Notice Me 차량 앱 0.3.7 / code13

최종 디자인은 팀원 PR #16(6cdd8e3)입니다. [최종 release APK](../apk/울산동천고듀오_NoticeMe_release.apk) · [소스/APK manifest](../apk/manifest.json).

[루트 README](../README.md)의 실행·설치·검사 절차가 현재 기준입니다. 이번 최종 APK에서 서버의 MOCK brief와 Pleos 한국어 청취를 다시 확인했습니다. Pleos Connect2.1/API34/x86_64/2560×1440px/160dpi, 내비와 앱 각841×1210px 분할 환경에서 검증합니다.

앱은 HTTP health→feed→detail로 실제 서버 응답을 파싱하고 TOP3 및 독립된 alerts/queue/playback_order를 사용합니다. 재생 직전 권리·만료를 다시 검사합니다. Pleos flavor는 SDK ON_DEVICE TTS이며 Standard는 일반 Android TTS입니다. NaviHelper 위치·목적지·ETA 조회를 사용하지만 목적지 생성/미검증 행사 이동시간을 보장하지 않습니다.

MOCK은 서버의 자체 작성 모의 자료입니다. LIVE 음성은 허가된 신선한 고정 지역 날씨만 허용합니다. 과거 LIVE 날씨 청취와 이번 최종 APK의 MOCK 재검증을 구별합니다. 서버가 없으면 APK만으로 콘텐츠를 제공하지 않습니다. onStop에서 TTS를 중단합니다.

기존0.3.3 및 preview/compact APK는 이 제출 트리에 포함하지 않으며 다른 브랜치/로컬 백업으로 보존합니다. 새 빌드는 저장소 밖의 기존 release 키로 서명해야 합니다. 개인 설정·인증키·SDK 원본·DB는 커밋하지 않습니다. [최종 검증](../docs/FINAL_SUBMISSION_2026-11-15.md) · [보안 감사](../docs/PUBLICATION_AUDIT_2026-11-15.md).
