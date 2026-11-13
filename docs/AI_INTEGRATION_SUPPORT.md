# 멀티 AI 연동의 공식 지원·로컬 준비 상태

확인일2026-11-14 KST. 공식 지원 확인과 이 계정의 접근 성공을 구별한다. 이번 외부 모델 추론 호출·웹 채팅 입력·유료 사용·계정 연결·SDK 설치는 **0회**다. 웹 공식 문서 열람과 git fetch는 모델 API 호출이 아니다. [실행 도구](AI_DEVELOPMENT_WORKFLOW.md), [Gemini 제안 재검토](GEMINI_REVIEW_REASSESSMENT.md), [검증 증거](verification/2026-11-14-ai-workflow.json).

여기서0회는 **이번 도구가 추가로 연결·실행한 외부 리뷰/하위 agent**의 집계다. 현재 Codex 대화의 작업은 앱 사용량을 소모할 수 있으며 그 잔여량/비용은 이 도구로 측정하지 않았다. 전체 개발 작업이 무료이거나 사용량0이라는 뜻은 아니다.

## A. 공식 API·SDK

| 담당 | 공식 수단·확인한 지원 | 계정·요금·이번 준비 상태 |
|---|---|---|
| Codex 오케스트레이터 | [공식 harness 안내](https://developers.openai.com/blog/codex-as-a-platform): codex exec, SDK, app-server. [SDK](https://learn.chatgpt.com/docs/codex-sdk)는 스레드 시작/재개와 읽기 전용 권한 등을 제공 | 설치 CLI0.167.0-alpha.4.1, login status는 ChatGPT 로그인. 모델별 권한·잔여 구독량·API 잔액 미조회. 이번 하위 Codex 추론 실행 없음 |
| Gemini 기술 리뷰 | [Gemini API 모델 명세](https://aistudio.google.com/docs/models/gemini-4-argon)에서 요청한 **Gemini 4 Argon / gemini-4-argon** 확인. Carbon으로 임의 대체하지 않음. 공식 Google Gen AI SDK/문서 경로 사용 가능 | 프로세스 환경과 기존 서버.env에서 키 설정을 찾지 못함. 검사한 서버 venv에 google.genai 없음. 실제 계정 권한·프로젝트 할당량 미검증 |
| Claude 위험·실패 리뷰 | [Client/Agent SDK 구분](https://code.claude.com/docs/en/agent-sdk/overview), [공식 CLI headless](https://code.claude.com/docs/en/headless)의 claude -p·구조화 출력·세션 기능 확인 | claude 명령은 PATH에서 미발견, 검사 venv에 anthropic 없음. 실제 모델은 미선정이며 식별자를 추측하지 않음. 앱/API 계정·크레딧 미확인 |
| GPT 종합 판단 | [Responses API 대화 상태](https://developers.openai.com/api/docs/guides/conversation-state)로 별도 API 대화 관리 가능. SDK/Conversations/previous_response_id는 API 문맥을 위한 기능 | 검사한 환경에 OPENAI_API_KEY와 openai SDK 없음. Codex의 ChatGPT 로그인만으로 일반 API 결제·권한·잔액을 보증하지 않음. GPT 모델 ID는 미선정 |
| 학교 BAZE | 학교의 공식 endpoint/인증/사용 모델/할당량/요금·반출 정책 문서가 아직 없음 | 환경/서버 설정에서 관련 키 설정 미발견. 학교 웹 토큰·채팅 크레딧을 Gemini/Claude/OpenAI API 크레딧으로 간주하지 않음. 임의 OpenAI 호환 URL 미구현 |

SDK 없음은 **검사한 서버 venv 범위**의 관측이며 PC 전체에 없다는 뜻은 아니다. 기존 서버 의존성에 AI SDK를 추가하지 않았다. 키값·로그인 토큰·쿠키·계정 이메일은 읽어 출력하거나 수집하지 않는다.

`gemini-4-argon`은 확인한 Developer API 식별자다. Antigravity CLI의 --model slug가 반드시 같다고 가정하지 않으며, 후속 연결 시 해당 제품의 공식 모델 목록/계정 선택값을 확인해야 한다.

### 비용과 구독 구분

- [Gemini 공식 가격](https://aistudio.google.com/docs/pricing#gemini-4-argon): Argon은 Free tier에 없음. Standard의100만 토큰당 입력$2/출력$10(생각 토큰 포함)은11/30까지,12/1부터$4/$20으로 표시됨. 도구·검색 비용이 별도일 수 있다. 이는 계정별 견적/잔액을 확인한 값이 아니며 실제 호출 전에 다시 확인한다. 이번 저장소 무료 정책과 사전 승인 조건상 유료 adapter를 활성화하지 않는다.
- [Antigravity 요금제](https://antigravity.google/docs/plans)는 앱의 기본 할당량과 초과 AI 크레딧 설정을 별도로 설명한다. 모델/작업 난도에 따라 소모가 달라 단순 프롬프트 수를 잔여량으로 환산하지 않는다. 앱 기본량을 다 쓰면 AI Credit Overages의 Always가 추가 크레딧을 쓸 수 있으므로 실제 설정을 확인해야 한다. 변경하지 않았다.
- [Claude 앱/API 분리](https://support.claude.com/en/articles/9876003-why-is-claude-api-usage-billed-separately-from-my-paid-claude-plan): Console 설정은 별도다. 다만 [Max·Ultra·Team의 API 크레딧 혜택](https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-ultra-and-team-plans)이 있어 “구독에는 API 혜택이 전혀 없다”라고 단정하지 않는다. 자격·조직 연결·잔액 확인이 필요하며 이번에 신청하지 않았다. 모델별 요금은 [공식 가격](https://platform.claude.com/docs/en/about-claude/pricing)에서 선정 후 확인한다.
- [ChatGPT Work/Codex 가격](https://learn.chatgpt.com/docs/pricing)과 [ChatGPT 구독자 API 크레딧](https://developers.openai.com/api/docs/guides/chatgpt-api-credits)은 서로 다른 사용량을 설명한다. 일부 Pro/Business 구독은 조건부 조직 연결 후 API 크레딧 혜택이 있다. 이를 수령했거나 사용자가 해당 요금제라는 확인은 없다. 앱 로그인과 API 대화/프로젝트 잔액은 별도다. 실제 모델 요금은 [API 가격](https://developers.openai.com/api/docs/pricing)에서 확인한다.
- 공급자 오류·타임아웃은 무료라는 보장이 없다. [Claude 과금 안내](https://support.claude.com/en/articles/8977456-how-do-i-pay-for-my-claude-api-usage)는 응답 도중 연결이 끊겨도 요금이 발생할 수 있음을 설명한다. 사용량을 모르면 unknown으로 두고 재시도하지 않는 것이 현재 기본안이다.

이번에 실제 남은 토큰·일일/주간 할당량·잔액을 확인한 공급자는 없다. 결제 계정/자동 충전도 미조회이며 미설정이라고 가정하지 않는다. 프로세스에 키가 안 보이는 것은 계정 부재의 증거가 아니다.

## B. Antigravity 공식 CLI·확장·MCP

| 수단 | 공식 확인 | 로컬·세션 연결의 한계 |
|---|---|---|
| CLI headless | [agy -p / JSON 출력 / conversation 재개](https://antigravity.google/docs/cli/headless/)가 공식 지원됨 | agy·gemini·antigravity 명령은 PATH에서 미발견. 설치된 IDE launcher는 별개이며 채팅 자동화 CLI로 간주하지 않음. 모델 요청 명령 실행0 |
| Python SDK | [google-antigravity / Agent](https://antigravity.google/docs/sdk/overview/)와 Gemini 키/Enterprise 인증 방식이 문서화됨 | 설치·인증·실행 미수행. 앱 구독으로 SDK 추론이 자동 무료라는 주장은 하지 않음 |
| MCP·확장 | [MCP](https://antigravity.google/docs/mcp?tab=cli), [공식 제품/확장 비교](https://antigravity.google/docs/overview?tab=cli) 확인 | MCP client가 도구를 쓰는 기능은 기존 Gemini/Claude 대화를 외부 Codex용 MCP 서버로 노출하는 기능과 다름. 기존 세션을 임의로 연결하지 않음. 전역 MCP/권한 설정 수정0 |
| 세션/원격 제어 | [공식 Remote Control](https://antigravity.google/docs/remote-control/)과 CLI의 conversation 재개 기능 존재 | GUI 세션의 ID·소유권·실제 재개 호환/지원 버전·권한/과금은 이번 미검증. 내부 앱 DB·쿠키·비공개 API를 세션 다리로 쓰지 않음. 서비스/Windows 예약 작업 설치0 |
| 모델/잔여량 | [공식 모델 목록](https://antigravity.google/docs/models/), [CLI /usage](https://antigravity.google/docs/cli/commands/usage/)에서 제품별 모델 조건과 계정별 quota 조회 수단을 설명 | Claude/GPT 계열 표시가 이 계정의 모든 제품에서 사용 가능하다는 뜻은 아님. /usage는 backend를 새로 조회하는 TUI이며 문서의 숫자를 사용자 잔여량으로 쓰지 않음 |

실제 Windows 파일 메타데이터: Antigravity App2.29.0.0, Antigravity IDE2.6.0 설치 확인. IDE launcher --version의1.107.0은 편집기 출력으로 별도 기록하며 제품 버전으로 혼동하지 않는다. App의 version 파일44.5.1도 제품 버전으로 채택하지 않았다. GUI가 설치돼 있어도 CLI·SDK가 준비됐다는 증거는 아니다.

현재 플러그인 카탈로그에서 Antigravity/Gemini/Claude를 조회한 결과는0건이었다. 전체 생태계에 없다는 결론은 아니며 [플러그인 디렉터리](https://chatgpt.com/plugins)에 더 있을 수 있다. 설치·연결·권한 변경은 수행하지 않았다. 공식 CLI/SDK 경로와 별도로 검증되지 않은 제3자 bridge를 도입하지 않았다.

## C. 브라우저 UI 조작

열려 있는 ChatGPT 웹 채팅은 Responses API 대화가 아니다. API conversation ID에 웹 채팅 URL/ID를 넣어 재개하지 않는다. 브라우저 조작은 공식 API보다 DOM/로그인/팝업 변화·대화 선택 오류·불명확한 사용량에 취약하다. 이번에는 웹 자동 입력·클립보드 제출·쿠키 추출·로그인 우회·브라우저 스케줄러를 만들거나 실행하지 않았다.

후속 UI 작업이 필요하면 지원되는 컴퓨터/브라우저 도구와 사이트 조건을 확인하고, **대상 대화·전송할 파일/본문 hash·계정·모델·호출 수·추가 크레딧 소모 여부**를 사용자가 먼저 승인해야 한다. 문서상 browser use 기능이 있다는 사실만으로 모든 사이트의 무제한 자동 입력을 승인한 것으로 해석하지 않는다.

## D. 이번에 실제로 구축한 파일 방식

Python 표준 라이브러리로 검토 요청/응답/결정/테스트 이력을 JSON 파일로 관리한다. 외부 API·브라우저 transport는 아예 없다. 별도 승인과 구현 없이는 설정값만 켜서 호출할 수 없다. 앱/웹에서 사용자가 승인한 내용을 수동으로 전달하고 내보낸 결과를 가져오는 방식이며, 앱이 이 저장소의 JSON을 공식 세션 형식으로 자동 import한다는 뜻은 아니다.

| 비교 | 완전 자동화(후속) | 파일 기반 반자동(이번) |
|---|---|---|
| 장점 | 구조화된 응답/usage 수집, 반복 비용·지연 통제 가능 | 인증/유료 API 없이 로컬 절차 검증, 기존 세션 사용 여부를 사용자가 선택, 작은 구축 범위 |
| 비용·권한 | 모델별 entitlement·요금·계정 연결/승인·반출 검토 필요 | 도구 자체 외부 추론0. 사용자가 앱에 제출하면 그 앱 quota를 소비할 수 있음 |
| 실패 | 비용 발생 뒤 timeout·잘못된 실행/도구 권한 위험 | 수동 전달·응답 형식 오류·출처/모델 사용량 자기신고 한계 |
| 현재 판정 | 문서상 기술적으로 가능, 실제 계정/종단 연결 미검증 | 파일 생성·가져오기·결정·중단/재개·제한·로컬 검사 게이트 구현/오프라인 시험 |

자동화가 모든 기능을 대신 개발하는 단계가 아니다. 현재 구현과 미래 승인 전 조건은 [실행 절차](AI_DEVELOPMENT_WORKFLOW.md)에 분리했다.
