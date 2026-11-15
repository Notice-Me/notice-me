# 제출 APK 의존성과 제3자 고지

0.3.7/code13 Pleos release의 실제 `pleosReleaseRuntimeClasspath` resolved artifact70개를 확인했다. [정확한 좌표·POM license·archive notice·원문 hash](licenses/android-runtime-inventory.json)를 참조한다. 이 문서는 앱/SDK 전체에 새 라이선스를 부여하는 문서가 아니다.

AndroidX/Material, Kotlin/coroutines/serialization, Gson, OkHttp/Okio, Tink, annotations 등은 각 배포 POM에 Apache2.0을 기재한다. 원문 [Apache2.0](licenses/Apache-2.0.txt)을 함께 제공한다. Guava listenablefuture1.0은 빈 호환 artifact이며 자체 POM의 license는 비어 있지만 parent guava-parent26.0-android의 Apache2.0을 확인했다. 메타데이터가 없는 값을 임의 생성하지 않았고 parent 출처를 inventory에 남겼다.

JNA5.13.0은 upstream notice에서 Apache2.0 또는 LGPL2.1 이상 중 선택 가능함을 명시하며 이 배포에서는 Apache2.0을 선택한다. [원래 JNA notice](licenses/oss-521bb271ac56e0e2.txt)를 그대로 보존한다. OkHttp publicsuffixes.gz는 Public Suffix List에서 컴파일한 자료로 [원래 notice](licenses/oss-8a9c58fbded5ea34.txt)와 [MPL2.0](licenses/MPL-2.0.txt)을 제공한다. 원천과 원형은 [Public Suffix List](https://publicsuffix.org/list/) 및 OkHttp4.12.0의 원래 배포 자료를 따른다. 해당 자료를 수정하지 않았으며 APK에 기존 notice/resource도 유지한다.

Pleos TextToSpeech3.3.1, NaviHelper3.0.5와 전이 의존성 navi-data3.0.4/navi-aidl3.0.1/universal-access0.6.0의 POM/배포 archive에서는 LICENSE를 확인하지 못했다. 이들은 Apache2.0으로 재라이선스하지 않는다. 공식 SDK 계정 약관/공모전 조건을 적용하며 **SDK 원본 바이너리·소스·시스템 이미지 자체는 저장소에 배포하지 않는다**. APK compiled runtime 포함과 SDK 원본 재배포의 차이 및 남은 해석은 [공개 감사](PUBLICATION_AUDIT_2026-11-15.md)에 기록했다.

앱과 함께 실행하는 Python 서버는 [고정 의존성](../server/requirements.lock)을 별도로 설치한다. 서버·실데이터·API 키는 APK에 내장되지 않는다. 서울시 등 데이터 출처의 이용조건은 [DATA_SOURCES](DATA_SOURCES.md), 자체 MOCK 자료는 [FIXTURE_LICENSE](FIXTURE_LICENSE.md)를 따른다. 뉴스·행사의 표시/음성 권한을 SDK 사용권과 혼동하지 않는다.

OkHttp4.12.0의 수정하지 않은 Public Suffix 리소스와 관련 소스는 [해당 버전 공식 Maven source archive](https://repo.maven.apache.org/maven2/com/squareup/okhttp3/okhttp/4.12.0/okhttp-4.12.0-sources.jar)에서 구할 수 있다. 이번에 source archive의 publicsuffixes.gz와 APK의 동일 entry 바이트가 일치함을 확인했다. source archive SHA256 `d91a769a4140e542cddbac4e67fcf279299614e8bfd53bd23b85e60c2861341c`.
