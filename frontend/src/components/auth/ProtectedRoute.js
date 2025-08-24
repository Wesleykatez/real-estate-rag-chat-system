/**
 * Protected Route Component for Real Estate RAG Chat System
 * Handles route protection based on authentication and permissions
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const ProtectedRoute = ({ 
  children, 
  requireAuth = true,
  requiredRoles = [],
  requiredPermissions = [],
  redirectTo = '/login',
  fallback = null
}) => {
  const { isAuthenticated, isLoading, user, hasRole, hasPermission, hasAnyRole } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="route-loading">
        <div className="loading-spinner-large">
          <div className="spinner"></div>
          <p>Checking authentication...</p>
        </div>
      </div>
    );
  }

  // If authentication is required but user is not authenticated
  if (requireAuth && !isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // If user is authenticated but shouldn't be (e.g., login page when already logged in)
  if (!requireAuth && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  // Check role requirements
  if (requiredRoles.length > 0) {
    const hasRequiredRole = hasAnyRole(requiredRoles);
    if (!hasRequiredRole) {
      if (fallback) {
        return fallback;
      }
      return (
        <div className="access-denied">
          <div className="access-denied-content">
            <span className="access-denied-icon">🚫</span>
            <h2>Access Denied</h2>
            <p>You don't have permission to access this page.</p>
            <p>Required roles: {requiredRoles.join(', ')}</p>
            <p>Your roles: {user?.roles?.join(', ') || 'None'}</p>
            <button 
              onClick={() => window.history.back()}
              className="back-button"
            >
              Go Back
            </button>
          </div>
        </div>
      );
    }
  }

  // Check permission requirements
  if (requiredPermissions.length > 0) {
    const hasAllPermissions = requiredPermissions.every(permission => 
      hasPermission(permission)
    );
    
    if (!hasAllPermissions) {
      if (fallback) {
        return fallback;
      }
      return (
        <div className="access-denied">
          <div className="access-denied-content">
            <span className="access-denied-icon">🔒</span>
            <h2>Insufficient Permissions</h2>
            <p>You don't have the required permissions to access this page.</p>
            <p>Required permissions: {requiredPermissions.join(', ')}</p>
            <button 
              onClick={() => window.history.back()}
              className="back-button"
            >
              Go Back
            </button>
          </div>
        </div>
      );
    }
  }

  // All checks passed, render the protected content
  return children;
};

// Convenience components for common protection scenarios
export const AdminRoute = ({ children, ...props }) => (
  <ProtectedRoute requiredRoles={['admin']} {...props}>
    {children}
  </ProtectedRoute>
);

export const AgentRoute = ({ children, ...props }) => (
  <ProtectedRoute requiredRoles={['agent', 'admin']} {...props}>
    {children}
  </ProtectedRoute>
);

export const EmployeeRoute = ({ children, ...props }) => (
  <ProtectedRoute requiredRoles={['employee', 'admin']} {...props}>
    {children}
  </ProtectedRoute>
);

export const ClientRoute = ({ children, ...props }) => (
  <ProtectedRoute requiredRoles={['client', 'agent', 'employee', 'admin']} {...props}>
    {children}
  </ProtectedRoute>
);

export const PublicRoute = ({ children, ...props }) => (
  <ProtectedRoute requireAuth={false} {...props}>
    {children}
  </ProtectedRoute>
);

export default ProtectedRoute;