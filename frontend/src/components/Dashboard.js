/**
 * Dashboard Component for Real Estate RAG Chat System
 * Main dashboard with role-based content and navigation
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import EnhancedChat from './EnhancedChat';
import ModernPropertyManagement from './ModernPropertyManagement';
import EnhancedFileUpload from './EnhancedFileUpload';
import './Dashboard.css';

const Dashboard = () => {
  const { user, logout, isAdmin, isAgent, isClient, isEmployee, getApiClient } = useAuth();
  const navigate = useNavigate();
  
  const [currentView, setCurrentView] = useState('chat');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [properties, setProperties] = useState([]);
  const [sessionId, setSessionId] = useState(null);

  useEffect(() => {
    // Generate session ID for current user
    const newSessionId = `session_${user?.id}_${Date.now()}`;
    setSessionId(newSessionId);
    
    // Load initial data
    loadUserData();
  }, [user]);

  const loadUserData = async () => {
    try {
      // Load properties if user has permission
      if (user?.permissions?.includes('read_properties')) {
        await loadProperties();
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  const loadProperties = async () => {
    try {
      const apiClient = getApiClient();
      const response = await apiClient.get('/api/properties');
      setProperties(response.data.properties || []);
    } catch (error) {
      console.error('Error loading properties:', error);
    }
  };

  const handleSendMessage = async (messageText) => {
    if (!messageText.trim()) return;

    const userMessage = {
      sender: 'user',
      text: messageText,
      timestamp: new Date().toISOString()
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setIsLoading(true);
    setError(null);

    try {
      const apiClient = getApiClient();
      const response = await apiClient.post('/chat', {
        message: messageText,
        role: user?.roles?.[0] || 'client',
        session_id: sessionId
      });

      const aiMessage = {
        sender: 'ai',
        text: response.data.response,
        timestamp: new Date().toISOString(),
        sources: response.data.sources || []
      };

      setMessages([...updatedMessages, aiMessage]);
    } catch (error) {
      setError(`Error: ${error.response?.data?.detail || error.message}`);
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (files) => {
    try {
      const apiClient = getApiClient();
      
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await apiClient.post('/upload-file', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        // Add upload confirmation message
        const uploadMessage = {
          sender: 'ai',
          text: `File "${file.name}" has been successfully uploaded and processed. I can now help you with questions about this document.`,
          timestamp: new Date().toISOString(),
          sources: [file.name]
        };
        setMessages(prev => [...prev, uploadMessage]);
      }
    } catch (error) {
      setError(`Upload failed: ${error.response?.data?.detail || error.message}`);
      console.error('Upload error:', error);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const getRoleIcon = (role) => {
    const icons = {
      client: '👤',
      agent: '🏠',
      employee: '👨‍💼',
      admin: '⚙️'
    };
    return icons[role] || '👤';
  };

  const getRoleColor = (role) => {
    const colors = {
      client: 'var(--primary-600)',
      agent: 'var(--success-600)',
      employee: 'var(--warning-600)',
      admin: 'var(--error-600)'
    };
    return colors[role] || 'var(--primary-600)';
  };

  const getNavigationItems = () => {
    const items = [
      { id: 'chat', label: 'Chat', icon: '💬', permission: 'chat_access' },
      { id: 'properties', label: 'Properties', icon: '🏠', permission: 'read_properties' },
      { id: 'upload', label: 'File Upload', icon: '📁', permission: 'upload_files' }
    ];

    // Filter items based on user permissions
    return items.filter(item => 
      !item.permission || user?.permissions?.includes(item.permission)
    );
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'chat':
        return (
          <EnhancedChat
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            selectedRole={user?.roles?.[0] || 'client'}
            onRoleChange={() => {}} // Role change handled by auth
            error={error}
          />
        );
      case 'properties':
        return (
          <ModernPropertyManagement
            properties={properties}
          />
        );
      case 'upload':
        return (
          <EnhancedFileUpload
            onFileUpload={handleFileUpload}
            selectedRole={user?.roles?.[0] || 'client'}
            onAnalysisComplete={(results) => {
              console.log('AI Analysis completed:', results);
            }}
          />
        );
      default:
        return null;
    }
  };

  const navigationItems = getNavigationItems();

  return (
    <div className="dashboard">
      {/* Navigation Header */}
      <nav className="dashboard-navigation">
        <div className="nav-content">
          <div className="nav-brand">
            <div className="brand-logo">
              <span className="logo-icon">🏢</span>
            </div>
            <div className="brand-text">
              <h1 className="brand-title">Real Estate AI Assistant</h1>
              <p className="brand-subtitle">Your intelligent property partner</p>
            </div>
          </div>

          <div className="nav-menu">
            {navigationItems.map((item) => (
              <button
                key={item.id}
                className={`nav-item ${currentView === item.id ? 'active' : ''}`}
                onClick={() => setCurrentView(item.id)}
              >
                <span className="nav-icon">{item.icon}</span>
                <span className="nav-text">{item.label}</span>
              </button>
            ))}
          </div>

          <div className="nav-user">
            <div className="user-info">
              <div className="user-avatar">
                <span style={{ color: getRoleColor(user?.roles?.[0]) }}>
                  {getRoleIcon(user?.roles?.[0])}
                </span>
              </div>
              <div className="user-details">
                <span className="user-name">
                  {user?.first_name} {user?.last_name}
                </span>
                <span className="user-role">
                  {user?.roles?.[0]?.charAt(0)?.toUpperCase() + user?.roles?.[0]?.slice(1)}
                </span>
              </div>
            </div>
            
            <div className="user-actions">
              <button
                className="profile-button"
                onClick={() => navigate('/profile')}
                title="Profile Settings"
              >
                ⚙️
              </button>
              <button
                className="logout-button"
                onClick={handleLogout}
                title="Logout"
              >
                🚪
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="dashboard-main">
        {error && (
          <div className="error-banner">
            <div className="error-content">
              <span className="error-icon">⚠️</span>
              <span className="error-message">{error}</span>
              <button 
                className="error-close"
                onClick={() => setError(null)}
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {renderCurrentView()}
      </main>

      {/* Status Bar */}
      <div className="dashboard-status">
        <div className="status-items">
          <div className="status-item">
            <span className="status-label">Session:</span>
            <span className="status-value">{sessionId?.slice(-8)}</span>
          </div>
          <div className="status-item">
            <span className="status-label">Messages:</span>
            <span className="status-value">{messages.length}</span>
          </div>
          <div className="status-item">
            <div className="connection-status">
              <div className="status-indicator connected"></div>
              <span className="status-text">Connected</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;