/**
 * Authentication Context for Real Estate RAG Chat System
 * Manages user authentication state, login/logout, and permissions
 */

import React, { createContext, useContext, useReducer, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

// Initial state
const initialState = {
  user: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  permissions: [],
  roles: [],
  csrfToken: null
};

// Action types
const AUTH_ACTIONS = {
  LOGIN_START: 'LOGIN_START',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  LOGOUT: 'LOGOUT',
  REGISTER_START: 'REGISTER_START',
  REGISTER_SUCCESS: 'REGISTER_SUCCESS',
  REGISTER_FAILURE: 'REGISTER_FAILURE',
  REFRESH_TOKEN: 'REFRESH_TOKEN',
  UPDATE_PROFILE: 'UPDATE_PROFILE',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  SET_CSRF_TOKEN: 'SET_CSRF_TOKEN'
};

// Reducer
const authReducer = (state, action) => {
  switch (action.type) {
    case AUTH_ACTIONS.LOGIN_START:
    case AUTH_ACTIONS.REGISTER_START:
      return {
        ...state,
        isLoading: true,
        error: null
      };

    case AUTH_ACTIONS.LOGIN_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        tokens: action.payload.tokens,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        permissions: action.payload.user.permissions || [],
        roles: action.payload.user.roles || [],
        csrfToken: action.payload.csrf_token
      };

    case AUTH_ACTIONS.REGISTER_SUCCESS:
      return {
        ...state,
        isLoading: false,
        error: null
      };

    case AUTH_ACTIONS.LOGIN_FAILURE:
    case AUTH_ACTIONS.REGISTER_FAILURE:
      return {
        ...state,
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
        permissions: [],
        roles: [],
        csrfToken: null
      };

    case AUTH_ACTIONS.LOGOUT:
      return {
        ...initialState,
        isLoading: false
      };

    case AUTH_ACTIONS.REFRESH_TOKEN:
      return {
        ...state,
        tokens: action.payload
      };

    case AUTH_ACTIONS.UPDATE_PROFILE:
      return {
        ...state,
        user: { ...state.user, ...action.payload }
      };

    case AUTH_ACTIONS.SET_LOADING:
      return {
        ...state,
        isLoading: action.payload
      };

    case AUTH_ACTIONS.SET_ERROR:
      return {
        ...state,
        error: action.payload
      };

    case AUTH_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null
      };

    case AUTH_ACTIONS.SET_CSRF_TOKEN:
      return {
        ...state,
        csrfToken: action.payload
      };

    default:
      return state;
  }
};

// Create context
const AuthContext = createContext();

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// API client setup
const createApiClient = (tokens) => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Add auth header if tokens exist
  if (tokens?.access_token) {
    client.defaults.headers.common['Authorization'] = `Bearer ${tokens.access_token}`;
  }

  return client;
};

// Auth Provider Component
export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedTokens = localStorage.getItem('auth_tokens');
        const storedUser = localStorage.getItem('auth_user');

        if (storedTokens && storedUser) {
          const tokens = JSON.parse(storedTokens);
          const user = JSON.parse(storedUser);

          // Check if tokens are still valid
          if (tokens.expires_at && new Date(tokens.expires_at) > new Date()) {
            const apiClient = createApiClient(tokens);
            
            try {
              // Verify token by getting current user
              const response = await apiClient.get('/auth/me');
              
              dispatch({
                type: AUTH_ACTIONS.LOGIN_SUCCESS,
                payload: {
                  user: response.data,
                  tokens,
                  csrf_token: null
                }
              });

              // Get CSRF token
              const csrfResponse = await apiClient.get('/auth/csrf-token');
              dispatch({
                type: AUTH_ACTIONS.SET_CSRF_TOKEN,
                payload: csrfResponse.data.csrf_token
              });

            } catch (error) {
              // Token is invalid, clear storage
              localStorage.removeItem('auth_tokens');
              localStorage.removeItem('auth_user');
              dispatch({ type: AUTH_ACTIONS.LOGOUT });
            }
          } else {
            // Tokens expired, try to refresh
            await refreshTokens(tokens.refresh_token);
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
      }
    };

    initializeAuth();
  }, []);

  // Auto-refresh tokens before they expire
  useEffect(() => {
    if (state.tokens?.access_token && state.tokens?.expires_at) {
      const expiryTime = new Date(state.tokens.expires_at).getTime();
      const currentTime = new Date().getTime();
      const timeUntilExpiry = expiryTime - currentTime;
      
      // Refresh 5 minutes before expiry
      const refreshTime = Math.max(0, timeUntilExpiry - 5 * 60 * 1000);

      const timer = setTimeout(() => {
        refreshTokens(state.tokens.refresh_token);
      }, refreshTime);

      return () => clearTimeout(timer);
    }
  }, [state.tokens]);

  // API functions
  const login = async (email, password, rememberMe = false) => {
    dispatch({ type: AUTH_ACTIONS.LOGIN_START });

    try {
      const apiClient = createApiClient();
      const response = await apiClient.post('/auth/login', {
        email,
        password,
        remember_me: rememberMe,
        device_info: {
          user_agent: navigator.userAgent,
          platform: navigator.platform,
          language: navigator.language
        }
      });

      const { user, tokens, csrf_token } = response.data;

      // Store tokens and user in localStorage
      localStorage.setItem('auth_tokens', JSON.stringify(tokens));
      localStorage.setItem('auth_user', JSON.stringify(user));

      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: { user, tokens, csrf_token }
      });

      return { success: true, user };

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: errorMessage
      });
      return { success: false, error: errorMessage };
    }
  };

  const register = async (userData) => {
    dispatch({ type: AUTH_ACTIONS.REGISTER_START });

    try {
      const apiClient = createApiClient();
      const response = await apiClient.post('/auth/register', userData);

      dispatch({
        type: AUTH_ACTIONS.REGISTER_SUCCESS,
        payload: response.data
      });

      return { success: true, data: response.data };

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Registration failed';
      dispatch({
        type: AUTH_ACTIONS.REGISTER_FAILURE,
        payload: errorMessage
      });
      return { success: false, error: errorMessage };
    }
  };

  const logout = async () => {
    try {
      if (state.tokens?.access_token) {
        const apiClient = createApiClient(state.tokens);
        await apiClient.post('/auth/logout');
      }
    } catch (error) {
      console.error('Logout API error:', error);
    } finally {
      // Clear local storage
      localStorage.removeItem('auth_tokens');
      localStorage.removeItem('auth_user');
      localStorage.removeItem('chat_messages');
      localStorage.removeItem('chat_session');
      
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
    }
  };

  const refreshTokens = async (refreshToken) => {
    try {
      const apiClient = createApiClient();
      const response = await apiClient.post('/auth/refresh', {
        refresh_token: refreshToken
      });

      const newTokens = response.data;
      localStorage.setItem('auth_tokens', JSON.stringify(newTokens));

      dispatch({
        type: AUTH_ACTIONS.REFRESH_TOKEN,
        payload: newTokens
      });

      return newTokens;

    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      return null;
    }
  };

  const updateProfile = async (profileData) => {
    try {
      const apiClient = createApiClient(state.tokens);
      const response = await apiClient.put('/auth/me', profileData);

      const updatedUser = response.data;
      localStorage.setItem('auth_user', JSON.stringify(updatedUser));

      dispatch({
        type: AUTH_ACTIONS.UPDATE_PROFILE,
        payload: updatedUser
      });

      return { success: true, user: updatedUser };

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Profile update failed';
      return { success: false, error: errorMessage };
    }
  };

  const changePassword = async (currentPassword, newPassword) => {
    try {
      const apiClient = createApiClient(state.tokens);
      await apiClient.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      });

      return { success: true };

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Password change failed';
      return { success: false, error: errorMessage };
    }
  };

  const forgotPassword = async (email) => {
    try {
      const apiClient = createApiClient();
      await apiClient.post('/auth/forgot-password', { email });

      return { success: true };

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Password reset request failed';
      return { success: false, error: errorMessage };
    }
  };

  const resetPassword = async (resetToken, newPassword) => {
    try {
      const apiClient = createApiClient();
      await apiClient.post('/auth/reset-password', {
        reset_token: resetToken,
        new_password: newPassword
      });

      return { success: true };

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Password reset failed';
      return { success: false, error: errorMessage };
    }
  };

  const getUserSessions = async () => {
    try {
      const apiClient = createApiClient(state.tokens);
      const response = await apiClient.get('/auth/sessions');
      return { success: true, sessions: response.data };

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get sessions';
      return { success: false, error: errorMessage };
    }
  };

  const revokeSession = async (sessionId) => {
    try {
      const apiClient = createApiClient(state.tokens);
      await apiClient.delete(`/auth/sessions/${sessionId}`);
      return { success: true };

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to revoke session';
      return { success: false, error: errorMessage };
    }
  };

  const revokeAllSessions = async (keepCurrent = true) => {
    try {
      const apiClient = createApiClient(state.tokens);
      const response = await apiClient.delete('/auth/sessions', {
        params: { keep_current: keepCurrent }
      });
      return { success: true, data: response.data };

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to revoke sessions';
      return { success: false, error: errorMessage };
    }
  };

  // Permission helpers
  const hasPermission = (permission) => {
    return state.permissions.includes(permission);
  };

  const hasRole = (role) => {
    return state.roles.includes(role);
  };

  const hasAnyRole = (roles) => {
    return roles.some(role => state.roles.includes(role));
  };

  const isAdmin = () => {
    return hasRole('admin');
  };

  const isAgent = () => {
    return hasRole('agent');
  };

  const isClient = () => {
    return hasRole('client');
  };

  const isEmployee = () => {
    return hasRole('employee');
  };

  // API client with current tokens
  const getApiClient = () => {
    return createApiClient(state.tokens);
  };

  // Clear error
  const clearError = () => {
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });
  };

  // Context value
  const value = {
    // State
    ...state,

    // Actions
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    forgotPassword,
    resetPassword,
    getUserSessions,
    revokeSession,
    revokeAllSessions,
    clearError,

    // Helpers
    hasPermission,
    hasRole,
    hasAnyRole,
    isAdmin,
    isAgent,
    isClient,
    isEmployee,
    getApiClient
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;