# kis-auto-trader

한국투자증권 Open API 기반 주식 자동매매 시스템

## 개요

- 기술적 분석 기반 자동 매수/매도
- 웹 대시보드로 실시간 모니터링
- 페이퍼 트레이딩 → 모의투자 → 실전 단계적 전환

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | FastAPI (Python 3.11+) |
| Frontend | Next.js + TradingView Lightweight Charts |
| DB | SQLite (개발) → PostgreSQL (운영) |
| API | [한국투자증권 Open Trading API](https://github.com/koreainvestment/open-trading-api) |
| 알림 | Telegram Bot |

## 프로젝트 구조

```
kis-auto-trader/
├── backend/
│   ├── app/
│   │   ├── api/          # API 엔드포인트
│   │   ├── core/         # 설정, 인증, 공통 유틸
│   │   ├── models/       # 데이터 모델
│   │   ├── services/     # KIS API 연동, 주문 처리
│   │   └── strategies/   # 매매 전략 로직
│   └── tests/            # 테스트
├── frontend/             # Next.js 대시보드
├── docs/                 # 설계 문서
└── .github/              # Issue 템플릿, CI/CD
```

## 개발 로드맵

- **v0.1** — 프로젝트 셋업, 더미 데이터 기반 페이퍼 트레이딩 엔진
- **v0.2** — KIS API 연동 (모의투자)
- **v0.3** — 웹 대시보드 (시세 조회, 잔고 확인)
- **v0.4** — 매매 전략 엔진 + 백테스트
- **v1.0** — 실전 투자 연동

## 시작하기

> 추후 작성 예정

## 면책조항

이 소프트웨어는 교육 및 개인 프로젝트 목적으로 제작되었습니다.
이 소프트웨어를 사용하여 발생하는 모든 투자 손실에 대해 개발자는 어떠한 책임도 지지 않습니다.
투자에 대한 최종 판단과 책임은 사용자 본인에게 있습니다.

## License

MIT
