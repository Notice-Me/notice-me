# API contract v1

버전 0.1.0 / 2026-11-11. Base URL `/api/v1`. UTF-8 JSON, timezone-aware ISO 8601 timestamps. 서버 정규화 자료는 UTC, 원천 날짜 해석은 KST입니다. [OpenAPI JSON](openapi.json)은 실행 중인 FastAPI에서 추출한 명세입니다. [LIVE](examples/live-feed.json) / [MIXED](examples/mixed-feed.json) 예시는 실제 HTTP 응답의 고정 스냅샷으로 현재 정보가 아닙니다.

[차량 앱 실행/연결 안내](VEHICLE_INTEGRATION.md)와 [요청 예제](examples/vehicle-api.http)를 함께 사용하세요. OpenAPI는 `.venv\Scripts\python.exe scripts/export_openapi.py`로 외부 통신 없이 재생성하며, 테스트에서 기록된 명세와 런타임 명세의 일치를 검사합니다.

## Endpoints

- `GET /health`: service/database health and provider configuration status (no credentials).
- `GET /feed?lat=37.57&lon=126.98&interests=예술&navigation_active=false`
  - required: lat [-90,90], lon [-180,180]
  - interests: repeatable query string, also accepts comma-separated values
  - navigation_active: bool, default false
  - destination_lat/destination_lon: optional pair, valid only as a complete pair
  - eta_minutes: optional nonnegative float, applied only with navigation_active
  - route_points / route_link_ids: optional future-compatible inputs, implementation format recorded below
- `GET /contents/{id}`: stored content, 404 if unknown; expired detail remains readable and marked.
- `POST /contents/{id}/explain`: optional JSON `{ "question": "자세히 알려줘" }`; grounded explanation only for rights-cleared, valid, verified content. Mock/LIVE AI mode is explicit. Unknown id 404, rights blocked 403, stale/unverified content 409.

## Feed response

```json
{"top3":[],"queue":[],"alerts":[],"generated_at":"2026-11-11T00:00:00Z","data_mode":"MOCK"}
```

`top3` maximum 3, score descending. `queue` is separately generated, unlimited item count before ETA budget, only TTS_ALLOWED. Alerts precede queue during playback. Display cards must not be independently sent to TTS. `data_mode`: LIVE (only live contributions), MOCK (only fixtures/simulation), MIXED (both); empty feed uses collection provenance and diagnostics, never silently relabels Mock as LIVE.

Common fields: id, content_type (NEWS/EVENT/EXHIBITION/LIFE/TRAFFIC), title, brief, source_name, source_url, published_at, updated_at, expires_at, latitude, longitude, interest_tags, rights_status (TTS_ALLOWED/LINK_ONLY/LICENSE_UNVERIFIED), verification_status (VERIFIED/UNVERIFIED/SIMULATED), priority.

Extensions carry per-item data_mode, score and score_reasons, provenance, rights evidence, driving-time verification, traffic impact and freshness. Nullable source update timestamps mean unknown, not fetch time. Source fetch time is separate. Unknown event travel time means excluded; diagnostics explain it.

## 구현된 요청 형식

| Query | 타입/기본값 | 검증 |
|---|---|---|
| lat, lon | 필수 float | [-90,90], [-180,180] |
| interests | 반복 문자열 / 빈 목록 | 쉼표 구분도 허용, 최대 30개 |
| navigation_active | bool / false | false이면 현재 위치만 사용 |
| destination_lat, destination_lon | 선택 float | 반드시 쌍으로 제공, 내비 사용 시만 허용 |
| eta_minutes | 선택 float [0,1440] | 내비 사용 시만 허용; 목적지 좌표 없이도 전달 가능 |
| route_points | 반복 `위도,경도` 문자열 | 최대 500개. `route_points=37.57,126.98`. 내비 사용 시만 허용 |
| route_link_ids | 반복 문자열 | 최대 1,000개, 내비 사용 시만 허용 |
| route_link_namespace | 문자열 / UNSPECIFIED | 실제 경로는 SEOUL_TOPIS 매핑 확인 후 사용. Mock은 DEMO |

관심사 별칭: art→예술, science/과학/IT→과학IT, anime/animation→애니메이션, weather→생활. 임의 관심사도 정확히 일치하는 태그와 비교합니다. 다른 지도 제공자의 링크 ID는 숫자가 같아도 같은 도로라고 가정하지 않습니다.

## 응답 확장과 차량 앱의 처리

- `top3`: 일반 콘텐츠 상위 최대 3건. 타입별 할당 없음. 화면 카드의 권리 상태를 확인하세요.
- `queue`: 별도로 생성한 전체 음성 큐. TTS_ALLOWED + 근거 URL + VERIFIED/SIMULATED + 유효기간을 통과한 항목만 포함.
- `alerts`: 유효한 TRAFFIC 중 수집 후 10분 이내이고 **같은 namespace의 경로 link ID가 일치**한 항목. top3/일반 queue와 분리.
- `playback_order`: 음성 자격이 있는 alerts ID를 앞에 놓고 queue ID를 이어 붙인 배열. alerts에서도 tts_eligible을 확인해야 합니다.
- `data_mode`: 실제 반환 항목이 모두 LIVE면 LIVE, 모두 MOCK이면 MOCK, 섞이면 MIXED. 빈 응답은 입력 저장자료/설정 모드를 따르며 NO_ELIGIBLE_CONTENT 진단 포함. 데이터 없음은 수집 성공을 의미하지 않습니다.
- `diagnostics`: code/count/message. DRIVING_TIME_UNVERIFIED, EXPIRED_OR_FUTURE, LIFE_INTEREST_REQUIRED, TTS_RIGHTS_BLOCKED, TRAFFIC_STALE, TRAFFIC_ROUTE_UNVERIFIED, SIMULATED_CONTENT, ETA_BUDGET_EXCEEDED, SOURCE_UNAVAILABLE 등.
- `routing_status`: 현재 UNVERIFIED_FOR_LIVE_EVENTS. Mock의 25분은 SIMULATED이며 LIVE 행사에 적용되지 않습니다.

ETA 적용: 음성 길이 **추정값** 합계를 `max(0, ETA×60−30초)` 안으로 제한하고 alerts 분량을 먼저 차감합니다. 실제 TTS 길이, 청취 이력, 재생 위치는 서버가 모릅니다. 화면 top3는 음성 예산과 독립입니다. 차량 앱이 새 요청으로 대기 큐를 재평가하고 재생 중 항목/오디오 포커스를 제어합니다. 장소 접근만으로 자동 재생하지 않습니다.

## 추가 콘텐츠 필드

| 필드 | 타입/의미 |
|---|---|
| fetched_at | 필수 ISO 수집시각. published_at/updated_at의 대체값 아님 |
| rights_evidence_url | 선택 URL, TTS_ALLOWED에는 필수 |
| data_mode | 항목별 LIVE 또는 MOCK. SIMULATED는 반드시 MOCK |
| provenance | PUBLIC_API / MANUAL_OFFICIAL_CONFIRMATION / SELF_AUTHORED_FIXTURE 등 |
| starts_at, venue, organizer_confirmed_at | 선택 행사 시작/장소/수동 공식 확인시각 |
| score, score_reasons | feed 점수와 구성 dictionary |
| tts_eligible | 음성 자격 bool. detail에서는 만료 여부도 반영 |
| estimated_speech_seconds | 음성 길이 추정 초, 실제 합성 duration 아님 |
| driving_time | 행사 이동시간 평가: status, minutes, provider, checked_at. LIVE는 VERIFIED 필요 |
| traffic | occurred_at, valid_until, status, affected_link_ids, link_namespace, radius_meters, extent_description, match_status, native_x/y/crs |

권리 미확인 실제 뉴스는 brief가 빈 문자열입니다. 교통·TourAPI source_url은 개별 원문 대신 공식 데이터셋 URL일 수 있습니다. 좌표 없음/좌표 체계 미확인은 latitude/longitude=null입니다. native 좌표가 있다고 WGS84 좌표가 있는 것은 아닙니다.

교통 ACTIVE 상태는 현행 API 목록과 종료예정에서 도출합니다. 해제 지연 가능성을 남기고 오래된 수집은 재생하지 않습니다. 좌표 근접은 PROXIMITY_ONLY 후보일 뿐 실제 경로 영향 확정 근거가 아니므로 긴급 alerts에서 제외합니다. 실제 경로와 namespace 매핑은 차량 담당자와 추가 검증이 필요합니다.

## health / detail / explain 세부 동작

health: status, database, configured_data_mode, stored_counts, providers, collections. 설정 모드와 feed의 반환 항목 모드는 다를 수 있습니다. status=ok는 서버/DB 상태이며 외부 API 정상 여부는 각 collections의 status/code/collected_at을 확인합니다. 인증키는 반환하지 않습니다.

detail: 공통 필드 + is_expired + tts_eligible. 만료 상세는 읽을 수 있지만 음성 불가. 모드에서 숨긴 id도 404입니다.

detail/explain도 feed와 같은 콘텐츠 유효성 검사를 적용합니다. 10분 초과 교통 수집, 해제 상태, 통제 유효기간 종료, 미래 발생/발행, 통제 필드 누락은 상세 tts_eligible=false이며 설명은 409로 거절합니다. 권리 미확인 항목의 403은 유지합니다. 상세의 자격 표시는 경로·관심사·행사 이동시간 검증을 대신하지 않으므로 재생 대상은 최신 feed의 queue/alerts에서 선택하세요.

explain: 선택 body `{"question":"자세히 알려줘"}`, 질문 최대 500자. 반환 content_id, answer, ai_mode, provider, source_urls, grounding. 현재 항상 ai_mode=MOCK, provider=deterministic. 저장된 제목·brief·장소·일정을 재배열하며 임의 질문에 추가 사실을 만들지 않습니다. 학교 AI endpoint는 미설정입니다. 오류: 404 unknown, 403 RIGHTS_NOT_CLEARED(음성/가공 자격 미충족), 409 만료, 422 입력 오류. 미검증 콘텐츠는 권리 자격 검사에서도 차단될 수 있습니다.

## 추천 규칙

1. 만료/미래 발행/UNVERIFIED 제외. 뉴스 URL 추적 파라미터와 같은 24시간대 제목 유사도(0.88)로 중복 제거. 같은 데이터셋 URL을 공유하는 서로 다른 교통·행사 ID는 보존합니다.
2. NEWS: 관심사 일치 또는 현재/목적지/경로 표본 20km 안의 지역 관련성. 관심사 뉴스에는 위치 제한 없음. LIFE: 관심사 일치 필수.
3. EVENT/EXHIBITION: 검증된 자동차 이동시간 <=60분. LIVE 미검증은 제외. 도착 전에 끝나면 제외. 향후 일정도 발견 가능하지만 세부 영업시간 검증은 아직 없음.
4. 점수: 관심사 태그당20(최대40), 현재/목적지/경로 표본 거리 점수 최대25(20km에서0), 7일 최신성 최대20, 원천 VERIFIED 10, 유효성5. 사고 링크 일치 별도100점과 priority 우선. 거리 점수는 이동시간이 아닙니다.

## Change log

- 2026-11-11: initial contract and directory/bootstrap documentation. No functional backend in bootstrap commit.
- 2026-11-11 feature 0.1.0: 기본 계약 유지. route_points/route_link_ids/**route_link_namespace**, fetched_at/권리 근거/항목 모드, 점수 근거, driving_time, traffic, diagnostics, playback_order, 상세 만료 표시, Mock 설명 응답 추가. 실제 수집은 CLI이며 공개 수집 endpoint는 없습니다.
- 2026-11-11 재검증: feed/detail/explain의 콘텐츠 유효성 검사 일치. 기존 URL·필드·권리 오류 유지. 기존 49개와 신규 유효성 회귀 테스트 10개 통과.
- 2026-11-11 연동 보강: health=HealthResponse, detail=ContentDetail 응답 모델을 명시하고 top3의 maxItems=3을 OpenAPI에 표현. 네 endpoint의 기존 JSON 필드와 요청 형식 유지. 앱에서 null 허용 필드와 403/404/409/422를 처리하도록 연동 안내 추가.
- 2026-11-11 FreeNews 조사: 내부 수집의 timeout/재시도/예산/검색별 저장을 보강. 차량 API 요청/응답·권리 정책 변경 없음. 저장된 OpenAPI 일치 테스트 통과. 새 CLI의 JSON 관측 필드는 차량 API 필드와 별개.
- 2026-11-11 Pleos 인계: API/OpenAPI 변경 없음. HTTP 검사 도구의 전체 재생 순서·alerts 권리/유효성·LIVE 뉴스403 검증 및 서버 HTTP 한정 표시를 보강. 선택 공공 수집 CLI와 앱 담당 확인표 추가. SDK/TTS 실행은 미검증.
