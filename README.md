# kis-auto-trader

한국투자증권 Open API 기반 주식 자동매매 시스템

## 개요

- 기술적 분석 기반 자동 매수/매도 (골든크로스, 모멘텀 전략)
- 웹 대시보드로 시세 조회, 포트폴리오 모니터링, 주문 관리
- 페이퍼 트레이딩 → 모의투자 → 실전 단계적 전환
- 백테스트 엔진으로 전략 사전 검증

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | FastAPI (Python 3.11+), SQLAlchemy, Alembic |
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| DB | SQLite (개발) → PostgreSQL (운영) |
| API | [한국투자증권 Open Trading API](https://github.com/koreainvestment/open-trading-api) |
| CI/CD | GitHub Actions (ruff + pytest) |

## 프로젝트 구조

```
kis-auto-trader/
├── backend/
│   ├── app/
│   │   ├── api/            # REST API 엔드포인트
│   │   │   ├── health.py   # GET /health
│   │   │   ├── trading.py  # 주문, 체결, 시세, 포트폴리오
│   │   │   └── strategy.py # 전략 분석, 백테스트
│   │   ├── core/           # 설정, DB, KIS 인증
│   │   ├── models/         # Stock, Order, Execution, PortfolioItem
│   │   ├── services/       # KIS API 연동, 주문 처리, 시세 조회
│   │   └── strategies/     # 매매 전략 (골든크로스, 모멘텀, 백테스트)
│   └── tests/              # pytest (48 tests)
├── frontend/               # Next.js 대시보드
│   └── src/app/
│       ├── market/         # 시세 조회
│       ├── portfolio/      # 포트폴리오
│       └── orders/         # 주문 내역
├── docs/                   # 설계 문서
└── .github/                # CI, Issue/PR 템플릿, Dependabot
```

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 헬스체크 |
| POST | `/api/orders` | 주문 생성 |
| DELETE | `/api/orders/{id}` | 주문 취소 |
| GET | `/api/orders` | 주문 목록 |
| POST | `/api/execute` | 대기 주문 체결 |
| GET | `/api/price/{code}` | 시세 조회 |
| GET | `/api/portfolio` | 포트폴리오 |
| GET | `/api/strategy/list` | 전략 목록 |
| POST | `/api/strategy/analyze` | 시그널 분석 |
| POST | `/api/strategy/backtest` | 백테스트 실행 |

## 개발 로드맵

- [x] **v0.1** — 프로젝트 셋업, 페이퍼 트레이딩 엔진
- [x] **v0.2** — KIS API 연동 (인증, 시세, 주문)
- [x] **v0.3** — 웹 대시보드 (시세 조회, 포트폴리오, 주문)
- [x] **v0.4** — 매매 전략 엔진 + 백테스트
- [ ] **v1.0** — 실전 투자 연동

## 시작하기

### 백엔드

```bash
cd backend
uv sync                        # 의존성 설치
uv run alembic upgrade head    # DB 마이그레이션
uv run fastapi dev             # 개발 서버 (http://localhost:8000)
uv run pytest -v               # 테스트
```

### 프론트엔드

```bash
cd frontend
npm install                    # 의존성 설치
npm run dev                    # 개발 서버 (http://localhost:3000)
```

### KIS API 연동 (선택)

1. [한국투자증권](https://www.koreainvestment.com/) 계좌 개설
2. Open API 신청 → 앱키/시크릿 발급
3. 설정 파일 생성:

```yaml
# ~/KIS/config/kis_devlp.yaml
my_app: "앱키"
my_sec: "앱시크릿"
my_acct: "계좌번호"
my_id: "HTS ID"
```

4. 환경변수로 모드 전환:

```bash
export KIS_KIS_ENV=virtual      # 모의투자
export KIS_KIS_ENV=production   # 실전투자
```

## 면책조항

이 소프트웨어는 교육 및 개인 프로젝트 목적으로 제작되었습니다.
이 소프트웨어를 사용하여 발생하는 모든 투자 손실에 대해 개발자는 어떠한 책임도 지지 않습니다.
투자에 대한 최종 판단과 책임은 사용자 본인에게 있습니다.

## License

MIT
