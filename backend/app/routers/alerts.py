from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import RegressionAlert
from ..schemas import RegressionAlertOut

router = APIRouter(prefix="/regression-alerts", tags=["alerts"])


@router.get("", response_model=list[RegressionAlertOut])
def list_alerts(db: Session = Depends(get_db)):
    return (
        db.query(RegressionAlert)
        .order_by(RegressionAlert.flagged_at.desc())
        .limit(200)
        .all()
    )
