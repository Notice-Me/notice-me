# 관심사·길안내 데이터 계약 검토 — 2026-11-13

구현 전 호환성 검토. 이번 서버 전용 P0는 기존 `interests: list[str]` 입력과 endpoint/Content/FeedResponse/OpenAPI 구조를 그대로 사용한다. `vehicle-app/`은 수정하지 않는다. main94de875와 미병합 차량 PR #8의 파서를 읽기 전용으로 대조했다. 두 앱 모두 기존 interests 반복 query를 사용하고 score_reasons의 키 집합에 의존하지 않는다.

## 이번 구현 범위

서버 내부 InterestProfile을 category(art/science/anime/weather 등), topic(치이카와와 한영일 별칭), format(캐릭터 굿즈/팝업/전시), 기타 정확 구문 keyword로 나눈다. 문자열 배열을 이 구조로 해석하므로 앱에 DTO 변경이 필요 없다. 문자열은 NFKC/casefold/공백 규칙으로 정규화한다. 제목의 ASCII 단어는 경계를 검사해 party의art/chair의ai/limited의it 같은 오탐을 막는다. 뉴스 본문·요약·원문을 내려받거나 LLM에 보내지 않는다.

구체 topic/keyword를 요청하면 제목에서 그 근거가 있어야 한다. format도 함께 있으면 같은 제목에 해당 형식이 있어야 한다(공식 분류에서 정규화한 EXHIBITION도 전시 형식 근거로 허용). topic/keyword끼리는OR, format끼리는OR, topic/keyword와format 사이는AND다. format만 요청하고 category도 있으면 제목의 category 일치도 요구한다. 구체 취향에서는 과거 수집 검색어가 섞인 interest_tags 대신 제목에서 category 근거도 다시 확인한다. 이는 무관한 일반 팝업/애니메이션 전체가 특정 취향을 대체하지 않도록 선택한 보수적 기본값이다. 복수 관심사 그룹을 OR로 구성하는 구조화된 사용자 프로필은 향후 별도 제안 대상이다.

기존 category-only NEWS의 위치 fallback, LIFE의 관심사 필요, 행사 발견·점수 방식과 MOCK 기본 흐름은 유지한다. 구체 취향을 요청한 경우에는 근접성만으로 구체 키워드 불일치를 우회하지 못한다. 명시적 weather/생활 관심사가 있는 실제 날씨와 경로 기반 긴급정보는 구체 취향의 제약과 분리해 기존 기능을 유지한다. 행사 실제 이동시간·권리·만료 정책은 별도 선행 조건이다.

추천 근거는 기존 `score_reasons: dict[str,number]` 안의 interest_match, interest_topic, interest_keyword, interest_format, 위치, freshness, source_verified, validity 점수로 제공한다. 합계가 score다. source_verified는 원천 레코드 검증 상태 점수이며 기사 사실성 보증이 아니다. 요청 위치·목적지·관심사 이력은 저장하지 않는다. 키워드를 source URL/언론사명/요약에서 발견했다는 이유로 강한 매칭을 주지 않는다.

알 수 없는 관심사도2~120자의 문자/숫자 구문이면 제목과 문자 그대로 비교한다. 정규식 실행·본문 검색·사실 생성은 하지 않는다. 너무 짧거나 무의미한 값은 UNSUPPORTED_INTEREST 개수로 진단하고 전체 일반 콘텐츠로 풀어 주지 않는다. SPECIFIC_INTEREST_MISMATCH도 기존 diagnostics 배열 안의 코드 추가이며 새 JSON 필드는 아니다. 빈 결과와 LIVE 날씨만 남는 결과 모두 정상일 수 있다.

앱 요청 예: `GET /api/v1/feed?lat=37.57&lon=126.98&interests=Chiikawa&interests=popup&interests=weather`. 위치값은 예시이며 요청 이력을 저장하지 않는다. 관심사 입력은 URL 인코딩한다. top3/queue/alerts/playback_order와 상세/설명 URL은 그대로다. 반환 brief를 임의로 일반 TTS에 보내지 말고 기존 tts_eligible/queue/권리·만료 판단을 따른다. 기존 v1 OpenAPI와의 완전 일치 테스트가 통과했다. [실제 HTTP·검증 경계](verification/2026-11-13-server-interest.json).

## 다음 단계 제안: 길안내 대상 DTO (이번 미구현)

| 앱 필요 정보 | 현재 v1 필드 | 사용 조건/한계 |
|---|---|---|
| 콘텐츠ID / 행사명 | id / title | 식별자를 그대로 사용 |
| 장소명 | venue | 공백/불명확 장소면 대상 아님 |
| 위도·경도 | latitude / longitude | nullable, 알려진 WGS84 좌표 쌍만. 주소명으로 추측하지 않음 |
| 주소 | 현재 별도 필드 없음 | venue를 주소로 바꾸지 않음. nullable address 제안은 후속 검토 필요 |
| 원문/공식 링크 | source_url | dataset URL과 주최사/행사 공식 URL은 구별해야 함 |
| 검증 상태 | verification_status / organizer_confirmed_at | VERIFIED 수집과 길안내 장소 검증은 다름 |
| 행사 유효기간 | starts_at / expires_at | 취소·변경·만료를 포함해 재확인 |

향후 `navigation_target` 제안은 `{eligible:false, reason_codes:[...], place_name:null, latitude:null, longitude:null, address:null, official_url:null, verified_at:null}`을 기본으로 한다. 공식 장소/좌표/주소 근거·유효기간·상태가 확인된 경우에만 eligible=true를 제안한다. tts_eligible나 목적지 ETA로 길안내 자격을 추론하지 않는다. 이 필드 추가 전 앱 호환성 검토와 공동 계약 갱신이 필요하다. 실제 Pleos 목적지 설정·음성 명령은 앱 담당이며 이번 서버는 SDK 코드를 만들지 않는다.
