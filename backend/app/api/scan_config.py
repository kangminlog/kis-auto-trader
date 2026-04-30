from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.scan_config_service import (
    get_all_params,
    init_default_params,
    run_tuning,
    set_param,
)

router = APIRouter(prefix="/api/scan-config", tags=["scan-config"], dependencies=[Depends(get_current_user)])


@router.get("/params")
def list_params(db: Session = Depends(get_db)):
    return get_all_params(db)


@router.post("/init")
def init_params(db: Session = Depends(get_db)):
    created = init_default_params(db)
    return {"created": created}


class SetParamRequest(BaseModel):
    key: str
    value: str


@router.patch("/params")
def update_param(req: SetParamRequest, db: Session = Depends(get_db)):
    config = set_param(db, req.key, req.value)
    return {"key": config.key, "value": config.value}


class ApplyTuningRequest(BaseModel):
    regime: str
    k_tp: float
    k_sl: float


@router.post("/tuning/run")
def tuning_run(db: Session = Depends(get_db)):
    """튜닝 실행. 제안값만 반환, 실제 적용은 /tuning/apply."""
    return run_tuning(db)


@router.post("/tuning/apply")
def tuning_apply(req: ApplyTuningRequest, db: Session = Depends(get_db)):
    """튜닝 제안 수동 승인 적용."""
    set_param(db, f"k_tp_{req.regime}", str(req.k_tp))
    set_param(db, f"k_sl_{req.regime}", str(req.k_sl))
    return {"applied": True, "regime": req.regime, "k_tp": req.k_tp, "k_sl": req.k_sl}
