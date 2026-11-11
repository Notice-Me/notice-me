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
