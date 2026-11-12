# Server

FastAPI + SQLite 콘텐츠 서버. [루트 README](../README.md)에 설치/실행/실데이터 수집 명령이 있습니다. 아래 명령은 모두 `server/`에서 실행합니다.

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --port 8000 --no-access-log
.venv\Scripts\python.exe -m app.cli ingest
.venv\Scripts\python.exe -m pytest -q
```

환경변수 우선순위: 프로세스 환경 > `.env` > 기본값. `.env.example`은 빈 키를 포함한 템플릿입니다. `NOTICE_DATA_MODE=mock|live|mixed`, 기본 mock. API는 SQLite 조회만 수행하며 수집은 명시적 CLI로 실행합니다. Mock/Mixed 시작 시 자체 작성 fixture를 갱신합니다. Live 시작 시 fixture를 만들지 않으며 DB의 MOCK 레코드를 노출하지 않습니다.

`app/providers`는 공식 스키마 기반 수집기, `recommendation.py`는 규칙/근거, `rights.py`는 음성·설명 권리 검사, `llm.py`는 학교 API 연결 전 인터페이스와 deterministic mock, `routing.py`는 실데이터 이동시간 미검증 및 fixture 전용 모의 라우팅입니다. 수동 팝업은 `popups.py`의 엄격한 입력 형식으로 로컬 파일을 지정합니다. 크롤러는 없습니다.

두 Uvicorn 서버를 live 8765, mixed 8766 포트에 띄운 후 `.venv\Scripts\python.exe scripts/smoke_http.py`로 실제 HTTP 통합 검증을 재현할 수 있습니다. 먼저 수집하고, mock 교통 fixture가 만료됐다면 mixed 서버를 재시작하세요. 고정시각 pytest와 외부 통신 없는 httpx.MockTransport 테스트는 실데이터 검증과 구분됩니다.

차량 담당자용 단일 서버 검사: `.venv\Scripts\python.exe scripts/check_vehicle_api.py --base-url http://127.0.0.1:8000 --expect-mode MOCK --demo-route`. 이 도구는 DB/키 없이 HTTP만 사용하고 결과를 reports에 저장합니다. 기존 smoke_http.py는 docs의 응답 예시를 갱신하므로 역사적 예시를 보존하려면 단일 서버 검사를 쓰세요. OpenAPI만 갱신하려면 `.venv\Scripts\python.exe scripts/export_openapi.py`를 사용합니다.

Pleos 첫 연결은 [차량 연동 안내](../docs/VEHICLE_INTEGRATION.md)와 [앱 담당 확인표](../docs/VEHICLE_ACCEPTANCE.md)를 사용합니다. 다른 기기에서 연결하려면 Uvicorn에 --host 0.0.0.0을 지정하고 기기에서 도달 가능한 주소를 사용하세요. 날씨만 시연 직전 갱신: `.venv\Scripts\python.exe -m app.cli ingest --public-provider seoul_city --report reports/vehicle-weather-ingest.json`. 다른 공공 제공자/뉴스를 호출하지 않습니다. 옵션 생략 시 기존 전체 수집을 유지합니다. 검사 성공은 SERVER_HTTP_ONLY이며 실제 앱·TTS 출력은 별도 확인합니다.

뉴스만 검사/수집하려면 `app.cli validate-news` / `ingest-news`를 사용합니다. `--keyword` 반복, 검증용 `--window-hours 24|168`, `--max-requests`로 범위를 줄일 수 있습니다. 뉴스의 read/최대 재시도/실행별 예산 기본값은20초/1회/20시도입니다. `NOTICE_NEWS_*`로 설정하고 기존 `.env`를 다시 복사하지 마세요. 검색별 허용 metadata는 news_searches 테이블에 append하며 validate-news만으로 원문 URL 없는 목록을 feed 콘텐츠로 만들지는 않습니다. [정책·실측](../docs/FREENEWS_INVESTIGATION.md).

TourAPI만 수집: `.venv\Scripts\python.exe -m app.cli ingest --public-provider tourapi --report reports/tourapi-next.json`. 기본 KST 오늘~90일/수정일순/페이지50/최대3페이지·3시도, 재시도0회입니다. NOTICE_TOUR_PAGE_SIZE/MAX_PAGES/REQUEST_BUDGET/LOOKAHEAD_DAYS로 조정하며 뉴스 예산과 별개입니다. 매 페이지의 성공/제외를 DB에 남기고 불완전하면 PARTIAL을 표시합니다. Type3/미확인은 TTS 차단, LIVE 이동시간 미검증이면 추천 제외를 유지합니다. [실제76건 수집·제외 원인·한계](../docs/TOURAPI_INVESTIGATION.md).
