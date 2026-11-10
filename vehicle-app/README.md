# Vehicle app handoff

차량 앱 담당자 작업 공간입니다. 서버 코드와 독립된 기능 브랜치를 사용하세요.

공유 계약: [`../docs/API_CONTRACT.md`](../docs/API_CONTRACT.md).

서버 응답의 `top3`는 화면 카드, `queue`는 권리 검증을 통과한 전체 음성 큐, `alerts`는 우선 처리 대상입니다. MOCK/MIXED 배지와 항목별 SIMULATED 표시를 유지하세요. `queue`에 없는 화면 카드를 임의로 TTS에 보내지 마세요.

차량 SDK 권한, GPS, 내비 경로/ETA 읽기, CarUxRestrictions, 오디오 포커스, 미디어 다음/다시, TTS 실행은 차량 앱 담당 범위입니다. SDK 지원 여부를 확인하기 전에는 연동 완료로 표시하지 않습니다.
