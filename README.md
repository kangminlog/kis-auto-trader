<h1 align="center">KIS Auto Trader</h1>

<p align="center">
  <strong>한국투자증권 Open API 기반 주식 자동매매 시스템</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js-15-black?logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker" />
</p>

<p align="center">
  <a href="https://github.com/kangminlog/kis-auto-trader/actions"><img src="https://github.com/kangminlog/kis-auto-trader/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://github.com/kangminlog/kis-auto-trader/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License" /></a>
  <img src="https://img.shields.io/badge/tests-79%20passed-brightgreen" alt="Tests" />
</p>

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| **자동매매 엔진** | 전략 기반 자동 매수/매도, 스케줄러로 N분 간격 실행 |
| **매매 전략** | 골든크로스, 모멘텀 전략 내장 + 플러그인 방식 확장 |
| **백테스트** | 과거 데이터로 전략 검증 (수익률, MDD, 승률) |
| **웹 대시보드** | 시세 조회, 주문 관리, 포트폴리오, 자동매매 설정 |
| **안전장치** | Kill Switch, 일일 매매 한도, 손절/익절 자동 매도 |
| **인증** | JWT 기반 API 인증 |
| **알림** | 텔레그램 봇 연동 (매매 체결 알림) |
| **3단계 전환** | Paper Trading → 모의투자 → 실전투자 |

---

## 기술 스택

<table>
<tr><td><strong>Backend</strong></td><td>FastAPI, SQLAlchemy, Alembic, APScheduler, PyJWT</td></tr>
<tr><td><strong>Frontend</strong></td><td>Next.js 15, TypeScript, Tailwind CSS</td></tr>
<tr><td><strong>Database</strong></td><td>SQLite (개발) / PostgreSQL 16 (운영)</td></tr>
<tr><td><strong>Infra</strong></td><td>Docker Compose, GitHub Actions CI/CD, Dependabot</td></tr>
<tr><td><strong>API</strong></td><td><a href="https://github.com/koreainvestment/open-trading-api">한국투자증권 Open Trading API</a></td></tr>
</table>

---

## 프로젝트 구조

```
kis-auto-trader/
├── backend/
│   ├── app/
│   │   ├── api/            # REST API (22개 엔드포인트)
│   │   │   ├── auth.py     # 인증 (login, setup)
│   │   │   ├── auto_trade.py # 자동매매 설정/스케줄러
│   │   │   ├── health.py   # 헬스체크
│   │   │   ├── safety.py   # 안전장치 (kill switch, 한도)
│   │   │   ├── strategy.py # 전략 분석, 백테스트
│   │   │   └── trading.py  # 주문, 체결, 시세, 포트폴리오
│   │   ├── core/           # 설정, DB, KIS 인증, JWT
│   │   ├── models/         # ORM 모델 6종
│   │   ├── services/       # 비즈니스 로직
│   │   └── strategies/     # 매매 전략 프레임워크
│   └── tests/              # 79 tests
├── frontend/               # Next.js 웹 대시보드
│   └── src/app/
│       ├── auto-trade/     # 자동매매 설정/로그
│       ├── market/         # 시세 조회 + 주문 생성
│       ├── orders/         # 주문 내역
│       └── portfolio/      # 포트폴리오
├── docker-compose.yml      # 원커맨드 배포
└── .github/                # CI, 템플릿, Dependabot
```

---

## 빠른 시작

### 로컬 개발

```bash
# 백엔드
cd backend
uv sync                        # 의존성 설치
uv run alembic upgrade head    # DB 마이그레이션
uv run fastapi dev             # http://localhost:8000

# 프론트엔드 (새 터미널)
cd frontend
npm install
npm run dev                    # http://localhost:3000
```

### Docker Compose

```bash
docker compose up --build      # 전체 실행 (backend + frontend + PostgreSQL)
```

> 백엔드: `http://localhost:8000` | 프론트엔드: `http://localhost:3000` | API 문서: `http://localhost:8000/docs`

---

## API 엔드포인트

<details>
<summary><strong>22개 엔드포인트 전체 보기</strong></summary>

#### 공개
| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 헬스체크 |
| POST | `/api/auth/setup` | 초기 관리자 설정 |
| POST | `/api/auth/login` | 로그인 (JWT 발급) |

#### 매매 (인증 필요)
| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/orders` | 주문 생성 |
| DELETE | `/api/orders/{id}` | 주문 취소 |
| GET | `/api/orders` | 주문 목록 |
| POST | `/api/execute` | 대기 주문 체결 |
| GET | `/api/price/{code}` | 시세 조회 |
| GET | `/api/portfolio` | 포트폴리오 |

#### 전략 (인증 필요)
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/strategy/list` | 전략 목록 |
| POST | `/api/strategy/analyze` | 시그널 분석 |
| POST | `/api/strategy/backtest` | 백테스트 실행 |

#### 자동매매 (인증 필요)
| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/auto-trade/configs` | 자동매매 설정 추가 |
| GET | `/api/auto-trade/configs` | 설정 목록 |
| PATCH | `/api/auto-trade/configs/{id}/toggle` | 활성/비활성 |
| DELETE | `/api/auto-trade/configs/{id}` | 설정 삭제 |
| GET | `/api/auto-trade/scheduler/status` | 스케줄러 상태 |
| POST | `/api/auto-trade/scheduler/start` | 스케줄러 시작 |
| POST | `/api/auto-trade/scheduler/stop` | 스케줄러 중지 |
| POST | `/api/auto-trade/scheduler/trigger` | 수동 실행 |
| GET | `/api/auto-trade/logs` | 실행 로그 |

#### 안전장치 (인증 필요)
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/safety/status` | 안전장치 상태 |
| POST | `/api/safety/kill-switch` | Kill Switch 토글 |
| PATCH | `/api/safety/config` | 한도/손절/익절 설정 |

</details>

---

## 개발 로드맵

- [x] **v0.1** — 프로젝트 셋업, 페이퍼 트레이딩 엔진
- [x] **v0.2** — KIS API 연동 (인증, 시세, 주문)
- [x] **v0.3** — 웹 대시보드 (시세, 포트폴리오, 주문)
- [x] **v0.4** — 매매 전략 엔진 + 백테스트
- [x] **v1.0** — 자동매매 스케줄러, 안전장치, 인증, 알림, Docker 배포

---

## KIS API 연동

> KIS API 키 없이도 Paper Trading 모드로 모든 기능을 사용할 수 있습니다.

실제 증권사 연동 시:

1. [한국투자증권](https://www.koreainvestment.com/) 계좌 개설 + Open API 신청
2. 설정 파일 생성:

```yaml
# ~/KIS/config/kis_devlp.yaml
my_app: "앱키"
my_sec: "앱시크릿"
my_acct: "계좌번호"
my_id: "HTS ID"
```

3. 환경변수로 모드 전환:

```bash
export KIS_KIS_ENV=virtual      # 모의투자
export KIS_KIS_ENV=production   # 실전투자 (주의!)
```

> **주의**: 실전투자 모드는 실제 자금이 사용됩니다. 반드시 모의투자에서 충분히 검증 후 전환하세요.

---

## 면책조항

이 소프트웨어는 교육 및 개인 프로젝트 목적으로 제작되었습니다.
이 소프트웨어를 사용하여 발생하는 모든 투자 손실에 대해 개발자는 어떠한 책임도 지지 않습니다.
**투자에 대한 최종 판단과 책임은 사용자 본인에게 있습니다.**

## License

[MIT](LICENSE)
