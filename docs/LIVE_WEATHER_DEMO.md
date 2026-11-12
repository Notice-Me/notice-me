# 실제 날씨 시연과 갱신 정책 — 2026-11-13

## 범위와 지역

이번 MVP의 LIVE 음성은 서울시 `seoul_city`의 날씨만 허용한다. 뉴스·행사·교통·다른 생활정보는 권리가 있어도 이번 LIVE 음성 범위에 넣지 않는다. MOCK 재생·모의 긴급정보·TOP3와 전체 큐 분리는 유지한다. 행사 추천에는 기존 검증된 자동차 이동시간 60분 이내 조건이 남는다. 목적지 ETA로 이 조건을 대신하지 않는다.

[서울시 공식 데이터셋](https://data.seoul.go.kr/dataList/OA-21285/F/1/datasetView.do)은 공공누리 1유형 출처표시(상업 이용·변경 가능), 제3저작권자 없음으로 표시한다. sample 키는 광화문·덕수궁에 한정되며 한 번에 한 장소를 조회한다. 현재 구현은 인증키 여부와 무관하게 POI009만 요청한다. 차량 현재 위치·목적지 날씨라고 바꾸어 안내하지 않는다. 원천 AREA_NM과 WEATHER_TIME을 그대로 근거로 사용한다. 고정 관측 지역을 다른 지역으로 일반화하지 않는다.

## API 호환성과 음성 조건

Content에 nullable `weather`를 추가했다. `area_code=POI009`, `region`, `observed_at`(offset 포함), `scope=FIXED_OBSERVATION_AREA`다. 기존 `updated_at`·`expires_at`·`brief`는 유지한다. 필드가 없는 옛 DB 자료는 파싱되지만 재수집 전 LIVE 음성으로 허용되지 않는다. 옛 앱은 추가 필드를 무시할 수 있으나 고정 지역·시각·앱 쪽 방어 표시를 위해 차량 후속 PR이 필요하다.

권리 허가(`tts_allowed`)와 이번 음성 범위(`voice_allowed`)를 분리했다. queue, playback_order, detail.tts_eligible에 같은 음성 정책을 적용한다. 관측이 미래이거나 1시간 이상 지났거나 수집시각이 미래면 feed와 detail 모두 차단한다. expires_at은 관측시각+1시간이며 재수집 시각으로 연장하지 않는다. explain의 기존 권리/유효성 검사와 deterministic MOCK은 유지한다.

진단: `FIXED_WEATHER_AREA`는 고정 관측 지역, `LIVE_TTS_WEATHER_ONLY`는 허가권과 별개인 MVP 음성 범위 제외, `WEATHER_STALE_OR_FUTURE`는 관측 신선도 문제다. 권리 미확인은 기존 `TTS_RIGHTS_BLOCKED`, 행사 경로 미확인은 `DRIVING_TIME_UNVERIFIED`로 남긴다.

## 갱신과 실행

11/15 시연은 수동 갱신을 우선한다. 앱의 약 15초 feed 조회는 SQLite 조회일 뿐 외부 API 수집을 일으키지 않는다. 별도 자동 scheduler는 이번에 넣지 않는다. 공식 페이지의 실시간 표기는 확인했지만 WEATHER_TIME의 정확한 갱신 간격을 확정한 것은 아니다. 1시간 TTL은 이 프로젝트의 보수적 허용 한계이며 공식 관측 보장 주기가 아니다.

시연 직전 `python -m app.cli ingest --public-provider seoul_city --report <새 파일>`로 날씨 한 제공자만 갱신하고, 관측시각·만료·LIVE queue/detail을 확인한다. 이번 날씨 수집기는 호출 1회·자동 재시도 0회다. 실패나 오래된 관측이면 새 문장을 만들지 말고 최신 데이터 없음으로 처리한다. 수동 갱신은 장시간/재부팅 뒤 자동 시연을 보장하지 않는다. 자동화 시에는 별도 worker에서 최소 15분 간격(선택한 제안값, 공식 갱신주기 아님), 실패 재시도 상한·공유 quota·중복 실행 잠금을 설계할 P1이다.

기존 `.env`·DB를 덮어쓰지 않으려면 설정을 읽고 DB는 별도 backup 사본으로 지정한다. 원본을 지우거나 `.env`를 복제할 필요는 없다. 서버는 같은 PC AVD에서 `http://10.0.2.2:8000`으로 연결한다. 서버 API 키를 앱에 넣지 않는다. 위치·목적지·질문 이력을 저장하지 않는다.

## 이번 실제 관측

2026-11-13 00:08 KST 원본 DB의 읽기 전용 backup 사본에서 seoul_city만 실제 1회 호출했다. HTTP200/SUCCESS, 날씨1건, 원천 관측 00:00 KST, 광화문·덕수궁 11.5도, 만료01:00 KST였다. 원본 DB와 `.env`는 수정하지 않았다. 뉴스/Tour/다른 콘텐츠 API 호출은 0회다.

00:10 KST 실제 로컬 Uvicorn: LIVE top3/queue/alerts=3/1/0, 뉴스2건 detail 음성 false·explain403. MOCK+명시적 모의 route=3/5/1 유지. 이 숫자는 해당 시각과 입력의 관측이며 영구 보장이 아니다. HTTP 검사와 Pleos SDK·청취 검증은 별개다. 차량 결과는 후속 인수 기록으로 구분한다.

서버 단위 테스트의 LIVE weather 표본은 합성 데이터다. 실제 외부 호출 증거와 합산하지 않는다. 처음 회귀 실행은4실패/155통과: 날씨 한국어 관심사 alias와 기존 LIVE 뉴스 음성 가정을 점검했다. alias를 보강하고 일반 MOCK 큐 테스트는 명시적 MOCK으로, LIVE 검사 표본은 weather로 바꾸었다. 실패를 감추기 위해 LIVE 차단 정책을 약화하지 않았다.

## P1 조사 경계

현재 좌표별 날씨 제공자는 미연결이다. 기상청 단기예보의 초단기실황을 후보로 [공식 목록](https://www.data.go.kr/data/15084084/openapi.do)에서 이용 승인·격자 좌표·발표 시각·권리·무료 quota를 확인한 뒤 별도 PR로 다뤄야 한다. 이번에는 호출하거나 통합하지 않았다.

행사 이동시간은 [Kakao Mobility 시작 가이드](https://developers.kakaomobility.com/guide/navi-api/start.html)와 [가격·무료 quota](https://developers.kakaomobility.com/price/)를11/13 확인했다. 자동차 길찾기는 공식 문서상 일10,000건 무료 제공량, 출발/도착1개와 REST API 키·서비스 정보 등록이 필요하다. 초과 유료 정책도 있으므로 계정 무료 자격·초과 차단·캐시/재배포 조건을 확인하고 서버 실행 단위의 작은 예산으로 별도P1 PR을 제안한다. 계정 생성·유료 설정·API 호출은 하지 않았다. 예전 `/docs/navi-api/directions/` 문서는404여서 현재 가이드 주소를 사용했다. 기상청은 공식 목록의 전국5km 격자·초단기실황 제공을 확인했으나 키 발급·격자 변환·신선도/권리 검증·호출은 아직 하지 않았다. 학교 AI endpoint는 여전히 미제공이다.

최종 서버 검사: pytest159통과, Ruff check/format37파일 통과, pip check 정상. Starlette/httpx 기존 deprecation 경고1개. 새 테스트12개는 날씨 권리/만료/미래/구형자료, LIVE 범위, ETA/행사 이동시간 구분과 목적지 우선 점수를 검사한다.
