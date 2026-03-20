"""Role-based permission helpers"""
from typing import List
from fastapi import HTTPException, status, Depends
from app.schemas.user import User, UserRole
from app.api.v1.endpoints.auth import get_current_user


def require_role(allowed_roles: List[UserRole]):
    """
    Dependency factory to require specific roles
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            current_user: User = Depends(require_role([UserRole.CLUSTER_ADMIN]))
        ):
            return {"message": "Admin access granted"}
    """
    async def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user
    
    return role_checker


# Convenience dependencies for common role checks
RequireClusterAdmin = Depends(require_role([UserRole.CLUSTER_ADMIN]))
RequireCompanyOwner = Depends(require_role([UserRole.COMPANY_OWNER]))
RequireUtilityProvider = Depends(require_role([UserRole.UTILITY_PROVIDER]))

# Combined role checks
RequireAdminOrOwner = Depends(require_role([UserRole.CLUSTER_ADMIN, UserRole.COMPANY_OWNER]))
RequireAnyRole = Depends(require_role([UserRole.CLUSTER_ADMIN, UserRole.COMPANY_OWNER, UserRole.UTILITY_PROVIDER]))
