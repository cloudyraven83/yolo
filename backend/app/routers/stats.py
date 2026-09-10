from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.security import get_current_admin
from ..models import AdminUser
from ..services import stats_service

router = APIRouter(prefix="/api/stats", tags=["stats"],
                   dependencies=[Depends(get_current_admin)])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    return stats_service.overview(db)


@router.get("/trend")
def trend(days: int = 7, db: Session = Depends(get_db)):
    return stats_service.trend(db, days)


@router.get("/category")
def category(db: Session = Depends(get_db)):
    return stats_service.category(db)
