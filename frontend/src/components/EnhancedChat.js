import React, { useState, useEffect, useRef } from 'react';
import './EnhancedChat.css';

const EnhancedChat = ({ 
  messages, 
  onSendMessage, 
  isLoading, 
  selectedRole, 
  onRoleChange,
  error 
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const [showMilestones, setShowMilestones] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Focus input when role changes
    inputRef.current?.focus();
  }, [selectedRole]);

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

  const formatMessage = (message) => {
    // Check for milestone celebrations
    const milestoneEmojis = ['🎉', '💼', '📅', '🤝', '🎵'];
    const hasMilestone = milestoneEmojis.some(emoji => message.text.includes(emoji));
    
    // Check for African agent celebration
    const hasAfricanCelebration = message.text.includes('🎵 Steadily, we are getting leads! 🎵');
    
    return {
      ...message,
      hasMilestone,
      hasAfricanCelebration,
      isAdminPanel: message.text.includes('⚙️ **Admin Analytics Dashboard**')
    };
  };

  const renderMessage = (message, index) => {
    const formattedMessage = formatMessage(message);
    const isUser = message.sender === 'user';
    
    return (
      <div 
        key={index} 
        className={`message ${isUser ? 'user-message' : 'ai-message'} ${
          formattedMessage.hasMilestone ? 'milestone-message' : ''
        } ${formattedMessage.hasAfricanCelebration ? 'african-celebration' : ''} ${
          formattedMessage.isAdminPanel ? 'admin-panel' : ''
        }`}
      >
        <div className="message-header">
          <span className="message-role-icon">
            {isUser ? getRoleIcon(selectedRole) : '🤖'}
          </span>
          <span className="message-sender">
            {isUser ? `${selectedRole.charAt(0).toUpperCase() + selectedRole.slice(1)}` : 'AI Assistant'}
          </span>
          <span className="message-time">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
        </div>
        
        <div className="message-content">
          {formattedMessage.hasMilestone && (
            <div className="milestone-badge">
              🎯 Milestone Achieved!
            </div>
          )}
          
          {formattedMessage.hasAfricanCelebration && (
            <div className="african-celebration-badge">
              🌍 African Agent Recognition!
            </div>
          )}
          
          {formattedMessage.isAdminPanel && (
            <div className="admin-panel-badge">
              🔐 Admin Dashboard
            </div>
          )}
          
          <div className="message-text">
            {message.text}
          </div>
          
          {message.sources && message.sources.length > 0 && (
            <div className="message-sources">
              <small>Sources: {message.sources.join(', ')}</small>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="enhanced-chat-container">
      {/* Role Selector */}
      <div className="role-selector">
        <div className="role-tabs">
          {['client', 'agent', 'employee', 'admin'].map((role) => (
            <button
              key={role}
              className={`role-tab ${selectedRole === role ? 'active' : ''}`}
              onClick={() => onRoleChange(role)}
              style={{ 
                borderColor: selectedRole === role ? getRoleColor(role) : 'transparent',
                backgroundColor: selectedRole === role ? `${getRoleColor(role)}10` : 'transparent'
              }}
            >
              <span className="role-icon">{getRoleIcon(role)}</span>
              <span className="role-name">{role.charAt(0).toUpperCase() + role.slice(1)}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Messages Container */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">💬</div>
            <h3>Welcome to Dubai Real Estate Assistant!</h3>
            <p>Start a conversation to explore properties, get market insights, or ask questions.</p>
            <div className="quick-suggestions">
              <button 
                className="suggestion-btn"
                onClick={() => onSendMessage("Show me properties in Dubai Marina")}
              >
                🏠 Show me properties in Dubai Marina
              </button>
              <button 
                className="suggestion-btn"
                onClick={() => onSendMessage("What's the investment potential in Downtown Dubai?")}
              >
                📈 Investment potential in Downtown Dubai
              </button>
              <button 
                className="suggestion-btn"
                onClick={() => onSendMessage("Tell me about Golden Visa requirements")}
              >
                🛂 Golden Visa requirements
              </button>
            </div>
          </div>
        ) : (
          messages.map((message, index) => renderMessage(message, index))
        )}
        
        {isLoading && (
          <div className="message ai-message loading-message">
            <div className="message-header">
              <span className="message-role-icon">🤖</span>
              <span className="message-sender">AI Assistant</span>
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="message-input-form">
        <div className="input-container">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={`Ask me anything about Dubai real estate as a ${selectedRole}...`}
            className="message-input"
            rows="1"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={!inputMessage.trim() || isLoading}
            style={{ backgroundColor: getRoleColor(selectedRole) }}
          >
            {isLoading ? (
              <span className="loading-spinner"></span>
            ) : (
              <span>➤</span>
            )}
          </button>
        </div>
        
        <div className="input-hints">
          <small>
            💡 Try: "Show me properties under 2M AED" • "Market trends in Palm Jumeirah" • "ROI analysis"
          </small>
        </div>
      </form>
    </div>
  );
};

export default EnhancedChat;