import React from 'react';
import './SmartSuggestions.css';

const SmartSuggestions = ({ suggestions, onSuggestionClick, selectedRole }) => {
  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  const getRoleColor = (role) => {
    const colors = {
      client: 'var(--primary-600)',
      agent: 'var(--success-600)',
      employee: 'var(--warning-600)',
      admin: 'var(--error-600)'
    };
    return colors[role] || 'var(--primary-600)';
  };

  const getSuggestionIcon = (suggestion) => {
    if (suggestion.includes('💰') || suggestion.includes('budget')) return '💰';
    if (suggestion.includes('📊') || suggestion.includes('compare')) return '📊';
    if (suggestion.includes('📍') || suggestion.includes('neighborhood')) return '📍';
    if (suggestion.includes('🏠') || suggestion.includes('viewing')) return '🏠';
    if (suggestion.includes('📱') || suggestion.includes('alert')) return '📱';
    if (suggestion.includes('🎯') || suggestion.includes('lead')) return '🎯';
    if (suggestion.includes('📈') || suggestion.includes('investment')) return '📈';
    if (suggestion.includes('💼') || suggestion.includes('sales')) return '💼';
    if (suggestion.includes('📋') || suggestion.includes('compliance')) return '📋';
    if (suggestion.includes('⚖️') || suggestion.includes('regulatory')) return '⚖️';
    if (suggestion.includes('🔧') || suggestion.includes('procedure')) return '🔧';
    if (suggestion.includes('📝') || suggestion.includes('document')) return '📝';
    if (suggestion.includes('✅') || suggestion.includes('check')) return '✅';
    if (suggestion.includes('⚙️') || suggestion.includes('system')) return '⚙️';
    if (suggestion.includes('🔍') || suggestion.includes('analyze')) return '🔍';
    return '💡';
  };

  return (
    <div className="smart-suggestions-container">
      <div className="suggestions-header">
        <span className="suggestions-title">💡 Quick Actions</span>
        <span className="suggestions-subtitle">Based on your {selectedRole} role</span>
      </div>
      
      <div className="suggestions-grid">
        {suggestions.map((suggestion, index) => {
          const cleanSuggestion = suggestion.replace(/[💰📊📍🏠📱🎯📈💼📋⚖️🔧📝✅⚙️🔍]/g, '').trim();
          const icon = getSuggestionIcon(suggestion);
          
          return (
            <button
              key={index}
              className="suggestion-button"
              onClick={() => onSuggestionClick(cleanSuggestion)}
              style={{ 
                borderColor: getRoleColor(selectedRole),
                '--role-color': getRoleColor(selectedRole)
              }}
            >
              <span className="suggestion-icon">{icon}</span>
              <span className="suggestion-text">{cleanSuggestion}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default SmartSuggestions;