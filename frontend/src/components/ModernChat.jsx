import React, { useState, useRef, useEffect } from 'react';
import './ModernChat.css';
import SmartSuggestions from './SmartSuggestions';

const ModernChat = ({ 
  messages, 
  onSendMessage, 
  isLoading, 
  selectedRole, 
  onRoleChange,
  onClearChat,
  isSaving,
  sessionId,
  suggestions = []
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputMessage.trim() && !isLoading) {
      onSendMessage(inputMessage);
      setInputMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion);
    onSendMessage(suggestion);
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
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

  return (
    <div className="modern-chat-container">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-content">
          <div className="chat-title">
            <div className="chat-logo">
              <span className="logo-icon">🏢</span>
            </div>
            <div className="title-text">
              <h1 className="app-title">Real Estate AI Assistant</h1>
              <p className="app-subtitle">Your intelligent property partner</p>
              <small style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>
                Session: {sessionId ? sessionId.substring(0, 8) + '...' : 'New'}
              </small>
            </div>
          </div>
          
          <div className="chat-actions">
            <div className="connection-status">
              <div className={`status-indicator ${isLoading ? 'connecting' : isSaving ? 'saving' : 'connected'}`}></div>
              <span className="status-text">
                {isLoading ? 'Connecting...' : isSaving ? 'Saving...' : 'Connected'}
              </span>
            </div>
            
            <button 
              className="btn btn-ghost btn-sm clear-chat-btn"
              onClick={onClearChat}
              title="Clear chat history"
            >
              <span className="btn-icon">🗑️</span>
              <span className="btn-text">Clear</span>
            </button>
          </div>
        </div>
      </div>

      {/* Role Selector */}
      <div className="role-selector">
        <div className="role-selector-content">
          {['client', 'agent', 'employee', 'admin'].map((role) => (
            <button
              key={role}
              className={`role-btn ${selectedRole === role ? 'active' : ''}`}
              onClick={() => onRoleChange(role)}
              style={{
                '--role-color': getRoleColor(role)
              }}
            >
              <span className="role-icon">{getRoleIcon(role)}</span>
              <span className="role-text">{role.charAt(0).toUpperCase() + role.slice(1)}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Messages Container */}
      <div className="messages-container">
        <div className="messages-list">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">💬</div>
              <h3 className="empty-state-title">Start a conversation</h3>
              <p className="empty-state-description">
                Ask me anything about properties, market trends, or real estate in Dubai
              </p>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={`message-wrapper ${message.sender === 'user' ? 'user-message' : 'ai-message'}`}
              >
                <div className="message-bubble">
                  {message.sender === 'ai' && (
                    <div className="message-avatar">
                      <span className="avatar-icon">🤖</span>
                    </div>
                  )}
                  
                  <div className="message-content">
                    <div className="message-header">
                      <span className="message-sender">
                        {message.sender === 'user' ? 'You' : 'AI Assistant'}
                      </span>
                      <span className="message-time">
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                    
                    <div className="message-text">
                      {message.text}
                    </div>
                    
                    {message.sources && message.sources.length > 0 && (
                      <div className="message-sources">
                        <div className="sources-header">
                          <span className="sources-icon">📚</span>
                          <span className="sources-title">Sources</span>
                        </div>
                        <div className="sources-list">
                          {message.sources.map((source, idx) => (
                            <div key={idx} className="source-item">
                              <span className="source-icon">📄</span>
                              <span className="source-text">{source}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="message-wrapper ai-message">
              <div className="message-bubble">
                <div className="message-avatar">
                  <span className="avatar-icon">🤖</span>
                </div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <div className="typing-dots">
                      <div className="dot"></div>
                      <div className="dot"></div>
                      <div className="dot"></div>
                    </div>
                    <span className="typing-text">AI is thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        {/* Smart Suggestions */}
        {suggestions.length > 0 && !isLoading && (
          <SmartSuggestions
            suggestions={suggestions}
            onSuggestionClick={handleSuggestionClick}
            selectedRole={selectedRole}
          />
        )}
      </div>

      {/* Input Area */}
      <div className="chat-input-container">
        <form className="chat-input-form" onSubmit={handleSubmit}>
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              className="chat-input"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`Ask me anything as a ${selectedRole}...`}
              rows="1"
              disabled={isLoading}
            />
            
            <div className="input-actions">
              <button
                type="button"
                className="btn btn-ghost btn-sm action-btn"
                title="Attach file"
                disabled={isLoading}
              >
                <span className="action-icon">📎</span>
              </button>
              
              <button
                type="button"
                className="btn btn-ghost btn-sm action-btn"
                title="Voice input"
                disabled={isLoading}
              >
                <span className="action-icon">🎤</span>
              </button>
              
              <button
                type="submit"
                className="btn btn-primary btn-sm send-btn"
                disabled={!inputMessage.trim() || isLoading}
              >
                <span className="send-icon">➤</span>
              </button>
            </div>
          </div>
        </form>
        
        <div className="input-footer">
          <span className="input-hint">
            Press Enter to send, Shift+Enter for new line
          </span>
        </div>
      </div>
    </div>
  );
};

export default ModernChat;
