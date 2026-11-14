# 공개 전 보안·개인정보·외부 자료 검토 — 2026-11-15

이 문서는 공개 승인 자체가 아니다. 저장소는 비공개로 유지하며 사용자 별도 승인 전 visibility·권한·기존 이력을 변경하지 않는다. [공식 제출 안내](https://appdevchallenge.auto-hmg.io/guide/submission)의 A안과 [release 제출 결과](RELEASE_SUBMISSION_2026-11-15.md)를 함께 확인한다.

## 조사 범위와 결과

초기 audit 기준 HEAD b2f66f5에서 로컬 및 fetch한 모든 참조에 도달 가능한 **48개 commit·362개 blob·3,400,973byte**를 읽었다. GitHub PR #1~#14의 head object가 모두 이 로컬 조사 범위에 있음을 확인했다. main만 검색하거나 현재 파일 삭제 여부만 확인한 검사가 아니다. 이번에 추가하는 문서/서명 APK는 commit 전후 별도 검사한다. 이후 새 commit/브랜치/PR이 생기면 그 범위는 다시 확인해야 한다.

| 항목 | 관측 | 판정·후속 |
|---|---|---|
| 실제 설정된 API 키·인코딩 변형 | 전체 도달 가능 blob에서 미발견 | 알려진 값 기준 통과. 미지의 모든 비밀을 증명하는 DLP 인증은 아님 |
| 일반 토큰 패턴·PEM private key | 미발견 | 새 release 키/암호는 저장소 밖에 보관. 공개 인증서 지문과 구별 |
| .env·DB·개인 설정·단말 로그·스크린샷·신청서 | 해당 민감 확장자/파일의 추적 이력 미발견 | 로컬에는 별도 존재하므로 폴더 전체 압축/무차별 git add 금지 |
| 위치처럼 보이는 숫자 | 7개 blob 후보 | JSON4개는 timestamp 소수초 오탐, 나머지는 공개 행사장 좌표/문서와 합성 검사 fixture. 실제 사용자 위치·목적지 이력 발견 없음 |
| 소스의 이메일 | 폐기된 PR #11의 테스트1개 | example.invalid 합성 입력이며 실제 연락처 아님 |
| Git 작성자·커미터 metadata | 고유 identity5개, 비-noreply 이메일2개 | **공개하면 기존 작성자 이름·이메일도 노출될 수 있음.** 실제 값은 보고서/Git에 재복제하지 않고 로컬 private 검토 파일에만 정리. 팀원 확인 필요 |
| 닫힌 PR·미병합 브랜치 | #11·#12 등도 참조 이력에 포함 | 제출 APK에서 제외해도 저장소 공개 범위에서는 볼 수 있음. 사용자 승인 없이 브랜치 삭제·이력 재작성 없음 |

Git 작성자 정보가 원치 않는 공개라면 현재 파일을 지우는 것으로 해결되지 않는다. 공유 이력·PR·원격 참조의 처리 범위를 먼저 합의해야 하며, 이번에는 reset/force push/이력 재작성·브랜치 삭제를 하지 않았다. 실제 유출 키가 발견된 경우에도 파일 삭제만으로 해결됐다고 하지 않고 폐기/재발급과 이력 정리를 별도 다뤄야 한다. 이번에는 해당 유출을 관측하지 않았다.

현재 제출 APK의 인증서는 공개 식별 정보이며 private key가 아니다. 개인 이름·이메일 대신 프로젝트 식별명으로 발급했다. 기존 debug 키와 새 release 키는 다르다. 서명키 원본·Windows DPAPI 암호 파일·비밀번호·개인 SDK 설정은 APK·소스·PR에 포함하지 않는다.

## SDK·소프트웨어·콘텐츠 권리

- SDK 원본 AAR/JAR/에뮬레이터 이미지/단말 로그를 Git에 추가하지 않았다. 기존 Gradle wrapper는 빌드 도구이며 제출 APK에는 빌드 결과로 의존 라이브러리가 포함된다.
- 실제 pleosReleaseRuntimeClasspath를 offline Gradle로 조회하고 cached POM의 라이선스 metadata를 [구성요소 목록](verification/2026-11-15-runtime-components.json)에 기록했다. metadata는 계약 적합성을 확정하는 법률 판단이 아니다.
- Pleos TTS3.3.1·NaviHelper3.0.5·navi-data3.0.4·navi-aidl3.0.1·security universal-access0.6.0의 POM/AAR에서 명시적 LICENSE/NOTICE를 찾지 못했다. Guava listenablefuture1.0도 조회한 POM에 라이선스 metadata가 없다. 이를 임의의 Apache/MIT 허가로 대체하지 않는다.
- [공모전 개발 안내](https://appdevchallenge.auto-hmg.io/guide/development)는 SDK 활용과 공식 문서 확인을 안내하고 [제출 안내](https://appdevchallenge.auto-hmg.io/guide/submission)는 APK 제출을 요구한다. 이 사실만으로 SDK 원본의 범용 재배포·상용 출시 권한까지 확보됐다고 단정하지 않는다. **공개 전 계정의 SDK 이용약관/배포 조건을 사용자·팀이 확인할 사항**으로 남긴다.
- 프로젝트 전체에 적용할 LICENSE를 임의로 추가하거나 SDK 코드를 오픈소스라고 재허가하지 않았다. 별도 이용 조건이 있는 코드를 포함한 APK의 배포 조건과 프로젝트 자체 라이선스 선택은 구분한다.
- 뉴스는 원문/임의 요약/음성 차단을 유지하고 metadata만 사용한다. 실제 DB·원문 기사 본문·포스터는 새 제출 파일에 없다. 실제 행사 이동시간·권리 게이트도 그대로다.

## 공개 전 최종 확인

1. 새 제출 commit의 소스·APK hash와 비밀값 검사 결과를 확인한다.
2. 작성자 metadata 노출, 미병합 팀원 브랜치 공개 범위, SDK 조건을 팀과 확인한다.
3. 사용자 별도 승인 후 11/16까지 public 전환하고 11/23까지 유지하는 계획을 실행한다. 이번 작업자가 전환하거나 예약하지 않았다.

이 검사는 정적 파일/이력·제출 APK 검토다. 악성코드·취약점·개인정보·모든 라이선스 문제의 부재를 포괄적으로 보증하지 않는다. 키/개인 원문/정밀 위치를 외부 AI나 공개 보고서로 보내 검증하지 않았다.
