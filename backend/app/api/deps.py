"""
Shared dependencies every module (this one and every future module --
Projects, Sprints, Kanban, Bugs, Reports, AI...) imports to enforce
authentication and RBAC on the BACKEND, never trusting the frontend alone.

Usage in a future module:

    from app.api.deps import get_current_user, require_role
    from app.models.role import RoleEnum

    @router.post("/projects")
    def create_project(user: User = Depends(require_role(RoleEnum.PRODUCT_OWNER, RoleEnum.OWNER_ADMIN))):
        ...
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.role import RoleEnum
from app.models.user import User

# tokenUrl is documentation-only (points Swagger UI at the login route)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise credentials_exception

    return user


def require_password_already_set(user: User = Depends(get_current_user)) -> User:
    """Blocks normal endpoints until the forced first-login password change
    is complete (spec §11) -- only the change-password endpoint itself
    should be reachable while this flag is true."""
    if user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password change required before continuing.",
        )
    return user


def get_db_and_user(
    db: Session = Depends(get_db), user: User = Depends(require_password_already_set)
) -> tuple[Session, User]:
    """Convenience bundle for services that need both in one dependency."""
    return db, user


def is_admin(user: User) -> bool:
    return user.role == RoleEnum.OWNER_ADMIN


def require_role(*allowed_roles: RoleEnum):
    """Dependency factory for RBAC. Every protected route across every
    module should use this rather than relying on the frontend hiding UI."""

    def dependency(user: User = Depends(require_password_already_set)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return user

    return dependency
