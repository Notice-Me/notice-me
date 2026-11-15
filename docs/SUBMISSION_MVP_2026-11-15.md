# 2026-11-15 1차 접수용 MVP 준비 결과

확인일: 2026-11-14 KST. 이번 접수는 **참가신청서·기획서 제출**이며 현장 시연이 아니다. APK·GitHub·영상은 추가 검토 자료다. 신청서 원본 DOCX와 팀원 정보는 수정하지 않았다. [기계 판독 검증 결과](verification/2026-11-14-submission.json), [현재 실행 방법](../README.md).

## 제출 기준과 변경 범위

- 기준: PR #8·#9·#10이 병합된 main `0fe84f9bb5b06141f8b48bb1862060c7ff201ee6`.
- 작업: `feat/submission-mvp`. 서비스 Python·Kotlin·UI·Gradle·권한·API 계약은 변경하지 않았다. README·제출 보고서·한국어 개발 기록만 갱신했다.
- 제외: 미병합 PR #11(자동화), #12(이전 UI), #13(팀원 반응형 UI). #13의 MainActivity·레이아웃·버전 변경을 복사하거나 수정하지 않았다. 사용자 승인 전 병합/자동 병합하지 않는다.
- APK: 0.3.3 / versionCode8, compileSdk37 / minSdk28 / targetSdk34. Pleos TTS3.3.1 ON_DEVICE, NaviHelper3.0.5. 실제 실차/스토어 출시용 앱이 아니라 정차 검증용 debug 빌드다.

## 이번에 실제 실행한 검사

| 검사 | 결과 | 근거·제한 |
|---|---|---|
| FastAPI pytest | 190개 통과, 기존 deprecation 경고1 | 임시 DB·MockTransport/fixture 시험 포함. 실제 제공자 성공과 구분 |
| Ruff·format·pip check | 통과 /39파일 포맷 일치/의존성 충돌 없음 | 서비스 코드 변경 없음 |
| 두 flavor assemble | 둘 다 성공 | 기존 캐시로 offline 빌드, 새 SDK/유료 서비스 설치 없음 |
| Pleos·standard 단위 테스트 | 각각26개, 실패/오류/skip0 | 각 flavor에 실제 로컬 MOCK HTTP1개 포함. 총52회이며 서로 다른52개 기능이라는 뜻은 아님 |
| 첫 통합 Gradle 실행 | Lint에서 실패 | 개인 local.properties의 `C:/...` drive 구분자 escape 검사. APK·단위 테스트는 성공했으나 전체 명령은 실패로 기록 |
| Lint 재검사 | Pleos 오류0/경고12, standard 오류0/경고4 | 원본 개인 설정을 보존하고 추적 소스만 동일한 별도 사본에 복사. ANDROID_HOME 지정 후 성공 |
| APK 서명 | 둘 다 apksigner verify 성공, v2 서명 | Android Debug 인증서. release 서명/스토어 배포 승인 아님 |
| 설치 | Pleos·standard 둘 다 SUCCESS | 기존 Pleos Connect2.1/API34 x86_64 AVD, install -r. 앱 데이터 삭제/권한 우회 없음. standard 음성은 재생하지 않음 |
| 실제 MOCK HTTP | health/feed/detail/explain 및 오류·권리 검사 성공 | TOP3=3, queue=5. 긴급정보는 모의 링크·10분 유효기간 조건에 따라 달라짐 |
| 실제 LIVE HTTP | health/feed/detail/explain 검사 성공 | TOP3=날씨1+뉴스metadata2, queue=날씨1, alerts=0. 뉴스2건 음성 false/설명403 |
| 기기 MOCK 재생 | 서버 brief 일치·SDK 완료·연속5개 확인 | 재생·다음·다시·중단 UI/SDK 확인. 사용자도 이번 APK의 한국어 음성 청취 확인 |
| 기기 LIVE 날씨 | 최신 detail.brief와 Pleos doSpeak 정확히 일치, onDone 확인 | 일반 Android TTS/하드코딩 예문 아님. 이번 LIVE 청취는 미확인, 11/13의 사용자 청취 기록은 별도 이력 |
| 서버 미연결 | 연결 오류 표시·이전 카드 제거 확인 | APK 내부의 임의 예문/오프라인 정보로 대체하지 않음 |

남은 Lint 경고는 대상 API/아이콘/백업 규칙/전이 native16KB 정렬/의존성·KTX 관련이다. 오류0이 출시 준비 완료를 뜻하지 않는다. Windows 창 캡처는 helper timeout과 모니터 범위 오류로 실패했으므로, Android SDK의 설치·화면 dump/캡처·기기 입력·앱 PID 로그를 이용했다. 이를 성공한 Windows 창 자동화로 기록하지 않는다. [과거 11/13 기기 검증](verification/2026-11-13-live-weather-vehicle.md)과 이번 결과를 합쳐 새로운 실차 검증이라고 표시하지 않는다.

## 외부 데이터와 호출 예산

원본 DB를 read-only SQLite backup으로 별도 시연 사본에 복제했다. `seoul_city` **실제1회·재시도0·HTTP200·정규화1건**만 갱신했다. 관측은 **11/14 18:20 KST, 광화문·덕수궁10.7도, 만료19:20 KST**다. 이 자료가 내일까지 유효하다는 뜻이 아니다. FreeNews/TourAPI/다른 공공 제공자·라우팅·외부 AI 호출은0회다.

날씨는 고정 관측 지역이며 현재 위치/목적지 날씨가 아니다. 관측+1시간이 지나면 다시 수집하기 전 LIVE 큐0건이 정상이다. 원본.env·DB·개인 설정은 보존한다. 별도 시연 DB·원본 로그·개인 위치는 제출 소스/PR에 포함하지 않는다.

## 제출용 산출물과 식별

로컬 `$SubmissionDir/artifacts/`에 준비한다. 사용자에게 전달하는 최종 답변에 실제 절대 경로를 기재하며 개인 PC 경로는 GitHub에 올리지 않는다.

| 파일 | 용도 | SHA256 |
|---|---|---|
| Notice-Me-0.3.3-pleos-debug.apk | Pleos 검토용 | `3f3832a7231ea6945cdda41e6b8fbd051f17dc257f8760720b4ffa80943a830f` |
| Notice-Me-0.3.3-standard-debug.apk | 일반 Android 비교용 | `935cf2fd40dd6e5b492087654313d524fa414fbe8b094eacf2bed865a21c5524` |
| Notice-Me-source-커밋.zip | 최종 기능 브랜치 commit의 추적 소스 | 압축 이후 동봉 artifact-manifest.json에 commit·해시 기록 |
| Notice-Me-MOCK-screen-only.mp4 | 약40초 화면 검증 영상 | **무음**, MOCK 화면·재생 상태 자료. 실제 음질·LIVE·내비/실차 증거로 쓰지 않음 |
| Notice-Me-LIVE-weather.png | 고정 지역/시각/출처와 LIVE 표시 | 실제 위치 사용을 끈 상태로 촬영. 뉴스는 metadata만 표시 |
| SUBMISSION.txt / artifact-manifest.json | 파일·commit·해시·실행 한계 | APK와 함께 검토할 설명 자료 |

서명 인증서 SHA256은 `0e722f28c16b258c38450149259eee0550a9c8c82c7a639786d1fe88f7ea4a8d`다. 이는 APK 파일 해시와 다르다. APK 구현 소스는 위 main과 같고, 최종 ZIP commit에는 제출 문서 갱신도 포함한다. ZIP은 git archive의 추적 파일만 사용하므로 로컬 `.env`·DB·빌드 캐시·이전 자동화 산출물·미추적 팀원/자문 파일을 포함하지 않는다.

## 심사자가 APK만 설치할 때의 한계

1. 앱 내부에 FastAPI·실제 DB·API 키가 없다. **MOCK도 외부 서버가 필요**하다. 서버 없이는 연결 오류가 정상이다.
2. Pleos flavor는 실제 Pleos TTS·내비 서비스와 권한이 있는 에뮬레이터/기기에서 사용한다. 일반 Android 설치 성공만으로 해당 SDK가 동작하지 않는다.
3. 같은 PC AVD는 `http://10.0.2.2:8000`으로 로컬 서버에 연결한다. 다른 PC/LAN 주소는 debug HTTP 허용 목록·네트워크 설정이 필요하다. 공개 서버·인증·TLS 배포는 이번에 하지 않았다.
4. 일반 flavor는 다른 패키지와 일반 Android TTS를 사용하며 Pleos 검증을 대신하지 않는다. 실패 시 자동 fallback하지 않는다.
5. 내장 MOCK 데모는 작은 별도 기능으로 검토할 수 있으나 데이터/권리/모드·detail 재검사 계약을 함께 설계해야 한다. 마감 전 서버 경로를 바꾸는 구현은 추가하지 않고, 키 없는 기존 MOCK 서버와 화면 영상으로 보완했다.
6. 저장소는 private이다. GitHub URL을 적는 것만으로 심사자 접근을 보장할 수 없으며 공개 전환/외부 접근 허용은 별도 사용자 승인 대상이다. 실제 신청서 제출·파일 업로드도 수행하지 않았다.

## 신청서에 반영할 기술적 사실

다음 문구는 기획서에 옮길 수 있는 기술 요약이며, 원본 신청서를 대신 수정한 것이 아니다.

> Notice Me는 Pleos 차량 환경에서 위치·목적지·도착 예상 시간과 관심사를 활용해 소식을 추천하는 MVP를 구현했다. FastAPI·SQLite 서버가 화면 TOP3와 별도의 음성 큐를 제공하고, Kotlin 앱은 최신 상세 정보의 권리·유효성을 재검사한 뒤 Pleos 기기 내 TTS로 재생한다. 실제 서울시 고정 지역 날씨와 MOCK 소식을 통한 서버-앱 연결을 검증했으며, 뉴스는 제목·출처·원문 링크 등 메타데이터만 제공한다. 현재는 정차 시연용 개발 단계로, 실제 주행 적합성과 상용 배포는 후속 검증 대상이다.

최종 기획과 현재 코드의 차이는 다음처럼 적는다.

| 기획 | 현재 | 후속 목표 |
|---|---|---|
| 긴급·안전 > 지역·개인 관심사 > 화제 > 일반 | 조건을 충족한 교통 alerts 우선, 일반 후보는 관심사·지역·신선도 등의 점수. 앱의 실제 도로 링크 전달/긴급 연동은 미완료 | 단계별 우선순위 정책과 안전 정보 종단 검증 |
| 장거리 음성 큐 확장 | TOP3와 큐는 분리. 현재 큐를 ETA 예산에 맞춰 줄이는 기능 구현 | 지역 자료가 부족하면 권리가 확인된 개인 관심사·화제 후보로 확대. 현재 화제 수집/보충 로직은 없음 |
| 팝업 발견·추천 | 공공 수집기·공식 확인 입력 경로, 이동시간 미검증 후보 차단 | 공식 웹 공지·SNS·허용된 제공자에서 후보 발견 후 일정/장소/좌표/변경/권리/이동시간 검증 |
| 개인 관심사 프로필 | 구체 주제와 형식의 상세 검색 및 다국어 별칭 | 독립 관심사 OR와 상세 검색 AND를 분리한 계약 합의·구현 |

민간 뉴스 본문 낭독·실제 자동차60분 행사 추천·STT·Gleo·학교 AI·실제 생성형 요약·앱 목적지 생성은 완료 기능으로 기재하지 않는다. 출처 사용권·SDK 권한·계정/비용이 확인되지 않은 기능은 개발 목표로만 구분한다.

## 마감 전 사용자 결정과 이후 개발

- 준비한 APK·영상·소스 ZIP을 추가 자료로 제출할지 선택하고, 신청서의 최종 기능 범위를 이 보고서와 맞춘다.
- 비공개 GitHub 링크의 접근 방식과 PR 병합 여부는 사용자가 결정한다. 검토 전 main을 변경하거나 공개 저장소로 전환하지 않는다.
- 1차 제출 후 첫 서버 기능 후보는 **독립 관심사 OR 프로필/상세 AND 검색 분리**다. 기존 GET 계약·날씨/MOCK 유지, 앱 담당자와 요청 계약 합의 후 별도 서버 PR에서 구현한다. 그다음 실제 행사·라우팅·권리·사용량 조건을 검증한다. 잡음은P2다.
