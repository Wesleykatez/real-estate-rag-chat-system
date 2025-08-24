"""
Authentication Middleware for Real Estate RAG Chat System
Provides JWT validation, permission checking, and security features
"""

import os
import time
from typing import Optional, List, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from collections import defaultdict
from datetime import datetime, timedelta
import ipaddress
import logging

from auth_service import AuthService
from models import User, AuditLog
from database import get_db

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
rate_limit_storage = defaultdict(list)

class SecurityHeaders:
    """Security headers middleware"""
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://api.openai.com https://generativelanguage.googleapis.com"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
    
    def is_allowed(self, identifier: str, endpoint: str) -> bool:
        """Check if request is allowed based on rate limits"""
        now = time.time()
        key = f"{identifier}:{endpoint}"
        
        # Clean old entries
        rate_limit_storage[key] = [
            timestamp for timestamp in rate_limit_storage[key]
            if now - timestamp < 3600  # Keep last hour
        ]
        
        # Check minute limit
        minute_ago = now - 60
        minute_requests = len([
            timestamp for timestamp in rate_limit_storage[key]
            if timestamp > minute_ago
        ])
        
        # Check hour limit
        hour_requests = len(rate_limit_storage[key])
        
        if minute_requests >= self.requests_per_minute or hour_requests >= self.requests_per_hour:
            return False
        
        # Add current request
        rate_limit_storage[key].append(now)
        return True
    
    def get_limits_info(self, identifier: str, endpoint: str) -> Dict[str, int]:
        """Get current rate limit status"""
        now = time.time()
        key = f"{identifier}:{endpoint}"
        
        # Clean old entries
        rate_limit_storage[key] = [
            timestamp for timestamp in rate_limit_storage[key]
            if now - timestamp < 3600
        ]
        
        minute_ago = now - 60
        minute_requests = len([
            timestamp for timestamp in rate_limit_storage[key]
            if timestamp > minute_ago
        ])
        hour_requests = len(rate_limit_storage[key])
        
        return {
            "requests_this_minute": minute_requests,
            "requests_this_hour": hour_requests,
            "minute_limit": self.requests_per_minute,
            "hour_limit": self.requests_per_hour,
            "minute_remaining": max(0, self.requests_per_minute - minute_requests),
            "hour_remaining": max(0, self.requests_per_hour - hour_requests)
        }

class AuthMiddleware:
    """Authentication and authorization middleware"""
    
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
        self.rate_limiter = RateLimiter()
        
        # IP whitelist for admin endpoints (in production, use proper IP ranges)
        self.admin_ip_whitelist = [
            "127.0.0.1",
            "::1",
            # Add your admin IPs here
        ]
        
        # Endpoints that don't require authentication
        self.public_endpoints = {
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/auth/register",
            "/auth/login",
            "/auth/forgot-password",
            "/auth/reset-password"
        }
        
        # Endpoints with special rate limits
        self.auth_endpoints = {
            "/auth/login",
            "/auth/register",
            "/auth/forgot-password",
            "/auth/reset-password"
        }
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host
    
    def is_admin_ip(self, ip: str) -> bool:
        """Check if IP is in admin whitelist"""
        try:
            client_ip = ipaddress.ip_address(ip)
            for allowed_ip in self.admin_ip_whitelist:
                if ipaddress.ip_address(allowed_ip) == client_ip:
                    return True
            return False
        except ValueError:
            return False
    
    async def __call__(self, request: Request, call_next):
        """Main middleware function"""
        start_time = time.time()
        client_ip = self.get_client_ip(request)
        path = request.url.path
        method = request.method
        
        # Add client IP to request state
        request.state.client_ip = client_ip
        
        try:
            # Apply rate limiting
            await self.apply_rate_limiting(request, client_ip, path)
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response = SecurityHeaders.add_security_headers(response)
            
            # Log request
            processing_time = time.time() - start_time
            logger.info(
                f"{method} {path} - {response.status_code} - "
                f"{processing_time:.3f}s - {client_ip}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Middleware error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
    
    async def apply_rate_limiting(self, request: Request, client_ip: str, path: str):
        """Apply rate limiting based on endpoint and IP"""
        # Strict rate limiting for auth endpoints
        if path in self.auth_endpoints:
            if not self.rate_limiter.is_allowed(client_ip, "auth"):
                rate_info = self.rate_limiter.get_limits_info(client_ip, "auth")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "message": "Too many authentication attempts",
                        "rate_limit_info": rate_info
                    }
                )
        
        # General rate limiting
        elif not self.rate_limiter.is_allowed(client_ip, "general"):
            rate_info = self.rate_limiter.get_limits_info(client_ip, "general")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Rate limit exceeded",
                    "rate_limit_info": rate_info
                }
            )

# Dependency injection functions
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
    request: Request = None
) -> User:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    auth_service = AuthService(db)
    
    try:
        # Get user from token
        user = auth_service.get_current_user(credentials.credentials)
        
        # Add user info to request state for logging
        if request:
            request.state.user = user
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication"
        )

def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None"""
    if not credentials:
        return None
    
    try:
        auth_service = AuthService(db)
        return auth_service.get_current_user(credentials.credentials)
    except:
        return None

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        auth_service = AuthService(db)
        if not auth_service.has_permission(current_user.id, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return permission_checker

def require_role(role_name: str):
    """Decorator to require specific role"""
    def role_checker(current_user: User = Depends(get_current_user)):
        user_roles = [role.name for role in current_user.roles]
        if role_name not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required"
            )
        return current_user
    
    return role_checker

def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin role"""
    return require_role("admin")(current_user)

def require_agent_or_admin(current_user: User = Depends(get_current_user)):
    """Require agent or admin role"""
    user_roles = [role.name for role in current_user.roles]
    if "agent" not in user_roles and "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent or Admin role required"
        )
    return current_user

def admin_ip_required(request: Request):
    """Require admin IP for sensitive endpoints"""
    middleware = AuthMiddleware()
    client_ip = middleware.get_client_ip(request)
    
    if not middleware.is_admin_ip(client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied from this IP address"
        )
    
    return True

class PermissionChecker:
    """Helper class for checking permissions"""
    
    @staticmethod
    def can_read_properties(user: User) -> bool:
        """Check if user can read properties"""
        user_roles = [role.name for role in user.roles]
        return any(role in ["client", "agent", "employee", "admin"] for role in user_roles)
    
    @staticmethod
    def can_create_properties(user: User) -> bool:
        """Check if user can create properties"""
        user_roles = [role.name for role in user.roles]
        return any(role in ["agent", "admin"] for role in user_roles)
    
    @staticmethod
    def can_edit_properties(user: User, property_agent_id: int = None) -> bool:
        """Check if user can edit properties"""
        user_roles = [role.name for role in user.roles]
        
        # Admin can edit all
        if "admin" in user_roles:
            return True
        
        # Agent can edit their own properties
        if "agent" in user_roles:
            return property_agent_id is None or property_agent_id == user.id
        
        return False
    
    @staticmethod
    def can_delete_properties(user: User, property_agent_id: int = None) -> bool:
        """Check if user can delete properties"""
        user_roles = [role.name for role in user.roles]
        
        # Admin can delete all
        if "admin" in user_roles:
            return True
        
        # Agent can delete their own properties
        if "agent" in user_roles:
            return property_agent_id is None or property_agent_id == user.id
        
        return False
    
    @staticmethod
    def can_manage_clients(user: User, client_agent_id: int = None) -> bool:
        """Check if user can manage clients"""
        user_roles = [role.name for role in user.roles]
        
        # Admin can manage all
        if "admin" in user_roles:
            return True
        
        # Agent can manage their own clients
        if "agent" in user_roles:
            return client_agent_id is None or client_agent_id == user.id
        
        return False
    
    @staticmethod
    def can_view_analytics(user: User) -> bool:
        """Check if user can view analytics"""
        user_roles = [role.name for role in user.roles]
        return any(role in ["agent", "employee", "admin"] for role in user_roles)
    
    @staticmethod
    def can_manage_users(user: User) -> bool:
        """Check if user can manage other users"""
        user_roles = [role.name for role in user.roles]
        return "admin" in user_roles

# CSRF Protection
class CSRFProtection:
    """CSRF protection for state-changing operations"""
    
    def __init__(self):
        self.secret = os.getenv("CSRF_SECRET", "change-in-production")
    
    def generate_token(self, user_id: int) -> str:
        """Generate CSRF token"""
        import hmac
        import hashlib
        timestamp = str(int(time.time()))
        message = f"{user_id}:{timestamp}"
        signature = hmac.new(
            self.secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{timestamp}.{signature}"
    
    def validate_token(self, token: str, user_id: int, max_age: int = 3600) -> bool:
        """Validate CSRF token"""
        try:
            import hmac
            import hashlib
            
            timestamp_str, signature = token.split(".", 1)
            timestamp = int(timestamp_str)
            
            # Check age
            if time.time() - timestamp > max_age:
                return False
            
            # Verify signature
            message = f"{user_id}:{timestamp_str}"
            expected_signature = hmac.new(
                self.secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError):
            return False

# Initialize CSRF protection
csrf_protection = CSRFProtection()

def require_csrf_token(
    csrf_token: str,
    current_user: User = Depends(get_current_user)
) -> bool:
    """Require valid CSRF token"""
    if not csrf_protection.validate_token(csrf_token, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired CSRF token"
        )
    return True

# Security utilities
class SecurityUtils:
    """Security utility functions"""
    
    @staticmethod
    def is_safe_redirect_url(url: str, allowed_hosts: List[str]) -> bool:
        """Check if redirect URL is safe"""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            if not parsed.netloc:  # Relative URL
                return True
            return parsed.netloc in allowed_hosts
        except:
            return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for security"""
        import re
        # Remove path traversal attempts
        filename = filename.replace("../", "").replace("..\\", "")
        # Remove special characters except dots, hyphens, and underscores
        filename = re.sub(r'[^a-zA-Z0-9.\-_]', '', filename)
        # Limit length
        filename = filename[:255]
        return filename
    
    @staticmethod
    def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
        """Validate file type by extension"""
        if not filename:
            return False
        
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        return extension in allowed_types
    
    @staticmethod
    def get_file_hash(file_content: bytes) -> str:
        """Get SHA256 hash of file content"""
        import hashlib
        return hashlib.sha256(file_content).hexdigest()