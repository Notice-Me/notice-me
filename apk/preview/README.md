# Release 검토 후보

현재 사용자 요청으로 최신 팀원 UI PR #16을 포함해 검증한 파일은 [NoticeMe-0.3.7-pr16-pleos-release.apk](NoticeMe-0.3.7-pr16-pleos-release.apk)입니다. **제출본 자동 교체 승인은 아닙니다.** [실제 결과와 한계](../../docs/RELEASE_UI_PR16_2026-11-15.md) · [manifest](manifest-pr16.json).

|파일|소스|구분|
|---|---|---|
|NoticeMe-0.3.7-pr16-pleos-release.apk|024d1b2 + 팀원6cdd8e3|최신 UI 검토 후보|
|NoticeMe-0.3.7-pleos-release.apk|fa37561 + main09b106b|먼저 검증한 PR #13 UI 참고본|

기존0.3.3 안정 release는 PR #15와 기존 worktree에 그대로 있습니다. compact 실험 APK는 이 폴더에 넣지 않았습니다. 같은 versionName/code라도 UI 소스가 다르므로 파일명·build input commit·SHA256을 함께 확인하세요. 키/비밀번호는 설치자가 필요로 하지 않으며 저장소에 포함되지 않습니다.

APK는 외부 FastAPI 서버가 필요합니다. 기본 주소는 같은 PC의 에뮬레이터에서 http://10.0.2.2:8000이며 MOCK도 서버 데이터입니다. 이번 테스트는 별도 설정으로8001을 사용했고 APK 기본값을 바꾸지 않았습니다. LIVE는 허가된 신선한 고정 지역 날씨만 읽으며 뉴스/미검증 행사는 차단합니다. Pleos Connect2.1/API34/x86_64/2560×1440px/160dpi에서 검증했고 일반 휴대전화·실차·모든 화면 규격의 성공을 보장하지 않습니다.
