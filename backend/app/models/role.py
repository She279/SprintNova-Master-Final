"""
Role definitions for RBAC.

Kept as a plain Python enum (not a DB table) so every other module can do:
    from app.models.role import RoleEnum
    @router.get(...)
    def handler(user: User = Depends(require_role(RoleEnum.OWNER_ADMIN))): ...

If richer, admin-editable roles/permissions are needed later, this enum can
be swapped for a `roles` table without changing the RBAC dependency's shape.
"""
import enum


class RoleEnum(str, enum.Enum):
    OWNER_ADMIN = "owner_admin"
    PRODUCT_OWNER = "product_owner"
    SCRUM_MASTER = "scrum_master"
    DEVELOPER = "developer"
    TESTER = "tester"
    CLIENT = "client"
    PROJECT_MANAGER = "project_manager"
    TEAM_LEAD = "team_lead"


# Roles allowed to create/manage employee accounts (Module 1)
ADMIN_ROLES = {RoleEnum.OWNER_ADMIN}
