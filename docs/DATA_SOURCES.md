# 데이터 출처·조건·실제 검증

확인일 **2026-11-11 KST**. 공식 문서 읽기, HTTP 응답 수신, 정상 데이터 수신, 추천 노출, TTS 허가를 구분합니다. 초기 측정값은 [API_VALIDATION_RESULTS.json](API_VALIDATION_RESULTS.json), 초기 서버 HTTP는 [HTTP_SMOKE_RESULTS.json](HTTP_SMOKE_RESULTS.json)입니다. 인증정보와 원본 기사 본문은 포함하지 않습니다.

**20시대 차량 인계 재현:** [최신 측정](verification/2026-11-11-vehicle-handoff.json). 서울시 도시데이터의 공식 공개 범위/공공누리1유형을 다시 확인하고 기존 어댑터로 날씨만1회 수집했습니다(200/정규화1건). FREE 뉴스 추가 호출0회, 기존 실제 뉴스2건은 권리 미확인으로 음성/설명 차단을 재확인했습니다. MOCK/LIVE/MIXED HTTP 검사에 추가 원천 호출은 없었습니다. 기존 날씨 필드의 허가를 다른 도시데이터 영역이나 언론사 기사에 확대하지 않습니다. 실제 Pleos TTS 출력은 미검증입니다.

**같은 날 18시대 KST 재검증:** [새 보고서](verification/2026-11-11-revalidation.json)에 별도 보존했습니다. 서울시 sample에서 현재 행사5·날씨1·교통5건을 다시 수신/정규화했습니다. 아래의 교통4건 등은 초기 호출의 역사적 수치입니다. 뉴스/TourAPI 키는 여전히 미설정이고 이번에는 뉴스 무인증 요청을 반복하지 않았습니다. 실제 뉴스 검색·건수·중복률·TTS 라이선스를 확인했다고 주장하지 않습니다. 이 회차에는 권리 정책을 확대하지 않았으며, 기존 차단 정책을 유지했습니다. 공식 도시데이터 안내는 다시 조회했지만 모든 제공자 약관을 새로 재검토한 기록은 아닙니다.

## 뉴스 비교

**최신 FreeNews 인증/오류 조사:** [상세](FREENEWS_INVESTIGATION.md), [실측 JSON](verification/2026-11-11-freenews-investigation.json). 현재 키 로딩/인증된 검색을 확인했고 실제 뉴스2건을 metadata로 저장했습니다. 아래의 초기 무인증401은 과거 관측입니다. 다른 두 제공자의 인증 상태는 이번에 새로 검증하지 않았습니다. 뉴스 권리 등급은 변경하지 않습니다.

| 항목 | FreeNewsAPI (.io, 1순위) | The News API (.com) | GNews |
|---|---|---|---|
| 무료 한도 | 5,000 요청/일, 2 요청/초 | 100 요청/일, 응답당 기사 3건 | 100 요청/일, 응답당 10건; 12시간 지연, 과거 30일 |
| 한국어/한국 공식 지원 | ko/KR 필터의 실제 예술 검색200/metadata5건 확인. 전체 coverage는 미측정 | 문서에 `language=ko`, `locale=kr` 명시 | 현재 공식 검색 문서의 언어/국가 목록에 ko/kr 없음. 한국어 키워드 요청만 준비; 한국 뉴스 확보는 미검증 |
| 검색 | `/v1/news`의 `in_title`; 현재 스키마는 q/in_body/in_subtitle 제거 | `/v1/news/all`, `search` | `/api/v4/search`, `q`; 지원되지 않은 lang/country를 추측해 넣지 않음 |
| 제목/설명/출처/발행시각/URL | 목록: uuid,title,publisher,published_at. `/details`: original_url,incipit,body | title,description,source,published_at,url | title,description,source,publishedAt,url |
| 24시간/7일 기사 수 | 과학 IT24h0, 예술24h5/168h첫10·추가 페이지 있음. 전체 count는 미제공 | **미측정** | **미측정**; 무료 최신 12시간 공백도 고려 필요 |
| 애니메이션/과학IT/예술 | 애니메이션500 재현, 과학 IT168h 기존TIMEOUT→별도20초 대기 관측에서0건. 원인은 미확정 | 스크립트 준비, 인증 미확보 | 스크립트 준비, 한국어 corpus/필터 제한 명시 |
| 초기 무인증 호출 (이전 관측) | **HTTP 401** | **HTTP 401** | **HTTP 400**, 응답이 API 키 미전송을 명시 |
| 사건 중복 비율 | 예술 반환5/10건의 제목 표본0.0. 전체/동일 사건 비율은 미검증 | 키가 없어 미측정 | 키가 없어 미측정 |
| AI 요약·TTS 재배포 | 뉴스 권리는 원저작권자에게 있음. 원문을 대체하는 재배포 제한; 별도 권리 필요 | 약관은 개인/비상업 사용 제한을 명시. 기사 AI/TTS 권리 부여 확인 못함 | 무료는 비상업/학술/평가 사용 범위. 유료도 제3자 기사 권리를 부여하지 않음 |
| 현재 rights_status | LICENSE_UNVERIFIED | LICENSE_UNVERIFIED | LICENSE_UNVERIFIED |

공식 근거: [FreeNews 홈](https://www.freenewsapi.io/), [OpenAPI](https://www.freenewsapi.io/docs/openapi.json), [FreeNews 약관](https://www.freenewsapi.io/terms.php); [The News API 문서](https://www.thenewsapi.com/documentation), [무료 가격](https://www.thenewsapi.com/pricing), [약관](https://www.thenewsapi.com/tos); [GNews 문서/무료 한도](https://docs.gnews.io/), [언어·국가·검색](https://docs.gnews.io/endpoints/search-endpoint), [약관](https://gnews.io/legal/terms-of-service). 이번 재조회에서 FreeNews 약관 페이지의 갱신 표시는 2026-11-11입니다. 제공자 전체 서비스의 허용과 개별 언론사의 권리를 동일시하지 않습니다.

현재 실제 인증 검색을 확인한 뉴스 제공자는 **FreeNewsAPI 1개**이며 일부 질의는 여전히 실패합니다. 실패/null을 기사0건으로 바꾸지 않고, 성공0건도 양수 기사 수신과 구분합니다. 첫 페이지/추가 페이지/전체 건수를 분리합니다. 제목 유사도0.88의 중복률은 표본 지표입니다. FreeNews는 기본 최대3건의 details만 보강하고 본문/설명문은 보존하지 않습니다. metadata와 기사 URL을 받았어도 라이선스 미확인 뉴스의 brief는 비어 있고 요약/설명/TTS에서 차단됩니다. 이번에는 실제 목록을 재사용해2건만 details 호출했습니다.

## 행사·전시

| 소스 | 인증/요금/갱신 | 필드 및 권리 | 실제 결과와 제한 |
|---|---|---|---|
| [서울시 문화행사](https://data.seoul.go.kr/dataList/OA-15486/A/1/datasetView.do) | 무료. sample은 첫 5건; 키 필요 시 본인 발급. 데이터셋 매일 1회 | TITLE, STRTDATE, END_DATE, PLACE, LAT/LOT, CODENAME, HMPG_ADDR/ORG_LINK. RGSTDATE는 등록일이며 최종 수정일로 대체하지 않음. 데이터셋 공공누리 1유형 | sample HTTP 200 / INFO-000, 5건 정규화. 전체 count 19,765는 조회 시 원천 전체 목록 건수. 갱신시각은 null, fetched_at 별도. 실데이터 자동차 이동시간 미검증이므로 5건 모두 추천 제외 |
| [TourAPI 국문 관광정보_GW](https://www.data.go.kr/data/15101578/openapi.do) | 무료, 개발계정 표시1,000. 계정 승인량/현재 잔여는 미조회. 기본 수집 최대3시도/3페이지×50 | 공식 Swagger/첨부 국문 매뉴얼v4.4 확인. eventstartdate/enddate·createdtime/modifiedtime·좌표·cpyrhtDivCd 구분. progresstype의 선택안함 허용, 취소/행사연기 제외, 불명확 값 보류. Type1만 TTS 허용 | 23시대 인증 실제 수집200: 2페이지 raw77/정규화·날짜 유효76(진행 중36/예정40), 온라인 상태1건 보류. 76건 모두 Type3/권리 미확인. 이동시간 미검증으로 추천 제외. 초기 무인증401은 과거 이력 |

TourAPI 목록에는 행사별 원문 홈페이지가 없으므로 현재 `source_url`은 공식 데이터셋 URL입니다. 행사 ID로 안정 해시 id를 생성합니다. 행사별 공식 홈페이지 보강(detailCommon2 등)은 미구현입니다. 이미지와 전체 소개문을 사용하지 않습니다. 좌표가 없으면 null로 유지하고 미확인 위치를 만들어내지 않습니다. 행사 마지막 날짜는 KST 기준 해당 날짜가 끝나는 다음 날 00:00을 만료시각으로 사용합니다.

TourAPI 조사 추가 호출은 총6회이며 첫 수집에서 마지막 numOfRows 해석 오류로 발생한 불필요한3페이지도 포함합니다. [실제 호출·제외 사유·한계](TOURAPI_INVESTIGATION.md)를 참고하세요. 현재/향후90일과 겹치는 날짜를 검사하며 수신/미수신만으로 개최 취소를 가정하지 않습니다. 수집 시각이 원천 종료일/수정일을 대체하지 않습니다. 권리 미확인 항목의 brief도 비워 둡니다.

## 생활·긴급 교통

| 소스 | 공식 조건/스키마 | 실제 검증 |
|---|---|---|
| [서울시 실시간 도시데이터](https://data.seoul.go.kr/dataList/OA-21285/F/1/datasetView.do) | 무료, sample은 광화문·덕수궁(POI009). 공공누리 1유형. WEATHER_TIME/TEMP만 사용해 날씨 LIFE 생성; WEATHER_TIME+1시간 만료. 전체 원천 데이터는 이질적인 공공/민간 데이터이므로 다른 영역에 허가를 일괄 확대하지 않음 | HTTP 200 / INFO-000. 실제 날씨 1건 정규화, 생활/날씨 관심사 요청에서 feed와 음성 큐로 응답. 초기 Unicode URL 전달 문제의 ERROR-500은 공식 장소코드 POI009 사용 후 해결 |
| [서울시 실시간 돌발](https://data.seoul.go.kr/dataList/OA-13315/A/1/datasetView.do) | 무료, sample 5건 이내, AccInfo XML. 공공누리 1유형. 발생/종료예정, LINK_ID, GRS80TM_X/Y, ACC_INFO. 실제 XML 태그는 소문자, 시간은 HHMM/HHMMSS 혼재 | HTTP 200 / INFO-000, 원본 4건·정규화 4건. 유효기간·현재 목록에서 ACTIVE 상태를 도출하므로 해제의 완전한 보증은 아님. 수집 후 10분을 넘으면 alerts 제외. 같은 SEOUL_TOPIS 링크 체계의 경로와 일치할 때만 우선 알림 |
| [국가교통정보센터](https://www.its.go.kr/opendata/opendataList?service=event) / [인증 안내](https://www.its.go.kr/file/opendata/openapi_manual.pdf) | 인증키 필요. 공식 안내 PDF는 확인했지만 상세 페이지는 브라우징 도구/터미널에서 타임아웃·연결 실패. 현재 엔드포인트/할당량/항목 권리를 충분히 검증하지 못함 | 실제 데이터 API **미호출**, 어댑터 **미구현**. 과거 블로그의 URL을 근거로 임의 구현하지 않음. 서울시 실데이터와 SIMULATED fixture로 독립 기능 검증 |

AccInfo의 GRS80TM 좌표는 EPSG 정의를 확인하기 전 WGS84로 추측 변환하지 않습니다. latitude/longitude는 null, native_x/native_y/native_crs를 별도 보존합니다. 영향 범위는 공식 LINK_ID와 원문 통제 설명입니다. 차량 앱이 다른 링크 체계를 사용하면 매핑이 필요합니다. 좌표 근접만으로 실제 경로 영향이라고 확정하지 않습니다. 도시데이터 내 사고 영역은 경로 링크 보강 전 정규화 보류입니다. 이 결과는 실제 차량 주행 검증이 아닙니다.

## 팝업 발견과 위치/이동시간 대안

`app/popups.py`: 주최자 공식 URL, 확인 근거·확인시각, 개최 확정, 시작/종료, 장소/좌표를 검토한 수동 JSON만 받습니다. `MANUAL_OFFICIAL_CONFIRMATION`과 자동 수집 `PUBLIC_API`를 구분합니다. 기본 등록 건수는 0이며, 실제 치이카와 팝업을 발견했다고 주장하지 않습니다. 검색/피드에서 발견해도 공식 개최 확인 전에는 추천하지 않습니다. 자동 발견은 추후 공개적으로 허용된 검색·피드와 주최자 확인 단계를 갖추어 연결하며 현재 크롤러는 없습니다. [수동 입력 예제](examples/manual-events.template.json)는 의도적으로 confirmed=false입니다.

- [Nominatim 공식 사용정책](https://operations.osmfoundation.org/policies/nominatim/): 무료 소량 지오코딩 후보. 최대 1요청/초, 식별 User-Agent/Referer, 출처표시, 캐시, 일괄/정기 조회 제한, 자동완성 금지, ODbL 조건이 있습니다. 공용 API는 범용 자동 생성 지오코더로 제공할 수 없다는 최신 제한도 있어 **연동하지 않았습니다**. 명시적으로 정책을 검토한 개발자가 사용 여부를 결정해야 합니다.
- [VWorld 공식 지오코더 문서](https://www.vworld.kr/dev/v4dv_geocoderguide2_s001.do): 이 환경에서 502로 열리지 않아 무료 조건·응답을 검증하지 못했습니다. 구현하지 않았습니다.
- [카카오모빌리티 공식 가격/쿼터](https://developers.kakaomobility.com/price/): 자동차 길찾기 무료 일일 제공량 10,000 표시는 확인했습니다. 계정의 월간 정책과 활성화·차량 앱 사용 조건은 추가 확인이 필요합니다. 키·정상 호출·최신 상세 스키마 미확보로 **미연동**입니다. 유료 초과 사용/결제 설정을 활성화하지 않습니다.

프로토타입 라우팅은 인터페이스만 있으며 실데이터는 UNVERIFIED입니다. MOCK 행사에만 SIMULATED 25분을 적용하며 실데이터에 전달되지 않습니다. 행사 추천을 활성화하려면 현재 위치에서 실제 도로 이동시간을 평가하는 검증된 provider를 연결해야 합니다.

## 권리 상태의 의미

- `TTS_ALLOWED`: 이 프로젝트의 자체 작성 fixture 또는 공식 데이터셋의 가공·이용 근거와 출처표시를 확인한 해당 사실 필드. 권리 근거 URL 필수. 제3자 이미지·기사 전체로 확대하지 않음.
- `LINK_ONLY`: 링크 안내만 허용된 항목. 현재 자체 fixture에서 차단 동작을 검증하며 실제 뉴스별 이 상태를 확정한 건은 없음.
- `LICENSE_UNVERIFIED`: AI 가공/TTS 재배포 근거 미확인. 실제 뉴스 기본값. 화면 metadata에서 상태를 표시하고 음성·LLM 요약/설명에 보내지 않음.

위 분류는 확인한 공개 문서에 따른 프로젝트의 보수적 운영 판단입니다. 별도 뉴스 라이선스를 확보했다고 주장하지 않습니다. 공식 조건은 변경될 수 있으므로 공개 배포 전 다시 확인합니다.

## 2026-11-11 차량 앱 SDK 확인

새 콘텐츠 제공자/유료 서비스 호출은 추가하지 않았습니다. 로컬 MOCK Uvicorn의 health/feed/detail을 클라이언트로 검사했습니다. Pleos 공식 Maven의 TextToSpeech 3.3.1 POM/AAR을 내려받아 메서드 정의와 컴파일을 확인했습니다. 기기 서비스/음성 실행은 미검증입니다.

공식 근거: [Pleos 개발 시작](https://document.pleos.ai/en/docs/pleos-only/getting-started), [TTS SDK 설치](https://document.pleos.ai/en/docs/pleos-only/connect-sdk-pleos/TextToSpeech/importing-sdk), [모드/개요](https://document.pleos.ai/en/docs/pleos-only/connect-sdk-pleos/TextToSpeech/intro), [권한](https://document.pleos.ai/en/docs/pleos-only/connect-sdk-pleos/TextToSpeech/declaring-permissions), [초기화](https://document.pleos.ai/en/docs/pleos-only/connect-sdk-pleos/TextToSpeech/initialization-and-release), [이벤트](https://document.pleos.ai/en/docs/pleos-only/connect-sdk-pleos/TextToSpeech/event-listeners), [locale](https://document.pleos.ai/en/docs/pleos-only/connect-sdk-pleos/TextToSpeech/set-locale), [합성/중단](https://document.pleos.ai/en/docs/pleos-only/connect-sdk-pleos/TextToSpeech/start-and-stop).

Android 근거: [AGP 9.5 호환표](https://developer.android.com/build/releases/agp-9-5-0-release-notes), [네트워크 보안 설정](https://developer.android.com/privacy-and-security/security-config), [오디오 포커스](https://developer.android.com/media/optimize/audio-focus), [Android TTS](https://developer.android.com/reference/android/speech/tts/TextToSpeech).
