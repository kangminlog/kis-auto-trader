"""scan_config 파라미터 관리 + 동적 튜닝."""

import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.scan_config import ScanConfig, SignalOutcome

logger = logging.getLogger(__name__)

# 기본 파라미터 (22 keys)
DEFAULT_PARAMS: dict[str, tuple[str, str]] = {
    # Volume Breakout
    "lookback": ("132", "peak day 탐색 기간 (거래일)"),
    "min_turnover_pct": ("10.0", "최소 turnover 비율 (%)"),
    "fomo_gain_pct": ("5.0", "FOMO 판단 당일 등락 기준 (%)"),
    "fomo_vol_multiple": ("3.0", "FOMO 판단 거래량 배수"),
    "min_days_since_peak": ("15", "peak 이후 최소 횡보 기간 (거래일)"),
    "max_breakthrough_pct": ("15.0", "peak 이후 최고가 상한 (%)"),
    "proximity_pct": ("3.0", "현재가-peak 근접 범위 (±%)"),
    # TP/SL (regime별)
    "k_tp_bull": ("5.0", "BULL regime TP ATR 배수"),
    "k_sl_bull": ("2.0", "BULL regime SL ATR 배수"),
    "k_tp_bear": ("4.0", "BEAR regime TP ATR 배수"),
    "k_sl_bear": ("2.5", "BEAR regime SL ATR 배수"),
    "k_tp_side": ("3.0", "SIDE regime TP ATR 배수"),
    "k_sl_side": ("1.8", "SIDE regime SL ATR 배수"),
    # Sizing
    "sizing_min_amount_krw": ("300000", "최소 주문 금액 (원)"),
    "sizing_max_amount_krw": ("500000", "최대 주문 금액 (원)"),
    # Universe
    "universe_min_market_cap": ("100000000000", "유니버스 최소 시총"),
    "universe_max_market_cap": ("5000000000000", "유니버스 최대 시총"),
    # General
    "atr_period": ("14", "ATR 계산 기간"),
    "regime_ma_period": ("60", "Regime 판별 MA 기간"),
    # Tuning
    "tuning_min_samples": ("20", "튜닝 최소 샘플 수"),
    "tuning_interval_days": ("30", "튜닝 주기 (일)"),
    "tuning_last_run": ("", "마지막 튜닝 실행일"),
}


def init_default_params(db: Session) -> int:
    """기본 파라미터 초기화. 이미 존재하는 키는 스킵."""
    created = 0
    for key, (value, desc) in DEFAULT_PARAMS.items():
        existing = db.query(ScanConfig).filter_by(key=key).first()
        if not existing:
            db.add(ScanConfig(key=key, value=value, description=desc))
            created += 1
    db.commit()
    return created


def get_param(db: Session, key: str) -> str:
    """파라미터 값 조회. 없으면 기본값."""
    config = db.query(ScanConfig).filter_by(key=key).first()
    if config:
        return config.value
    default = DEFAULT_PARAMS.get(key)
    return default[0] if default else ""


def get_param_float(db: Session, key: str) -> float:
    return float(get_param(db, key) or "0")


def get_param_int(db: Session, key: str) -> int:
    return int(float(get_param(db, key) or "0"))


def set_param(db: Session, key: str, value: str) -> ScanConfig:
    """파라미터 값 설정."""
    config = db.query(ScanConfig).filter_by(key=key).first()
    if config:
        config.value = value
    else:
        desc = DEFAULT_PARAMS.get(key, ("", ""))[1]
        config = ScanConfig(key=key, value=value, description=desc)
        db.add(config)
    db.commit()
    db.refresh(config)
    return config


def get_all_params(db: Session) -> dict[str, str]:
    """전체 파라미터 조회."""
    configs = db.query(ScanConfig).all()
    result = {}
    for key, (default_val, _) in DEFAULT_PARAMS.items():
        result[key] = default_val
    for config in configs:
        result[config.key] = config.value
    return result


def record_signal_outcome(
    db: Session,
    *,
    stock_code: str,
    strategy_name: str,
    signal: str,
    entry_price: float,
    tp_price: float = 0,
    sl_price: float = 0,
    regime: str = "side",
    params_snapshot: dict | None = None,
) -> SignalOutcome:
    """시그널 결과 기록 (진입 시)."""
    outcome = SignalOutcome(
        stock_code=stock_code,
        strategy_name=strategy_name,
        signal=signal,
        entry_price=entry_price,
        tp_price=tp_price,
        sl_price=sl_price,
        outcome="open",
        regime=regime,
        params_snapshot=json.dumps(params_snapshot) if params_snapshot else None,
    )
    db.add(outcome)
    db.commit()
    db.refresh(outcome)
    return outcome


def close_signal_outcome(db: Session, outcome_id: int, exit_price: float) -> SignalOutcome | None:
    """시그널 결과 마감 (청산 시)."""
    outcome = db.query(SignalOutcome).filter_by(id=outcome_id).first()
    if not outcome:
        return None

    outcome.exit_price = exit_price
    outcome.pnl_pct = (exit_price - outcome.entry_price) / outcome.entry_price * 100
    outcome.outcome = "win" if outcome.pnl_pct > 0 else "loss"
    outcome.closed_at = datetime.now()
    db.commit()
    db.refresh(outcome)
    return outcome


def run_tuning(db: Session) -> dict:
    """signal_outcomes 기반 k_tp/k_sl 자동 보정.

    최근 완료된 시그널의 승률/평균 수익을 분석해서
    regime별 k_tp/k_sl을 조정.
    """
    min_samples = get_param_int(db, "tuning_min_samples")

    results = {}
    for regime in ["bull", "bear", "side"]:
        outcomes = (
            db.query(SignalOutcome).filter_by(regime=regime).filter(SignalOutcome.outcome.in_(["win", "loss"])).all()
        )

        if len(outcomes) < min_samples:
            results[regime] = {"status": "insufficient_data", "samples": len(outcomes)}
            continue

        wins = [o for o in outcomes if o.outcome == "win"]
        losses = [o for o in outcomes if o.outcome == "loss"]
        win_rate = len(wins) / len(outcomes) * 100

        avg_win_pct = sum(o.pnl_pct for o in wins) / len(wins) if wins else 0
        avg_loss_pct = sum(abs(o.pnl_pct) for o in losses) / len(losses) if losses else 0

        current_k_tp = get_param_float(db, f"k_tp_{regime}")
        current_k_sl = get_param_float(db, f"k_sl_{regime}")

        # 보정 로직:
        # 승률 낮으면 → SL 넓히기 (k_sl 증가), TP 좁히기 (k_tp 감소)
        # 승률 높으면 → TP 넓히기, SL 좁히기
        adjustment = 0.0
        if win_rate < 40:
            adjustment = -0.2  # TP 줄이고 SL 늘리기
        elif win_rate > 60:
            adjustment = 0.2  # TP 늘리고 SL 줄이기

        new_k_tp = max(1.0, round(current_k_tp + adjustment, 1))
        new_k_sl = max(1.0, round(current_k_sl - adjustment * 0.5, 1))

        results[regime] = {
            "status": "tuned",
            "samples": len(outcomes),
            "win_rate": round(win_rate, 1),
            "avg_win_pct": round(avg_win_pct, 2),
            "avg_loss_pct": round(avg_loss_pct, 2),
            "k_tp": {"before": current_k_tp, "after": new_k_tp},
            "k_sl": {"before": current_k_sl, "after": new_k_sl},
        }

        # 제안만 반환, 실제 적용은 수동 승인 후
        logger.info(
            "Tuning %s: win_rate=%.1f%%, k_tp %.1f→%.1f, k_sl %.1f→%.1f",
            regime,
            win_rate,
            current_k_tp,
            new_k_tp,
            current_k_sl,
            new_k_sl,
        )

    set_param(db, "tuning_last_run", datetime.now().isoformat())
    return results
