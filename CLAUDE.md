# CLAUDE.md

## 프로젝트 개요

한국투자증권 Open API 기반 주식 자동매매 시스템.
FastAPI 백엔드 + Next.js 프론트엔드 구조.

참고 레포: https://github.com/koreainvestment/open-trading-api

## 현재 상태 (v0.4 완료)

- v0.1~v0.4 완료, v1.0 진행 중
- 48 tests, CI (backend lint+test, frontend lint+build)
- 현재 "자동매매"는 수동 API 호출 필요 → 자동 스케줄러 미구현
- 프론트엔드에 주문 생성 폼/전략 설정 화면 없음

### v1.0 작업 순서
1. #25 자동매매 스케줄러 (핵심 자동 루프)
2. #30 주문 생성 폼 + 전략 활성화 UI
3. #24 안전장치 (손절, 일일 한도, kill switch)
4. #32 API 인증/인가
5. #31 PostgreSQL 전환
6. #27 텔레그램 알림
7. #28 Docker Compose 배포
8. #26 대시보드 실시간 업데이트

## 아키텍처

- `/backend` — FastAPI 기반 매매 엔진, KIS API 연동
  - `/app/api` — REST API 엔드포인트 (health, trading, strategy)
  - `/app/core` — 설정, DB, KIS 인증
  - `/app/models` — Stock, Order, Execution, PortfolioItem (SQLAlchemy)
  - `/app/services` — KIS API 클라이언트, 주문 처리, 시세 조회, 체결 엔진
  - `/app/strategies` — BaseStrategy, 골든크로스, 모멘텀, 백테스트, 러너
  - `/tests` — pytest 48건
- `/frontend` — Next.js 15 + TypeScript + Tailwind CSS
  - `/src/app` — 대시보드, 시세 조회, 포트폴리오, 주문 내역
  - `/src/lib/api.ts` — 백엔드 API 헬퍼
- `/docs` — 설계 문서

## 개발 규칙

### 코드 스타일
- Python: ruff 포맷팅 및 린팅, 타입 힌트 필수
- TypeScript: ESLint + Prettier
- 커밋 메시지: Conventional Commits (feat:, fix:, docs:, refactor:, test:, chore:)

### Git 워크플로우
- 모든 작업은 Issue 기반으로 진행
- 브랜치 네이밍: `{type}/#{issue번호}-{설명}` (예: `feat/#12-add-order-api`)
- PR 생성 시 `Closes #{issue번호}` 포함
- main 브랜치 직접 커밋 금지
- PR 머지 전략: **Squash Merge** (1 PR = 1 커밋으로 main 히스토리 정리)

### GitHub 운영 규칙

#### Projects 보드
- 보드 URL: https://github.com/users/kangminlog/projects/1
- 칸반 방식: `Todo` → `In Progress` → `Done`
- Issue 생성 시 반드시 보드에 추가
- 작업 시작 시 `In Progress`로 이동, PR 머지 시 `Done`으로 이동

#### Milestones
| Milestone | 목표 |
|-----------|------|
| v0.1 - 페이퍼 트레이딩 | 더미 데이터 기반 매매 시뮬레이션 |
| v0.2 - KIS API 연동 | 모의투자 API 인증/시세/주문 |
| v0.3 - 웹 대시보드 | Next.js 시세 조회, 잔고 확인 UI |
| v0.4 - 전략 엔진 | 매매 전략 프레임워크 + 백테스트 |
| v1.0 - 실전 투자 | 실전 연동 및 안정화 |

- 모든 Issue는 반드시 Milestone에 할당
- Milestone 단위로 릴리즈 진행

#### Labels
| Label | 용도 |
|-------|------|
| `feature` | 새로운 기능 |
| `bug` | 버그 수정 |
| `backend` | 백엔드 관련 |
| `frontend` | 프론트엔드 관련 |
| `strategy` | 매매 전략 관련 |
| `infra` | CI/CD, 배포, 인프라 |
| `docs` | 문서 작업 |
| `refactor` | 리팩토링 |

- Issue 생성 시 최소 1개 이상의 Label 부착
- 영역 Label(`backend`, `frontend`, `strategy`) + 유형 Label(`feature`, `bug`) 조합 권장

#### Issue 템플릿
- `.github/ISSUE_TEMPLATE/feature.md` — 기능 요청
- `.github/ISSUE_TEMPLATE/bug.md` — 버그 리포트

#### GitHub Actions (CI)
- `.github/workflows/ci.yml` — PR 및 main 푸시 시 자동 실행
- 백엔드: ruff lint → ruff format check → pytest
- 프론트엔드: eslint → next build
- CI 통과 필수 (Branch Protection에 연동)

#### Branch Protection (main)
- main 직접 푸시 차단
- PR을 통해서만 머지 가능
- CI (Backend Lint & Test) 통과 필수
- 관리자도 규칙 적용 (enforce_admins)

#### PR Template
- `.github/pull_request_template.md` — PR 생성 시 자동 적용
- Summary, Related Issue, Changes, Checklist 포함

#### Discussions
- 설계 결정, 아이디어 논의, 기술 검토 등 Issue와 분리된 논의 공간
- Issue: 구체적 작업 단위 / Discussion: 열린 논의, 의사결정 기록

#### 작업 흐름 요약
1. Issue 생성 (템플릿 사용, Label + Milestone 할당, 보드에 추가)
2. 브랜치 생성: `feat/#3-add-paper-trading`
3. 작업 → 커밋 (Conventional Commits)
4. PR 생성 (`Closes #3` 포함, 보드에서 `In Progress`)
5. CI 자동 실행 (lint + test)
6. CI 통과 → Squash Merge → 보드에서 `Done`

### KIS API 관련
- 인증 정보(앱키, 시크릿)는 `kis_devlp.yaml`에 저장 → .gitignore 대상
- 환경 전환(모의/실전)은 환경변수 `KIS_ENV`로 관리 (`paper` | `virtual` | `production`)
- API 키는 절대 커밋하지 않음
- API 호출은 반드시 서비스 레이어를 통해 수행

### 테스트
- 더미 데이터 기반 단위 테스트 우선
- KIS API 호출은 mock 처리
- `pytest` 사용, 커버리지 목표 80%

## 명령어

```bash
# 백엔드
cd backend && uv run fastapi dev       # 개발 서버
cd backend && uv run pytest            # 테스트
cd backend && uv run ruff check .      # 린트
cd backend && uv run ruff format .     # 포맷

# 프론트엔드
cd frontend && npm run dev             # 개발 서버
cd frontend && npm run build           # 빌드
cd frontend && npm run lint            # 린트
```
