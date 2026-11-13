# 관심사 프로필 OR·상세 검색 AND 계약 제안

2026-11-13 / **앱 담당자 공유용 설계안, 미구현**. 이번 PR은 문서와 공개 검증 메타데이터만 변경한다. 서버 endpoint/모델/OpenAPI, vehicle-app/Kotlin은 바꾸지 않는다. [측정·현재 코드와의 차이](verification/2026-11-13-profile-content.json).

## 현재 브랜치 상태와 문제

확인 당시 main94de875, 차량 [PR #8](https://github.com/Notice-Me/notice-me/pull/8)84cad04, 관심사 [PR #9](https://github.com/Notice-Me/notice-me/pull/9)7c73072는 모두 후자의 두 PR이 미병합이었다. 이번 브랜치는 최신 origin/main에서 시작했다. #9를 병합하거나 복사해 별도 기능으로 중복 구현하지 않는다. #9의 [기존 계약 검토](https://github.com/Notice-Me/notice-me/blob/7c730726f22609e66abcc281474d10878c4c45c4/docs/INTEREST_CONTRACT_REVIEW.md)를 선행 설계로 사용한다.

#9의 interests는 구체 topic이 있으면 그 제목 근거를 요구하는 상세 검색 의미다. 실제 수신한 지브리 공연 메타데이터에서 anime만 요청한 matcher는 true, 치이카와+science+anime를 합친 matcher는 false였다. 이는 서로 독립적인 프로필 관심사를 한 배열로 합치면 원하는 OR가 되지 않는다는 재현이며, #9의 상세 검색 의도를 오류라고 바꾸는 것은 아니다. 이동시간 게이트와 분리한 **matcher 관측**이다.

## 권고: 기존 GET 유지 + 명시적인 새 POST

| 방식 | 호환성·장단점 | 판단 |
|---|---|---|
| 기존 interests를 모두 OR로 재해석 | 치이카와+팝업의 AND 검색이 넓어짐 | 채택하지 않음 |
| GET /feed에 mode/filter query 추가 | 기존 호출은 유지 가능하지만 구 서버가 모르는 query를 무시하면 상세 조건이 사라진 성공200을 받을 수 있음. URL에 관심사/위치가 노출될 수도 있음 | 대안, 구 서버 감지 규약 필요 |
| POST /api/v1/feed/query 추가 | 기존 GET /api/v1/feed와 interests를 그대로 유지. 새 구조를 명시적으로 요청하며 구 서버는404. FeedResponse 재사용 가능 | **권고안**, 앱 담당자와 합의 후 별도 서버 구현 |

새 endpoint를 현재 호출하면404인 것을 실제 HTTP로 확인했다. 이 문서는 배포된 API 설명이 아니다. 구 서버404에 기존 GET으로 자동 fallback하지 않는다. 조회 방식을 바꿔 조용히 조건을 풀지 말고 업데이트 필요를 표시하는 동작을 앱과 합의한다. 기존 앱은 GET을 계속 사용하며 자동으로 OR 프로필 기능을 얻지는 않는다.

### 제안 JSON 예시

아래 위치는 기존 공개 시연 예시이며 사용자 실제 위치가 아니다. alias 정규화는 #9의 사전을 재사용할 수 있으나 profile 전체를 기존 상세 matcher에 그대로 넣으면 안 된다.

```json
{
  "context": {"lat": 37.57, "lon": 126.98, "navigation_active": false},
  "profile": {
    "categories": ["science", "anime"],
    "topics": ["치이카와"],
    "keywords": []
  }
}
```

이는 치이카와 **OR** 과학/IT **OR** 애니메이션이다. 상세 검색만 할 때는 profile을 생략하고 다음 filter를 사용한다.

```json
{
  "context": {"lat": 37.57, "lon": 126.98, "navigation_active": false},
  "filter": {"topics_any": ["Chiikawa"], "formats_any": ["팝업스토어"]}
}
```

이는 치이카와 **AND** 팝업이다. 영문·한국어·일본어 alias는 canonical chiikawa로 정규화한다. formats는 popup/character_goods/exhibition과 별칭을 해석한다. 미등록 캐릭터는 검증된 alias인 척 등록하지 않고 keywords의 정확 구문으로 요청할 수 있게 제안한다. 무민 등 새 topic 사전은 별도 검토 대상이다.

## 제안 평가 규칙

| 입력 | 일반 후보의 조건 |
|---|---|
| profile만 있음 | category 하나 OR topic 하나 OR keyword 하나와 일치 |
| filter만 있음 | 비어 있지 않은 필터 필드끼리 AND, 같은 필드의 원소끼리 OR |
| 둘 다 있음 | profileMatch AND filterMatch. 예: 과학만 선택한 profile과 치이카와 filter는0건일 수 있음 |
| 둘 다 없음/정규화 후 모두 빈 값 | 새 API에서는422. 기존 GET의 빈 관심사 동작은 바꾸지 않음 |

filter의 선택 필드는 categories_any/topics_any/formats_any/keywords_any를 제안한다. 형식 판단은 #9의 제목·명시적 EXHIBITION 근거를 재사용하며 browser popup/일반 가수 굿즈를 캐릭터 팝업으로 확대하지 않는다. 카테고리 일치가 명시한 topic을 대체하지 않는다. 새 profile/filter의 category도 제목이나 확인된 원천 분류 근거를 다시 검사하고, 과거 수집 검색어가 섞인 캐시 interest_tags를 그대로 신뢰하지 않는다. 뉴스 검색어/URL/출처명/본문에서 topic 근거를 만들지 않는다. 기존 GET의 broad-only 동작까지 변경한다는 뜻은 아니다.

새 요청은 unknown field를422로 거절하고, 잘못된 category/topic 식별자와 짧거나 무의미한 keyword도422를 제안한다. 네 배열을 포함한 선택값은 정규화 전후 총30개 이하, 각 문자열1~120자, 중복 alias는 점수 중복 가산 금지. 기존 GET의 쉼표/반복 배열/기존 오류 규약은 그대로 둔다. context의 좌표 쌍·ETA·navigation_active·경로 제한은 기존 FeedContext와 동일하게 검증하되 interests를 context에 혼합하지 않는다.

이 OR는 후보 적합성을 뜻하며 선택한 각 관심사를 TOP3에 하나씩 보장하지 않는다. 후보를 한 번 평가·중복 제거·공통 점수 정렬한 뒤 TOP3/전체 큐를 만든다. 관심사별 TOP3를 먼저 만든 후 합치면 후보가 누락되므로 그 방식을 피한다. score_reasons의 기존 숫자 dict를 재사용하고 alias 개수로 점수를 늘리지 않는다. 정확한 새 점수·검사 코드는 구현 시 검토한다.

## 음성·날씨·긴급정보·위치의 경계

권리/만료/출처와 실제 행사60분 검증은 OR/AND보다 독립적인 필수 게이트다. 일치해도 허가가 생기지 않는다. 미검증 경로와 사용자의 목적지 ETA로 행사 이동시간을 채우지 않는다. 실제 경로와 일치하는 긴급 alerts는 profile/filter에 숨겨지지 않게 유지한다.

기존 GET의 명시적 weather와 LIVE 날씨 TTS/MOCK은 유지한다. 새 POST의 profile에 weather가 있고 filter가 없으면 날씨가 OR 후보가 된다. 상세 filter를 함께 주면 일반 날씨 카드에도 filter를 적용하는 안을 제안하므로 치이카와+팝업 검색 결과에는 날씨가 없을 수 있다. 날씨·일반 추천을 계속 원하면 기존 GET을 사용한다. 새 검색이 비었다고 모의 행사나 뉴스 음성을 대신 제공하지 않는다. 이 부분은 앱 담당자가 구현 전에 확인할 선택 사항이다.

프로필 영속 저장은 이번 제안에 포함하지 않는다. 앱이 선택값을 전달하고 서버는 요청 중 평가만 한다. 사용자 식별자·현재/목적지·경로·관심사 이력을 DB/접근 로그에 저장하지 않는다. POST도 자동으로 사생활을 보장하지 않으므로 실제 배포 로그와 인증·TLS는 별도 검토한다.

## 구현 전에 공유할 확인 사항과 인수 기준

앱 담당자에게 이 PR의 링크로 공유할 수 있도록 작성했으며 **메시지 발송이나 합의 완료를 주장하지 않는다**. UI/SDK/Kotlin 코드는 이번 범위 밖이다.

| 확인할 항목 | 제안 |
|---|---|
| 경로·메서드 | POST /api/v1/feed/query, 기존 GET 유지 |
| 요청/응답 | 위 profile/filter JSON, 응답은 기존 FeedResponse. OpenAPI 추가는 합의 후 구현 PR에서 수행 |
| 구 서버 | 404 표시, 의미가 다른 GET으로 자동 대체하지 않음 |
| 선택 UI | 독립 관심사 선택과 상세 형식 필터를 분리. 사용자 과학/애니메이션 선택이 치이카와 때문에 사라지지 않음 |
| 길안내 | 주소·공식 장소·좌표·일정/변경·경로 검증은 별도. 이번 실제 추천/목적지 설정 기능 없음 |

후속 행동 테스트에는 (1) 치이카와 없는 과학 기사도 OR 프로필에 포함, (2) 치이카와 신작 소식은 popup 상세에서 제외, (3) 화장품 팝업 제외, (4) alias 중복 점수 불변, (5) 빈/잘못된 입력422, (6) 구 서버404, (7) 권리/만료/라우팅·긴급정보·날씨·MOCK 회귀를 포함해야 한다. 이는 **앞으로 구현할 인수 기준**이며 지금 통과한 새로운 기능 테스트가 아니다.
