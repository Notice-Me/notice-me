# 11/15 GitHub A안 release 제출 준비

2026-11-15 KST. 신청서는 Antigravity에서 별도 수정하므로 이번 작업자는 열어 수정하지 않았다. [공식 안내](https://appdevchallenge.auto-hmg.io/guide/submission)에 맞춰 기존 Notice-Me/notice-me 저장소에 소스와 `apk/`의 실행 가능한 release APK를 준비했다. 사용자 확정 접수 시각은11/15 23:59 KST이며 공식 페이지에서 확인한 것은 접수 마감일11/15다. 접수 메일에는 저장소 URL·최종 commit hash·APK 경로를 적는다. public 전환은11/16까지 별도 사용자 승인 후,11/23까지 유지하는 계획이며 실행/예약하지 않았다.

## 제출 후보

- 기존 main0fe84f9(PR #8·#9·#10) UI/기능0.3.3/code8을 보존했다. 검토한 PR #14의 문서를 기능 브랜치에 fast-forward로 포함했으며 main에 병합하지 않았다.
- APK 빌드 입력 commit: **b2f66f5c6de3a2ad1d54d59c7249ca7c22a656dd**. main 대비 기능 차이는 release 전용 로컬 HTTP whitelist이며, Python·Kotlin·팀원 레이아웃/스타일·권한·API 변경은 없다.
- 파일: [울산동천고듀오_NoticeMe_release.apk](../apk/울산동천고듀오_NoticeMe_release.apk), **24,951,703byte**, SHA256 `7aa31e6b81220bac2ae76c6e86db670ac3d5b9ab06bbe2a622a1ba3aa54cb78d`.
- 실제 pleosRelease를 빌드한 뒤 독립 release 키로 서명했다. manifest/package의 debuggable 비활성, apksigner verify(v3) 성공, 설치/실행 성공을 확인했다. debug 파일을 rename한 것이 아니다. [APK manifest](../apk/manifest.json).
- Pleos Connect2.1/API34/x86_64, 전체 화면2560×1440px·160dpi. 앱 영역은 차량 패널/분할 상태에 따라 다르다. App Market 승인/실차/주행 적합성 완료를 뜻하지 않는다.

## 실제 검증 결과

| 항목 | 이번 실행 |
|---|---|
| 서버 | pytest190 통과, 기존 경고1, Ruff/format39/pip check 통과 |
| Release 빌드 | Pleos·standard 둘 다 성공. 제출/서명/설치는 Pleos만 수행 |
| 단위 테스트 | 실제 존재하는 debug task로 flavor별26 통과, 실패/오류/skip0, 각각 로컬 MOCK HTTP 포함 |
| Release 단위 task | 프로젝트에 없어 첫 task 추정 실행은 실패. task 목록을 확인해 수정했고 release runtime은 별도 실제 검증 |
| Release Lint | Pleos 오류0/경고10, standard 오류0/경고4. 개인 local.properties를 제외한 동일 추적 소스 사본 사용 |
| 서명·정렬 | 독립 프로젝트 인증서·apksigner verify PASS(v3)·zipalign PASS. native16KB 등의 Lint 경고가 해결됐다는 뜻은 아님 |
| 설치·SDK | 기존 debug 앱을 지우지 않고 신규 전용 AVD에서 설치/실행. NAVI_ROUTE/TTS_SERVICE granted 확인, 권한 우회 없음 |
| HTTP | release에서 로컬 MOCK 연결/파싱/화면3건·큐 확인. 서버 HTTP 검사3/5/1은 명시적 SIMULATED DEMO 경로 결과 |
| Pleos 음성·조작 | SDK 발화10회가 모두 HTTP detail.brief와 일치, onDone·오류0. 재생·다음·다시·중단 상태 확인. 사용자 한국어 청취 확인 |
| 서버 미연결 | 연결 오류 표시·기존 MOCK 카드 제거 확인 |
| 실제 LIVE·실차 | 이번 release에서 재수집/실제 날씨 재생·실차·주행 ETA 변화는 미실행. 11/13·11/14 debug 결과와 구분 |
| 외부 호출 | 콘텐츠/라우팅/외부 AI0. SDK 내부 네트워크는 별도 계측하지 않음 |

MOCK이 실제 콘텐츠라는 뜻은 아니다. 실제 날씨는 고정 POI009 지역·원천 관측+1시간·별도 수집이 필요하고, 뉴스 본문/요약/TTS·권리 미확인 행사·미검증 이동시간 차단은 유지한다. 이전 debug APK 두 개와 원본.env/DB/개인 설정/기존 AVD는 보존했다. 이번 검증용 서버·새 AVD 실행은 종료했으며 새 AVD 파일은 삭제하지 않았다. [기계 판독 결과](verification/2026-11-15-release.json).

## release 통신·서명에서 달라진 점

기존 release의 main network config는 모든 HTTP를 차단해 기본 서버 주소로 접속할 수 없었다. 새 release 전용 resource는 기본 차단을 유지하고 **10.0.2.2/127.0.0.1/localhost만** 허용한다. UI XML을 수정한 것이 아니며 다른 HTTP 호스트/전역 cleartext 허용·TLS 우회를 하지 않는다. 최종 APK의 최적화된 compiled resource에서도 이를 검사했다. [Android 네트워크 설정](https://developer.android.com/privacy-and-security/security-config).

기존 release 키는 검색한 개발 위치에서 찾지 못했고 debug.keystore만 확인했다. 사용자가 없는 경우 신규 키 사용을 허용한 뒤 저장소 밖에 PKCS12/RSA3072/유효10000일의 키를 만들었다. 비밀번호는 무작위 생성·Windows CurrentUser DPAPI로 암호화했으며 새 키 폴더만 현재 사용자 ACL로 제한했다. 비밀값은 명령행/로그/Git에 넣지 않고 서명 프로세스의 임시 환경변수로 전달 후 지웠다. 공개 인증서 지문만 [manifest](../apk/manifest.json)에 기록한다. 심사자의 APK 설치에는 이 비밀번호가 필요하지 않다.

서명키를 잃으면 같은 서명의 업데이트를 만들기 어렵다. **사용자는 키와 비밀번호를 개인 보안 저장소에 별도 백업해야 하며**, DPAPI 파일 복사만으로 다른 Windows 계정/PC에서 복구된다고 가정하면 안 된다. 키를 채팅/PR/공개 저장소로 전달하지 않는다. [Android 서명 설명](https://developer.android.com/studio/publish/app-signing).

첫 서명 시 DPAPI 텍스트의 줄바꿈 처리 때문에 실패했지만 Trim 후 정상 복호화/서명·검증했다. 실패 산출물은 제출하지 않았다. Windows aapt는 한글 경로에서 오류가 나서 동일 hash의 ASCII 경로 사본을 검사했고, 원래 한글 파일의 adb 설치는 성공했다. 이는 APK가 손상됐다는 증거와 구분한다.

## PR 순서·UI 동결·마감 계획

1. PR #14는 기존 구현/검증 문서이므로 먼저 승인 병합할 수 있다. 이번 release PR은 그 commit을 포함해 의존 관계를 보존한다. 사용자 승인 전 어떤 PR도 병합하지 않는다.
2. PR #13은 UI 최종 완료·검증 전 병합하지 않는다. 오늘 기본 제출 후보는0.3.3 stable release다. [정적 UI 검토와 최소 제안](PR13_UI_REVIEW_2026-11-15.md)은 팀원 브랜치에서 적용할 자료이며 실제 수정하지 않았다.
3. UI가 확정되면 해당 commit을 다시 검토하고 충돌·버전(현재 PR #13은0.3.7/code13)·권리/날씨 표시 보존을 확인한다. 두 flavor 빌드/검사, **같은 release 키**로 APK 재생성, 설치·재생,README/hash·최종 접수 commit을 갱신한다.
4. 기존 stable commit/APK와 debug 산출물은 보존한다. 새 UI가 검증되지 않으면 현 제출 후보를 유지한다. 마감 전 마지막으로 보낸 전체 제출 자료/commit을 기준으로 관리한다.
5. 저장소 공개 전 [보안·SDK/작성자 정보 검토](PUBLICATION_SECURITY_REVIEW_2026-11-15.md)를 확인하고 사용자가 별도 승인한다. 메일 발송·신청서 수정·공개 전환·팀원 브랜치 수정은 이번에 수행하지 않는다.

최종 제출 commit은 APK를 포함한 이 문서의 후속 commit으로 확정해 최종 답변/로컬 접수 메모에 적는다. 위 build input commit과 혼동하지 않는다. 소프트웨어 실행에는 여전히 외부 FastAPI 서버가 필요하며, MOCK도 내장 오프라인 모드가 아니다. 클라우드 배포·새 AI 자동화·STT/Gleo/길찾기/OR API는 추가하지 않았다.
