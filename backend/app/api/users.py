"""Rotas de consulta de usuarios."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.api.deps import CurrentUser
from app.core.database import get_db
from app.core.session_manager import SessionManager, get_session_manager
from app.models.user import User
from app.schemas.auth import UserProfile

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/online", response_model=list[UserProfile])
def online_users(
    current_user: CurrentUser,
    db: Annotated[DbSession, Depends(get_db)],
    manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> list[User]:
    """Usuarios com conexao WebSocket ativa, exceto o proprio (F14.3)."""
    online_ids = manager.online_user_ids() - {current_user.id}
    if not online_ids:
        return []
    return list(db.scalars(select(User).where(User.id.in_(online_ids))).all())
