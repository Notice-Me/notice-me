# Notice Me

현재 위치·경로·목적지·관심사를 바탕으로 뉴스, 행사, 전시, 생활정보를 추천하는 Pleos 차량 앱 프로토타입입니다. 2인 팀의 서버/차량 앱 공동 저장소이며 2026-11-15 핵심 흐름 시연을 목표로 합니다.

## 디렉터리

- `server/`: Python 3.11+, FastAPI, SQLite, httpx, pytest 백엔드
- `vehicle-app/`: 차량 앱 담당자 작업 공간 및 연동 안내
- `docs/PROJECT_CONTEXT.md`: 전체 기획과 운영 규칙
- `docs/API_CONTRACT.md`: 차량 앱과 공유하는 v1 API 계약
- `docs/PROJECT_STATUS.md`: 실제 완료/미완료 상태와 검증 결과
- `docs/DATA_SOURCES.md`: 공식 출처, 인증, 권리, 실제 호출 결과

초기화 이후 개발은 `feat/server-content-feed` 등 기능 브랜치에서 진행합니다. main에는 기능 코드를 직접 커밋하지 않으며, 테스트 확인 후 PR을 만들고 사용자 승인 전에는 병합하지 않습니다.

실행 방법은 서버 구현 후 이 문서에 추가합니다. 데이터 모드는 `LIVE` / `MOCK` / `MIXED`로 구분하며, 이용권한이 확인되지 않은 콘텐츠는 음성 큐에서 제외합니다.
