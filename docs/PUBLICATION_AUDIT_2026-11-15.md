# Notice Me 공개 전 보안 감사

2026-11-15 KST 검사. **기술 보안 검사 PASS, 종합 공개 판정은 조건부 PASS / 실제 공개 전환은 사용자 승인 대기**다. 이번 범위에서 실제 인증키·서명 암호·개인 DB·정밀 이동 이력은 발견하지 않았다. 비밀값 부재나 모든 제3자 권리의 법률적 보증은 아니다. main 병합·공개 전환·이력 재작성·브랜치 삭제·메일 발송은 하지 않았다.

## 검사 범위와 방법

시작 main09b106b, 최종 코드 검증 commit f5f194a를 기준으로 `git fetch origin --prune` 후 열린/닫힌 PR #1~#18 **모든 head**를 별도 로컬 audit ref로 읽었다. 초기 스냅샷은 **53 refs /60 commits /912 reachable objects /446 blobs /84,858,639 bytes**다. 최종 문서 commit에 대해서도 commit/push 전후 재검사한다. 도달 불가능·서버 내부 삭제 객체·외부 fork·타인의 미push 작업은 조회 범위 밖이며 보호했다. 모든 기존 브랜치·worktree·PR을 그대로 유지했다.

- 공식 Gitleaks8.30.1 portable를 저장소 밖에 두고 다운로드 checksum을 확인했다. `git --all --full-history`, 디코드 검사와 redact100을 사용했다. 보고서 template은 Secret/Match/Line/Author/Email/Message를 아예 제외하여 검출 원문을 별도 저장하지 않았다. CI나 자동 개발 시스템은 추가하지 않았다.
- 직접 모든 reachable blob를 읽고 키/인증서/DB/로그/개인 양식 경로, private-key header를 검사했다. 기존 로컬 .env의 실제 키2개와 release 암호1개는 메모리에서만 원문·URL encoding variants 대조했다. 보고서/명령줄에 값은 출력하지 않았다.
- 이력의 APK **3개**를 ZIP 해제해 리소스·DEX·native payload를 같은 방법으로 검사했다. 최종 APK 하나만 보았다고 전체 이력 검사로 표시하지 않았다. SDK를 decompile/수정하거나 권한을 우회하지 않았다.
- PR18개 본문/제목, issue/review comment API, Actions runs/artifacts, Release 목록을 확인하고 텍스트를 별도로 Gitleaks 검사했다. 댓글0/Actions0/artifact0/Release0이었다. PR 본문 스캔은 검출0.
- Git author/committer를 모두 확인했다. PNG13개는 별도 사본의 contact sheet로 직접 확인했다. raw 로그·SQLite·신청서·개인 연락처·정밀 위치를 새 공개 자료에 포함하지 않았다.

## 결과와 예외

|항목|결과|
|---|---|
|실제 기존 키/서명 암호 일치|0건. 실제 값을 보고서에 복제하지 않음|
|private-key header / 민감 경로|0건. `.env.example`의 예제와 Gradle wrapper JAR는 구분|
|JKS/PKCS12/PEM 원본|모든 reachable Git에서 발견0. 키는 저장소 밖의 기존 Windows DPAPI 보관을 유지|
|개인 DB/단말 로그/신청서 파일|tracked 이력 발견0. 원본 DB·개인 양식·raw log는 업로드하지 않음|
|APK 내부|실제 키/서명 암호 일치0, 민감 파일명0. 공개 인증서/서명 블록은 private key가 아님|
|Gitleaks Git 이력|경고2건. 아래 공개 검증 SHA256 필드로 분류. 검출을 숨기기 위한 allowlist/baseline은 추가하지 않음|
|좌표 직접 검사|54개 텍스트 버전의 좌표는 소스 fixture/테스트 예제와 서울시 공개 행사장 메타데이터. 개인 이동 이력 발견0. JSON 숫자 좌표에 대한 보완 검사 수행|
|텍스트 연락처|테스트의 example domain fixture만 발견. 개인 연락처 파일 발견0|
|PNG13개|MOCK/가상 긴 제목/에뮬레이터 화면. 개인정보·실제 이동 경로·키 표시 발견0. Pleos 화면 자체의 권리까지 소유한다고 주장하지 않음|
|Git 작성자/커미터|비-noreply 주소2개. 사용자에게 노출 범위를 설명했고 **두 작성자 모두 공개 동의**를 받았다는 사용자 답변 확인. 주소 원문은 이 보고서에 복제하지 않음|

Gitleaks의 exit1은 “실제 유출2개”가 아니다. `docs/verification/2026-11-11-vehicle-handoff.json`의 b22c1e2…:330은 `server/scripts/check_vehicle_api.py`의 SHA256이며 당시 파일을 재계산해 일치했다. `docs/verification/2026-11-11-revalidation.json`의00104b0…:323은 `openapi_sha256`라는64hex 검증 fingerprint이고 실제 키/키 hash와 다르다. 두 번째는 당시 응답의 원본 직렬화 bytes를 확보하지 못해 동일 값을 재계산한 것은 아니다. 문맥/필드/형태와 실제 키 대조로 인증정보가 아닌 공개 아티팩트 hash로 분류했다. [위치·분류만 담은 기록](verification/2026-11-15-final/gitleaks-triage.safe.json).

새 보고서에는 위치와 유형만 기록한다. 발견된 민감 문자열을 “삭제했으니 해결”로 처리하거나 force push하지 않았다. 향후 진짜 비밀값이 확인되면 우선 폐기/재발급과 노출 범위를 보고하고, 이력 정리는 별도 승인 후 결정해야 한다.

## Git 이메일과 공개 범위

현재 private 저장소는 권한 있는 사용자에게 Git metadata가 보인다. 비로그인 commit API 요청은 이번에404였다. Public으로 바꾸면 과거 브랜치와 commit의 작성자/커미터 이메일을 누구나 clone·git log·API로 볼 수 있다. 프로필 이메일 비공개 설정을 바꿔도 기존 commit을 소급 수정하지 않는다. GitHub의 `noreply@github.com` 웹 merge 및 `users.noreply.github.com` 주소는 개인 주소2개에 포함하지 않았다.

근거: [GitHub commit 이메일 안내](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address), [visibility 변경 안내](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility). 앞으로 새 commit에 noreply를 쓸지는 팀이 선택할 수 있지만 이번에는 글로벌 Git 설정/기존 작성자/이력을 바꾸지 않았다.

PR #11/12를 닫았거나 #15/18을 제출에서 제외해도 원격 브랜치·PR head·이력은 남는다. Public 전환은 최종 tree만 공개하는 동작이 아니다. 이번 감사는 그 이전 작업까지 포함했고 실제 secret는 발견하지 않았다. 미push 팀원 파일은 검사하거나 덮어쓰지 않았다.

## SDK와 제3자 권리

모든 Git 이력의 AAR/JAR 경로는 **Gradle wrapper JAR만**이며 Pleos SDK 원본/시스템 이미지/계정 토큰을 올리지 않았다. APK에는 앱 실행에 필요한 compiled dependency가 포함되어 있다. 이 둘은 구분한다. 이번 실제 resolved Pleos runtime artifact는 **70개**다. POM license와 배포된 archive 내 LICENSE/NOTICE를 직접 확인하고 [의존성·고지](THIRD_PARTY_NOTICES.md), [정확한 inventory](licenses/android-runtime-inventory.json), 필요한 표준 license/기존 notice를 함께 제공했다. JNA는 upstream의 Apache2.0 선택을 명시했고, OkHttp의 Public Suffix List에 대한 MPL2 notice도 보존했다.

Pleos의 TextToSpeech3.3.1, NaviHelper3.0.5, navi-data3.0.4, navi-aidl3.0.1, universal-access0.6.0 POM/배포 archive에서는 명시적 LICENSE를 찾지 못했다. 빈 POM license를 오픈소스 허가로 해석하지 않는다.

**공모전 범위의 공식 근거:** [개발 환경](https://appdevchallenge.auto-hmg.io/guide/development)은 Pleos/NaviHelper/TTS SDK 사용과 에뮬레이터 검증을 안내하고, [제출 안내](https://appdevchallenge.auto-hmg.io/guide/submission)·[FAQ](https://appdevchallenge.auto-hmg.io/faq)는 소스+실행 가능한 APK를 GitHub에 두고11/16까지 Public으로 전환하도록 명시한다. 사용자가 지정한 `contest-application-consent.docx` 원본도 읽기 전용으로 확인했고 GitHub/APK 선택 제출·기획서·동의/서명 안내가 일치했다. 원본에는 SDK 원본 재배포를 별도로 허가하는 문구는 찾지 못했다.

한편 [Pleos Playground 약관](https://developers.pleos.ai/playground/external/use-policy?locale=ko-KR&partnerId=hmg-kr-42dot-developers)은 개발도구 제3자 제공·성능 분석/테스트 결과 공개 등에 제한을 둔다. 이번 공식 공모전 안내는 **공모전용 앱 소스·compiled APK·동작 증거 제출을 뒷받침하는 근거**로 해석한다(검토자의 해석이며 개별 서면 허락 확인과 동일하지 않음). 원본 SDK 배포, SDK 자체 benchmark/내부 구현 공개, 상업 서비스·Market 배포까지 포괄 허용되었다고 판단하지 않는다. 이번 문서는 Notice Me의 기능 검증이며 SDK 성능 벤치마크가 아니다. 공모전과 계정별 SDK 약관의 우선관계를 명시한 별도 조항/개별 허락 자료는 확인하지 못했으므로 **권리 검토 한계는 남는다**. 사용자가 더 엄격한 허락 확인을 원하면 공식 운영자에 제출 범위 적용을 문의할 수 있다. 이번에 문의 메일은 발송하지 않았다.

## 최종 판정과 승인 경계

- 인증정보/개인 DB/단말 로그 기술 검사: **PASS(명시된 범위 내)**.
- 비-noreply2개 이메일 공개: **사용자 확인상 전원 동의**. 강제 이력 수정 불필요.
- 공모전용 앱 소스·APK 공개: 공식 제출 안내를 근거로 **조건부 PASS**. SDK 원본 재배포·상업 이용의 허가 판정은 아님.
- 저장소 실제 Public 전환: **수행하지 않음 / 사용자 최종 검토·별도 승인 대기**. main 병합과 메일 발송도 동일.

새 commit·브랜치·PR·이미지가 추가되면 범위를 갱신해 다시 검사해야 한다. 이번 결과는 취약점 진단/모든 저작권 심사/실차 안전성 인증을 대신하지 않는다.
