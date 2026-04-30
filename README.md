<h1 align="center">KIS Auto Trader</h1>

<p align="center">
  <strong>한국투자증권 Open API 기반 주식 자동매매 시스템</strong><br/>
  <sub>API 키 하나로 전략 설정 → 자동 매수/매도 → 손절/익절 → 알림까지</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js-15-000000?logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker" />
</p>

<p align="center">
  <a href="https://github.com/kangminlog/kis-auto-trader/actions"><img src="https://github.com/kangminlog/kis-auto-trader/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://github.com/kangminlog/kis-auto-trader/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License" /></a>
  <img src="https://img.shields.io/badge/tests-115%20passed-brightgreen" alt="Tests" />
  <img src="https://img.shields.io/badge/API-28%20endpoints-blue" alt="API" />
</p>

---

## What It Does

```
종목+전략 설정 → 스케줄러 자동 실행 → 시그널 감지 → 자동 주문 → 손절/익절 감시 → 알림
```

> **API 키 없이도** Paper Trading 모드로 모든 기능을 체험할 수 있습니다.

---

## 주요 기능

<table>
<tr>
  <td width="50%">

**자동매매 엔진**
- N분 간격 전략 자동 실행
- BUY/SELL 시그널 → 자동 주문
- 종목별 손절가/익절가 지정
- Kill Switch 긴급 정지

  </td>
  <td width="50%">

**매매 전략 (3종 내장)**
- Golden Cross (이동평균 교차)
- Momentum (N일 수익률)
- **Volume Breakout Retest** (6단계 퀀트 필터)

  </td>
</tr>
<tr>
  <td>

**웹 대시보드 (6개 페이지)**
- 대시보드 (상태, 안전장치, 로그)
- 시세 조회 + 주문 생성
- 자동매매 설정/스케줄러/로그
- 포트폴리오, 주문 내역

  </td>
  <td>

**안전장치**
- Kill Switch (즉시 전체 중단)
- 일일 매매 횟수/금액 한도
- 글로벌 % 손절/익절
- 종목별 절대 가격 손절/익절
- 중복 주문 방지

  </td>
</tr>
</table>

---

## Volume Breakout Retest 전략

> 거래대금 폭발일을 앵커로, 충분히 횡보한 뒤 재접근 시 매수하는 퀀트 전략

```
Peak Day 탐색 (132거래일)
  → ① Turnover >= 10% ✓
  → ② 양봉 확인 ✓
  → ③ FOMO 제외 ✓
  → ④ 횡보 >= 15일 ✓
  → ⑤ 추격 금지 (< 15%) ✓
  → ⑥ 근접도 ±3% → BUY
  → ATR(14) × Regime 배수로 TP/SL 자동 계산
  → 30~50만원/종목 자동 사이징
```

| Regime | TP 배수 | SL 배수 |
|--------|---------|---------|
| BULL | 5.0x ATR | 2.0x ATR |
| BEAR | 4.0x ATR | 2.5x ATR |
| SIDE | 3.0x ATR | 1.8x ATR |

> 상세 스펙: [`docs/strategy-volume-breakout-retest.md`](docs/strategy-volume-breakout-retest.md)

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| **Backend** | FastAPI, SQLAlchemy, Alembic, APScheduler, PyJWT, bcrypt |
| **Frontend** | Next.js 15, TypeScript, Tailwind CSS |
| **Database** | SQLite (개발) / PostgreSQL 16 (운영) |
| **Infra** | Docker Compose, GitHub Actions, Dependabot |
| **API** | [한국투자증권 Open Trading API](https://github.com/koreainvestment/open-trading-api) |

---

## 빠른 시작

### 1. 로컬 실행

```bash
# 백엔드
cd backend
uv sync && uv run alembic upgrade head && uv run fastapi dev

# 프론트엔드 (새 터미널)
cd frontend
npm install && npm run dev
```

### 2. Docker Compose

```bash
docker compose up --build
```

### 3. 접속

| 서비스 | URL |
|--------|-----|
| 대시보드 | http://localhost:3000 |
| API 서버 | http://localhost:8000 |
| Swagger 문서 | http://localhost:8000/docs |

> 첫 접속 시 `/login` → **계정 생성** → 로그인

---

## KIS API 연동

```bash
# 1. 설정 파일
mkdir -p ~/KIS/config
cat > ~/KIS/config/kis_devlp.yaml << EOF
my_app: "발급받은 앱키"
my_sec: "발급받은 앱시크릿"
my_acct: "계좌번호"
my_id: "HTS ID"
EOF

# 2. 환경변수
export KIS_KIS_ENV=virtual              # 모의투자 (먼저 이걸로 검증!)
export KIS_SCHEDULER_AUTO_START=true    # 서버 시작 시 자동매매 시작
export KIS_SECRET_KEY="32자이상시크릿키"

# 3. 실행
cd backend && uv run fastapi dev
```

| 환경 | 환경변수 | 설명 |
|------|---------|------|
| `paper` | 기본값 | 더미 시세, API 키 불필요 |
| `virtual` | `KIS_KIS_ENV=virtual` | 모의투자 (가상 자금) |
| `production` | `KIS_KIS_ENV=production` | **실전투자 (실제 자금!)** |

> **반드시 `virtual`에서 충분히 검증한 후 `production`으로 전환하세요.**

---

## 프로젝트 구조

```
kis-auto-trader/
├── backend/
│   ├── app/
│   │   ├── api/              # 28개 REST API 엔드포인트
│   │   │   ├── auth.py       # 인증 (JWT)
│   │   │   ├── auto_trade.py # 자동매매 설정/스케줄러/로그
│   │   │   ├── safety.py     # 안전장치 (kill switch, 한도)
│   │   │   ├── scan_config.py# 전략 파라미터 관리/튜닝
│   │   │   ├── strategy.py   # 전략 분석/백테스트
│   │   │   └── trading.py    # 주문/체결/시세/포트폴리오
│   │   ├── core/             # 설정, DB, KIS 인증, JWT
│   │   ├── models/           # ORM 8 테이블
│   │   ├── services/         # 비즈니스 로직
│   │   │   ├── auto_trader.py     # 자동매매 엔진
│   │   │   ├── balance_sync.py    # KIS 잔고 동기화
│   │   │   ├── provider_factory.py# 환경별 시세 자동 전환
│   │   │   ├── safety.py          # 안전장치
│   │   │   ├── scheduler.py       # APScheduler
│   │   │   └── universe.py        # 유니버스 필터
│   │   └── strategies/       # 매매 전략
│   │       ├── volume_breakout.py # Volume Breakout Retest
│   │       ├── golden_cross.py    # 골든크로스
│   │       ├── momentum.py        # 모멘텀
│   │       ├── indicators.py      # ATR, Regime, Sizing
│   │       └── backtest.py        # 백테스트 엔진
│   └── tests/                # 115 tests
├── frontend/                 # Next.js 대시보드
│   └── src/
│       ├── app/              # 6개 페이지
│       ├── components/       # Nav (로그아웃)
│       └── lib/              # API 헬퍼, 인증
├── docs/                     # 전략 스펙 문서
├── docker-compose.yml        # PostgreSQL + backend + frontend
└── .github/                  # CI, 템플릿, Dependabot
```

---

<details>
<summary><strong>API 엔드포인트 (28개)</strong></summary>

#### 공개
| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 헬스체크 |
| POST | `/api/auth/setup` | 초기 관리자 설정 |
| POST | `/api/auth/login` | 로그인 (JWT 발급) |

#### 매매
| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/orders` | 주문 생성 |
| DELETE | `/api/orders/{id}` | 주문 취소 |
| GET | `/api/orders` | 주문 목록 |
| POST | `/api/execute` | 대기 주문 체결 |
| GET | `/api/price/{code}` | 시세 조회 |
| GET | `/api/portfolio` | 포트폴리오 |
| POST | `/api/portfolio/sync` | KIS 잔고 동기화 |

#### 전략
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/strategy/list` | 전략 목록 |
| POST | `/api/strategy/analyze` | 시그널 분석 |
| POST | `/api/strategy/backtest` | 백테스트 |

#### 자동매매
| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/auto-trade/configs` | 설정 추가 |
| GET | `/api/auto-trade/configs` | 설정 목록 |
| PATCH | `/api/auto-trade/configs/{id}/toggle` | 활성/비활성 |
| DELETE | `/api/auto-trade/configs/{id}` | 설정 삭제 |
| GET | `/api/auto-trade/scheduler/status` | 스케줄러 상태 |
| POST | `/api/auto-trade/scheduler/start` | 스케줄러 시작 |
| POST | `/api/auto-trade/scheduler/stop` | 스케줄러 중지 |
| POST | `/api/auto-trade/scheduler/trigger` | 수동 실행 |
| GET | `/api/auto-trade/logs` | 실행 로그 |

#### 안전장치
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/safety/status` | 안전장치 상태 |
| POST | `/api/safety/kill-switch` | Kill Switch |
| PATCH | `/api/safety/config` | 한도 설정 |

#### 파라미터 관리
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/scan-config/params` | 전체 파라미터 |
| POST | `/api/scan-config/init` | 기본값 초기화 |
| PATCH | `/api/scan-config/params` | 파라미터 수정 |
| POST | `/api/scan-config/tuning/run` | 튜닝 실행 |
| POST | `/api/scan-config/tuning/apply` | 튜닝 적용 |

</details>

---

## 개발 로드맵

- [x] **v0.1** — 페이퍼 트레이딩 엔진
- [x] **v0.2** — KIS API 연동 (인증, 시세, 주문)
- [x] **v0.3** — 웹 대시보드
- [x] **v0.4** — 매매 전략 엔진 + 백테스트
- [x] **v1.0** — 자동매매 스케줄러, 안전장치, 인증, 알림, Docker 배포
- [x] **v1.1** — Volume Breakout Retest 전략, 유니버스 스캐너, 동적 파라미터 튜닝, 로그인 UI, 환경 자동 전환

---

## 면책조항

이 소프트웨어는 교육 및 개인 프로젝트 목적으로 제작되었습니다.
이 소프트웨어를 사용하여 발생하는 모든 투자 손실에 대해 개발자는 어떠한 책임도 지지 않습니다.
**투자에 대한 최종 판단과 책임은 사용자 본인에게 있습니다.**

## License

[MIT](LICENSE)
