/**
 * Login Form Component for Real Estate RAG Chat System
 * Provides user authentication with validation and error handling
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import './AuthForms.css';

const LoginForm = () => {
  const { login, isLoading, error, clearError, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });

  const [formErrors, setFormErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  // Clear errors when component mounts
  useEffect(() => {
    clearError();
  }, [clearError]);

  const validateForm = () => {
    const errors = {};

    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Clear specific field error when user starts typing
    if (formErrors[name]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }

    // Clear general error
    if (error) {
      clearError();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const result = await login(formData.email, formData.password, formData.rememberMe);

    if (result.success) {
      // Redirect will be handled by useEffect
    }
  };

  const handleDemoLogin = async (role) => {
    const demoCredentials = {
      client: { email: 'demo.client@example.com', password: 'demo123' },
      agent: { email: 'demo.agent@example.com', password: 'demo123' },
      employee: { email: 'demo.employee@example.com', password: 'demo123' },
      admin: { email: 'demo.admin@example.com', password: 'demo123' }
    };

    const creds = demoCredentials[role];
    if (creds) {
      setFormData({ ...creds, rememberMe: false });
      await login(creds.email, creds.password, false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">
            <span className="logo-icon">🏠</span>
            <h1>Real Estate AI</h1>
          </div>
          <h2>Welcome Back</h2>
          <p>Sign in to access your real estate dashboard</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <span>{typeof error === 'string' ? error : 'Login failed. Please try again.'}</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <div className="input-wrapper">
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={formErrors.email ? 'error' : ''}
                placeholder="Enter your email"
                disabled={isLoading}
                autoComplete="email"
              />
              <span className="input-icon">📧</span>
            </div>
            {formErrors.email && (
              <span className="field-error">{formErrors.email}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={formErrors.password ? 'error' : ''}
                placeholder="Enter your password"
                disabled={isLoading}
                autoComplete="current-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isLoading}
              >
                {showPassword ? '👁️' : '🙈'}
              </button>
            </div>
            {formErrors.password && (
              <span className="field-error">{formErrors.password}</span>
            )}
          </div>

          <div className="form-row">
            <label className="checkbox-label">
              <input
                type="checkbox"
                name="rememberMe"
                checked={formData.rememberMe}
                onChange={handleChange}
                disabled={isLoading}
              />
              <span className="checkbox-custom"></span>
              Remember me
            </label>

            <Link to="/forgot-password" className="forgot-password">
              Forgot password?
            </Link>
          </div>

          <button
            type="submit"
            className="auth-button primary"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="loading-spinner"></span>
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>

          <div className="auth-divider">
            <span>or</span>
          </div>

          <div className="demo-logins">
            <p className="demo-title">Try Demo Accounts:</p>
            <div className="demo-buttons">
              <button
                type="button"
                className="demo-button client"
                onClick={() => handleDemoLogin('client')}
                disabled={isLoading}
              >
                👤 Client Demo
              </button>
              <button
                type="button"
                className="demo-button agent"
                onClick={() => handleDemoLogin('agent')}
                disabled={isLoading}
              >
                🏠 Agent Demo
              </button>
              <button
                type="button"
                className="demo-button employee"
                onClick={() => handleDemoLogin('employee')}
                disabled={isLoading}
              >
                👨‍💼 Employee Demo
              </button>
              <button
                type="button"
                className="demo-button admin"
                onClick={() => handleDemoLogin('admin')}
                disabled={isLoading}
              >
                ⚙️ Admin Demo
              </button>
            </div>
          </div>

          <div className="auth-footer">
            <p>
              Don't have an account?{' '}
              <Link to="/register" className="auth-link">
                Sign up here
              </Link>
            </p>
          </div>
        </form>
      </div>

      <div className="auth-features">
        <h3>Why Choose Our Platform?</h3>
        <div className="feature-list">
          <div className="feature-item">
            <span className="feature-icon">🤖</span>
            <div>
              <h4>AI-Powered Chat</h4>
              <p>Get instant, intelligent responses to your real estate questions</p>
            </div>
          </div>
          <div className="feature-item">
            <span className="feature-icon">📊</span>
            <div>
              <h4>Market Intelligence</h4>
              <p>Access comprehensive Dubai real estate market data and trends</p>
            </div>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🔒</span>
            <div>
              <h4>Secure & Private</h4>
              <p>Your data is protected with enterprise-grade security</p>
            </div>
          </div>
          <div className="feature-item">
            <span className="feature-icon">📱</span>
            <div>
              <h4>Multi-Device Access</h4>
              <p>Access your dashboard from anywhere, on any device</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;