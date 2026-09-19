import math
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def paginate(db: Session, stmt: Select[Any], page: int, page_size: int) -> tuple[list[Any], int, int]:
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = list(db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all())
    return items, total, math.ceil(total / page_size) if total else 0


def commit_or_conflict(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, message) from exc
