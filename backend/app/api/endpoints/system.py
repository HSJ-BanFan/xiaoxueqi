from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/healthz")
def healthz() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/readyz")
def readyz(db: Session = Depends(get_db)) -> Dict[str, Any]:
    db_ok = False
    db_error = None
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # pragma: no cover - surfaced in response
        db_error = str(exc)

    status = "ok" if db_ok else "degraded"
    body: Dict[str, Any] = {
        "status": status,
        "checks": {
            "database": {"ok": db_ok, "error": db_error},
            "agent": {"enabled": settings.AGENT_ENABLED, "model": settings.LLM_MODEL},
        },
    }
    return body
