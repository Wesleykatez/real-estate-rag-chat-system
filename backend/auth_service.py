"""
Authentication Service for Real Estate RAG Chat System
Handles user authentication, JWT tokens, password security, and session management
"""

import os
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from email_validator import validate_email, EmailNotValidError
from models import User, Role, Permission, UserSession, PasswordReset, AuditLog
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength and return requirements"""
        errors = []
        requirements = {
            "min_length": 8,
            "has_uppercase": False,
            "has_lowercase": False,
            "has_digit": False,
            "has_special": False
        }
        
        if len(password) < requirements["min_length"]:
            errors.append(f"Password must be at least {requirements['min_length']} characters long")
        
        if any(c.isupper() for c in password):
            requirements["has_uppercase"] = True
        else:
            errors.append("Password must contain at least one uppercase letter")
            
        if any(c.islower() for c in password):
            requirements["has_lowercase"] = True
        else:
            errors.append("Password must contain at least one lowercase letter")
            
        if any(c.isdigit() for c in password):
            requirements["has_digit"] = True
        else:
            errors.append("Password must contain at least one number")
            
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if any(c in special_chars for c in password):
            requirements["has_special"] = True
        else:
            errors.append("Password must contain at least one special character")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "requirements": requirements
        }
    
    def validate_email_format(self, email: str) -> bool:
        """Validate email format"""
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
    
    def generate_tokens(self, user_id: int, device_info: Dict = None) -> Dict[str, Any]:
        """Generate access and refresh tokens"""
        # Generate access token
        access_payload = {
            "user_id": user_id,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
            "iat": datetime.utcnow()
        }
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        
        # Generate refresh token
        refresh_payload = {
            "user_id": user_id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(32)  # JWT ID for token revocation
        }
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        # Store session in database
        session = UserSession(
            user_id=user_id,
            session_token=access_token,
            refresh_token=refresh_token,
            device_info=device_info or {},
            expires_at=datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        )
        self.db.add(session)
        self.db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "expires_at": access_payload["exp"].isoformat()
        }
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # Check if token exists in database for access tokens
            if token_type == "access":
                session = self.db.query(UserSession).filter(
                    and_(
                        UserSession.session_token == token,
                        UserSession.is_active == True,
                        UserSession.expires_at > datetime.utcnow()
                    )
                ).first()
                
                if not session:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token not found or expired"
                    )
                
                # Update last accessed time
                session.last_accessed = datetime.utcnow()
                self.db.commit()
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def refresh_token(self, refresh_token: str, device_info: Dict = None) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        payload = self.verify_token(refresh_token, "refresh")
        user_id = payload["user_id"]
        
        # Check if refresh token exists and is valid
        session = self.db.query(UserSession).filter(
            and_(
                UserSession.refresh_token == refresh_token,
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or expired"
            )
        
        # Deactivate old session
        session.is_active = False
        self.db.commit()
        
        # Generate new tokens
        return self.generate_tokens(user_id, device_info)
    
    def register_user(self, user_data: Dict[str, Any], role_name: str = "client") -> Dict[str, Any]:
        """Register a new user"""
        # Validate email format
        if not self.validate_email_format(user_data["email"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Validate password strength
        password_validation = self.validate_password_strength(user_data["password"])
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet requirements",
                    "errors": password_validation["errors"]
                }
            )
        
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            or_(
                User.email == user_data["email"],
                User.username == user_data.get("username", user_data["email"])
            )
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )
        
        # Get role
        role = self.db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{role_name}' not found"
            )
        
        # Create user
        hashed_password = self.hash_password(user_data["password"])
        user = User(
            email=user_data["email"],
            username=user_data.get("username", user_data["email"]),
            password_hash=hashed_password,
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            phone=user_data.get("phone"),
            company=user_data.get("company"),
            job_title=user_data.get("job_title"),
            license_number=user_data.get("license_number"),
            bio=user_data.get("bio"),
            preferences=user_data.get("preferences", {})
        )
        
        user.roles.append(role)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Log registration
        self.log_audit_event(
            user_id=user.id,
            action="user_registered",
            details={"role": role_name}
        )
        
        return {
            "user_id": user.id,
            "uuid": user.uuid,
            "email": user.email,
            "username": user.username,
            "full_name": f"{user.first_name} {user.last_name}",
            "roles": [role.name for role in user.roles]
        }
    
    def authenticate_user(self, email: str, password: str, device_info: Dict = None) -> Dict[str, Any]:
        """Authenticate user and return tokens"""
        # Find user
        user = self.db.query(User).filter(
            and_(
                or_(User.email == email, User.username == email),
                User.is_active == True
            )
        ).first()
        
        if not user or not self.verify_password(password, user.password_hash):
            # Log failed login attempt
            self.log_audit_event(
                action="login_failed",
                details={"email": email, "reason": "invalid_credentials"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Generate tokens
        tokens = self.generate_tokens(user.id, device_info)
        
        # Log successful login
        self.log_audit_event(
            user_id=user.id,
            action="login_success",
            details={"device_info": device_info}
        )
        
        return {
            "user": {
                "id": user.id,
                "uuid": user.uuid,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "roles": [role.name for role in user.roles],
                "permissions": self.get_user_permissions(user.id),
                "avatar_url": user.avatar_url,
                "company": user.company,
                "job_title": user.job_title
            },
            "tokens": tokens
        }
    
    def logout_user(self, access_token: str) -> bool:
        """Logout user by deactivating session"""
        payload = self.verify_token(access_token)
        user_id = payload["user_id"]
        
        # Deactivate session
        session = self.db.query(UserSession).filter(
            and_(
                UserSession.session_token == access_token,
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()
            
            # Log logout
            self.log_audit_event(
                user_id=user_id,
                action="logout",
                details={}
            )
            
            return True
        
        return False
    
    def get_current_user(self, access_token: str) -> User:
        """Get current user from access token"""
        payload = self.verify_token(access_token)
        user_id = payload["user_id"]
        
        user = self.db.query(User).filter(
            and_(User.id == user_id, User.is_active == True)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get all permissions for a user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        permissions = set()
        for role in user.roles:
            for permission in role.permissions:
                permissions.add(f"{permission.action}_{permission.resource}")
        
        return list(permissions)
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has specific permission"""
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions
    
    def create_password_reset_token(self, email: str) -> str:
        """Create password reset token"""
        user = self.db.query(User).filter(
            and_(User.email == email, User.is_active == True)
        ).first()
        
        if not user:
            # Don't reveal if email exists
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="If an account with this email exists, a password reset link has been sent"
            )
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        
        # Store reset token
        password_reset = PasswordReset(
            user_id=user.id,
            reset_token=reset_token,
            expires_at=expires_at
        )
        self.db.add(password_reset)
        self.db.commit()
        
        # Log password reset request
        self.log_audit_event(
            user_id=user.id,
            action="password_reset_requested",
            details={}
        )
        
        return reset_token
    
    def reset_password(self, reset_token: str, new_password: str) -> bool:
        """Reset password using reset token"""
        # Validate new password
        password_validation = self.validate_password_strength(new_password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet requirements",
                    "errors": password_validation["errors"]
                }
            )
        
        # Find valid reset token
        password_reset = self.db.query(PasswordReset).filter(
            and_(
                PasswordReset.reset_token == reset_token,
                PasswordReset.used == False,
                PasswordReset.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not password_reset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Update user password
        user = self.db.query(User).filter(User.id == password_reset.user_id).first()
        user.password_hash = self.hash_password(new_password)
        
        # Mark reset token as used
        password_reset.used = True
        
        # Deactivate all user sessions
        self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user.id,
                UserSession.is_active == True
            )
        ).update({"is_active": False})
        
        self.db.commit()
        
        # Log password reset
        self.log_audit_event(
            user_id=user.id,
            action="password_reset_completed",
            details={}
        )
        
        return True
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not self.verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        password_validation = self.validate_password_strength(new_password)
        if not password_validation["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet requirements",
                    "errors": password_validation["errors"]
                }
            )
        
        # Update password
        user.password_hash = self.hash_password(new_password)
        self.db.commit()
        
        # Log password change
        self.log_audit_event(
            user_id=user.id,
            action="password_changed",
            details={}
        )
        
        return True
    
    def deactivate_user(self, user_id: int, admin_user_id: int) -> bool:
        """Deactivate user account"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_active = False
        
        # Deactivate all user sessions
        self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).update({"is_active": False})
        
        self.db.commit()
        
        # Log deactivation
        self.log_audit_event(
            user_id=admin_user_id,
            action="user_deactivated",
            details={"deactivated_user_id": user_id}
        )
        
        return True
    
    def log_audit_event(self, action: str, user_id: int = None, details: Dict = None, ip_address: str = None, user_agent: str = None):
        """Log audit event"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(audit_log)
        self.db.commit()
    
    def get_user_sessions(self, user_id: int) -> List[Dict]:
        """Get all active sessions for a user"""
        sessions = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).all()
        
        return [
            {
                "id": session.id,
                "device_info": session.device_info,
                "ip_address": session.ip_address,
                "created_at": session.created_at.isoformat(),
                "last_accessed": session.last_accessed.isoformat(),
                "expires_at": session.expires_at.isoformat()
            }
            for session in sessions
        ]
    
    def revoke_session(self, session_id: int, user_id: int) -> bool:
        """Revoke a specific user session"""
        session = self.db.query(UserSession).filter(
            and_(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()
            
            # Log session revocation
            self.log_audit_event(
                user_id=user_id,
                action="session_revoked",
                details={"session_id": session_id}
            )
            
            return True
        
        return False
    
    def revoke_all_sessions(self, user_id: int, except_current: str = None) -> int:
        """Revoke all user sessions except optionally the current one"""
        query = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        )
        
        if except_current:
            query = query.filter(UserSession.session_token != except_current)
        
        sessions = query.all()
        count = len(sessions)
        
        for session in sessions:
            session.is_active = False
        
        self.db.commit()
        
        # Log session revocation
        self.log_audit_event(
            user_id=user_id,
            action="all_sessions_revoked",
            details={"revoked_count": count, "except_current": except_current is not None}
        )
        
        return count