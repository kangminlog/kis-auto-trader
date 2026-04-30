# Volume Breakout Retest 전략 스펙

## 핵심 아이디어

과거 N일 중 시총 대비 거래대금이 가장 터진 날(peak day)을 앵커로.
그 뒤 충분히 횡보해서 에너지 축적되고, 다시 그 가격대 근처로 돌아왔을 때 BUY.

= "한 번 들어왔던 자리에 다시 오는 것" = 재돌파 직전 매집 가정.

## ① 유니버스 필터

- symbol_type=STOCK (ETF/채권/펀드 제외)
- 상장폐지/관리/투자주의/투자경고 제외
- 시총 1,000억 ~ 5조
- 종목명에 "액티브/머니마켓/채권" 포함 시 제외
- 오늘 거래정지 / 블랙리스트 제외

## ② 평가 조건 (순차 체크, 하나라도 실패 시 PASS)

| # | 조건 | 임계값 | 실패 사유 예 |
|---|------|--------|------------|
| 1 | turnover >= X% (peak day 거래대금/시총) | 10.0% | "turnover 4% < 10%" |
| 2 | 양봉 peak day (음봉=투매 제외) | — | "peak day 음봉, 투매" |
| 3 | FOMO 제외: 당일 +5%↑ && 거래량배수 < 3배 | 5% / 3배 | "FOMO: +6.2% vol×1.5" |
| 4 | 횡보 충분: peak 이후 경과일 >= N | 15거래일 | "days_since=8 < 15" |
| 5 | 추격 금지: peak 이후 최고가 +N% 미만 | 15% | "breakthrough 18% >= 15%" |
| 6 | 근접도: 현재가 vs peak 종가 ±X% 이내 → BUY | ±3% | "proximity +4.5% too far" |

## ③ TP/SL — ATR(14) 기반, Regime별 다른 배수

```
TP = 현재가 + k_tp × ATR(14)
SL = 현재가 − k_sl × ATR(14)
```

| Regime | k_tp | k_sl |
|--------|------|------|
| BULL | 5.0 | 2.0 |
| BEAR | 4.0 | 2.5 |
| SIDE | 3.0 | 1.8 |

## ④ 사이징

- 주문금액: 30~50만원/종목 (sizing.min/max_amount_krw)
- 현재가로 나눠서 주수 계산

## ⑤ 동적 파라미터 튜닝

- signal_outcomes 기반 월 1회 k_tp/k_sl 자동 보정
- N라운드 파라미터 개선안 제안 → 수동 승인 후 scan_config 업데이트

## ⑥ Lookback 창

- 과거 132 거래일 (약 6개월)에서 peak day 탐색

## 구현 파일

| 파일 | 역할 |
|------|------|
| `backend/app/strategies/volume_breakout.py` | 전략 메인 로직 |
| `backend/app/strategies/indicators.py` | ATR, Regime, Peak Day, Sizing 유틸 |
| `backend/tests/test_volume_breakout.py` | 14개 테스트 |

## 파라미터 목록

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| lookback | 132 | peak day 탐색 기간 (거래일) |
| min_turnover_pct | 10.0 | 최소 turnover 비율 (%) |
| fomo_gain_pct | 5.0 | FOMO 판단 당일 등락 기준 (%) |
| fomo_vol_multiple | 3.0 | FOMO 판단 거래량 배수 기준 |
| min_days_since_peak | 15 | peak 이후 최소 횡보 기간 (거래일) |
| max_breakthrough_pct | 15.0 | peak 이후 최고가 상한 (%) |
| proximity_pct | 3.0 | 현재가-peak 근접 범위 (±%) |
| min_amount_krw | 300,000 | 최소 주문 금액 (원) |
| max_amount_krw | 500,000 | 최대 주문 금액 (원) |

## 미구현 (향후)

- 유니버스 자동 스캔 (현재는 수동 종목 지정)
- 동적 파라미터 튜닝 (signal_outcomes 기반 자동 보정)
- scan_config DB 테이블 (현재는 코드 내 기본값)
