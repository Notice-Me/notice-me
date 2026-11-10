# API 키 설정 — 처음 사용하는 경우

API 키는 데이터 사이트에서 “이 요청을 보낸 계정”을 확인하는 접속 비밀값입니다. 서비스 이름은 그 키를 발급한 사이트 이름입니다. GitHub 로그인은 뉴스/서울시 계정 로그인과 별개입니다. 키를 채팅에 붙여 넣지 마세요.

## 지금 키 없이 되는 기능

Mock 전체 시연과 서울시 공식 sample 수집은 바로 가능합니다. `server/.env`에는 템플릿을 복사해 두었습니다. 개인 키는 비어 있습니다. 기존 파일이 있으면 덮어쓰지 않습니다. 이 파일은 Git에서 제외합니다.

## 권장 발급 순서

1. [FreeNewsAPI](https://www.freenewsapi.io/)의 Get Free API Key → 본인이 가입/이메일 인증 → 발급된 키를 로컬 `server/.env`의 `NOTICE_FREENEWS_API_KEY=` 뒤에 입력 → 저장. **.io** 사이트가 이 프로젝트의 1순위이며 비슷한 이름의 .ai 사이트와 다릅니다. 무료 서비스만 사용하고 결제/유료 전환은 하지 않습니다.
2. [서울 열린데이터광장](https://data.seoul.go.kr/) 로그인 → 원하는 데이터셋의 인증키 신청 → `NOTICE_SEOUL_API_KEY=sample`을 본인 키로 교체. sample은 처음 5건 및 광화문·덕수궁으로 제한되므로 초기 시연만으로 충분하면 발급을 미뤄도 됩니다. 계정별 실제 허용량은 발급 화면에서 확인합니다.
3. [공공데이터포털 TourAPI](https://www.data.go.kr/data/15101578/openapi.do) → 회원가입/로그인 → 활용신청 → 승인된 **Decoding** 인증키를 `NOTICE_TOUR_API_KEY=`에 입력. 이미 URL 인코딩된 키를 다시 인코딩하지 않도록 Decoding 값을 사용합니다. 기본 개발계정 트래픽 표시는 1,000이며 실제 승인 할당량을 확인합니다.
4. 비교가 필요할 때만 [The News API](https://www.thenewsapi.com/)의 Free 가입 후 `NOTICE_THENEWSAPI_TOKEN=`, [GNews](https://gnews.io/)의 Free 가입 후 `NOTICE_GNEWS_API_KEY=`를 설정합니다. GNews의 현재 공식 언어/국가 필터 목록에는 한국어/한국이 없어 우선순위가 낮습니다. 유료 trial과 결제정보를 등록하지 않습니다.

국가교통정보센터는 현재 상세 공식 문서 접근 문제와 인증키 부재로 어댑터를 구현하지 않았습니다. `NOTICE_ITS_API_KEY`는 예약된 설정일 뿐이며 값을 넣는 것만으로 연동되지는 않습니다. 학교 AI 토큰도 아직 넣을 필드가 없습니다. 공식 엔드포인트/인증 방식/응답 계약을 받은 뒤 연결합니다.

## 입력 후 실행

서버를 종료 후 다시 실행하면 .env 변경을 반영합니다. PowerShell에서 앞서 설정한 `$env:NOTICE_...` 값이 있으면 .env보다 우선하므로 의도한 모드인지 확인하세요. 키 값을 출력하는 명령은 실행하지 마세요.

```powershell
cd server
.venv\Scripts\python.exe -m app.cli validate --report reports/validation.json
.venv\Scripts\python.exe -m app.cli ingest --keyword '애니메이션'
```

검증 결과의 `SUCCESS`는 해당 호출의 성공입니다. 뉴스 키워드별 `reported_total=null`은 미측정/미제공이며 0건을 뜻하지 않습니다. 키를 발급받아도 언론사 AI 요약·TTS 재배포권이 자동 생기지 않습니다. 뉴스는 권리 근거 확인 전 `LICENSE_UNVERIFIED`이고 음성 큐·설명에서 차단됩니다.
