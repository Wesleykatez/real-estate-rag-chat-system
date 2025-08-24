"""
Authentication Routes for Real Estate RAG Chat System
Provides registration, login, password reset, and user management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from database import get_db
from auth_service import AuthService
from auth_middleware import (
    get_current_user, require_admin, require_permission, 
    csrf_protection, SecurityUtils, RateLimiter
)
from models import User, Role, UserSession, AuditLog

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# Pydantic models for request/response
class UserRegistration(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: str = "client"
    company: Optional[str] = None
    job_title: Optional[str] = None
    license_number: Optional[str] = None
    bio: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ['client', 'agent', 'employee', 'admin']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v

class UserLogin(BaseModel):
    email: str
    password: str
    remember_me: bool = False
    device_info: Optional[Dict[str, Any]] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    reset_token: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    license_number: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    id: int
    uuid: str
    email: str
    username: str
    first_name: str
    last_name: str
    phone: Optional[str]
    company: Optional[str]
    job_title: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    roles: List[str]
    permissions: List[str]
    created_at: datetime
    last_login: Optional[datetime]

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    expires_at: str

class LoginResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse
    csrf_token: str

class SessionResponse(BaseModel):
    id: int
    device_info: Dict[str, Any]
    ip_address: Optional[str]
    created_at: str
    last_accessed: str
    expires_at: str

# Helper functions
def get_client_info(request: Request) -> Dict[str, Any]:
    """Extract client information from request"""
    return {
        "ip_address": getattr(request.state, 'client_ip', request.client.host),
        "user_agent": request.headers.get("User-Agent", ""),
        "device_info": {
            "user_agent": request.headers.get("User-Agent", ""),
            "accept_language": request.headers.get("Accept-Language", ""),
            "referer": request.headers.get("Referer", "")
        }
    }

async def send_password_reset_email(email: str, reset_token: str):
    """Send password reset email (implement with your email service)"""
    # TODO: Implement email sending
    logger.info(f"Password reset email would be sent to {email} with token {reset_token}")

# Authentication endpoints
@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegistration,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    auth_service = AuthService(db)
    client_info = get_client_info(request)
    
    try:
        # Register user
        user_result = auth_service.register_user(
            user_data.dict(),
            user_data.role
        )
        
        # Log registration
        auth_service.log_audit_event(
            user_id=user_result["user_id"],
            action="user_registered",
            details={
                "role": user_data.role,
                "email": user_data.email
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        # TODO: Send welcome email
        # background_tasks.add_task(send_welcome_email, user_data.email)
        
        return {
            "message": "User registered successfully",
            "user": user_result,
            "next_steps": [
                "Please verify your email address",
                "Complete your profile",
                "Start exploring properties"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and return tokens"""
    auth_service = AuthService(db)
    client_info = get_client_info(request)
    
    try:
        # Authenticate user
        auth_result = auth_service.authenticate_user(
            credentials.email,
            credentials.password,
            client_info["device_info"]
        )
        
        # Generate CSRF token
        csrf_token = csrf_protection.generate_token(auth_result["user"]["id"])
        
        return LoginResponse(
            user=UserResponse(**auth_result["user"]),
            tokens=TokenResponse(**auth_result["tokens"]),
            csrf_token=csrf_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    auth_service = AuthService(db)
    client_info = get_client_info(request)
    
    try:
        tokens = auth_service.refresh_token(
            refresh_token,
            client_info["device_info"]
        )
        
        return TokenResponse(**tokens)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Logout user and invalidate session"""
    auth_service = AuthService(db)
    
    try:
        success = auth_service.logout_user(credentials.credentials)
        
        if success:
            return {"message": "Logged out successfully"}
        else:
            return {"message": "Already logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/forgot-password")
async def forgot_password(
    request_data: PasswordReset,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    auth_service = AuthService(db)
    client_info = get_client_info(request)
    
    try:
        reset_token = auth_service.create_password_reset_token(request_data.email)
        
        # Send reset email
        background_tasks.add_task(
            send_password_reset_email,
            request_data.email,
            reset_token
        )
        
        # Log password reset request
        auth_service.log_audit_event(
            action="password_reset_requested",
            details={"email": request_data.email},
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        return {
            "message": "If an account with this email exists, a password reset link has been sent"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    auth_service = AuthService(db)
    client_info = get_client_info(request)
    
    try:
        success = auth_service.reset_password(
            reset_data.reset_token,
            reset_data.new_password
        )
        
        if success:
            return {"message": "Password reset successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset failed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    auth_service = AuthService(db)
    
    try:
        success = auth_service.change_password(
            current_user.id,
            password_data.current_password,
            password_data.new_password
        )
        
        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

# User management endpoints
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    auth_service = AuthService(db)
    
    return UserResponse(
        id=current_user.id,
        uuid=current_user.uuid,
        email=current_user.email,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone=current_user.phone,
        company=current_user.company,
        job_title=current_user.job_title,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        roles=[role.name for role in current_user.roles],
        permissions=auth_service.get_user_permissions(current_user.id),
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.put("/me", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    auth_service = AuthService(db)
    
    try:
        # Update user fields
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        db.commit()
        db.refresh(current_user)
        
        # Log profile update
        auth_service.log_audit_event(
            user_id=current_user.id,
            action="profile_updated",
            details={"updated_fields": list(update_data.keys())}
        )
        
        return UserResponse(
            id=current_user.id,
            uuid=current_user.uuid,
            email=current_user.email,
            username=current_user.username,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            phone=current_user.phone,
            company=current_user.company,
            job_title=current_user.job_title,
            avatar_url=current_user.avatar_url,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            roles=[role.name for role in current_user.roles],
            permissions=auth_service.get_user_permissions(current_user.id),
            created_at=current_user.created_at,
            last_login=current_user.last_login
        )
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@router.get("/sessions", response_model=List[SessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active sessions for current user"""
    auth_service = AuthService(db)
    
    try:
        sessions = auth_service.get_user_sessions(current_user.id)
        return [SessionResponse(**session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a specific session"""
    auth_service = AuthService(db)
    
    try:
        success = auth_service.revoke_session(session_id, current_user.id)
        
        if success:
            return {"message": "Session revoked successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )

@router.delete("/sessions")
async def revoke_all_sessions(
    keep_current: bool = True,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Revoke all sessions (optionally keep current)"""
    auth_service = AuthService(db)
    
    try:
        current_token = credentials.credentials if keep_current else None
        count = auth_service.revoke_all_sessions(current_user.id, current_token)
        
        return {
            "message": f"Revoked {count} session(s)",
            "revoked_count": count
        }
        
    except Exception as e:
        logger.error(f"Revoke all sessions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke sessions"
        )

@router.get("/csrf-token")
async def get_csrf_token(current_user: User = Depends(get_current_user)):
    """Get CSRF token for current user"""
    csrf_token = csrf_protection.generate_token(current_user.id)
    return {"csrf_token": csrf_token}

# Admin endpoints
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    auth_service = AuthService(db)
    
    try:
        query = db.query(User)
        
        if role:
            query = query.join(User.roles).filter(Role.name == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        users = query.offset(skip).limit(limit).all()
        
        return [
            UserResponse(
                id=user.id,
                uuid=user.uuid,
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone,
                company=user.company,
                job_title=user.job_title,
                avatar_url=user.avatar_url,
                is_active=user.is_active,
                is_verified=user.is_verified,
                roles=[role.name for role in user.roles],
                permissions=auth_service.get_user_permissions(user.id),
                created_at=user.created_at,
                last_login=user.last_login
            )
            for user in users
        ]
        
    except Exception as e:
        logger.error(f"List users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate a user (admin only)"""
    auth_service = AuthService(db)
    
    try:
        success = auth_service.deactivate_user(user_id, current_user.id)
        
        if success:
            return {"message": "User deactivated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )

@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get audit logs (admin only)"""
    try:
        query = db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
        
        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ]
        
    except Exception as e:
        logger.error(f"Get audit logs error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )