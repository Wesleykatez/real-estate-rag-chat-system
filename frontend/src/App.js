import React, { useState, useEffect } from 'react';
import './App.css';
import './styles/modern-design-system.css';
import ModernChat from './components/ModernChat';
import ModernPropertyManagement from './components/ModernPropertyManagement';
import ModernFileUpload from './components/ModernFileUpload';
import EnhancedFileUpload from './components/EnhancedFileUpload';

const API_BASE_URL = 'http://localhost:8001';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedRole, setSelectedRole] = useState('client');
  const [sessionId, setSessionId] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [currentView, setCurrentView] = useState('chat'); // 'chat', 'properties', or 'upload'
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(true);
  const [properties, setProperties] = useState([]);
  const [isSaving, setIsSaving] = useState(false);

  // Role definitions with enhanced descriptions
  const roles = {
    client: {
      name: 'Client',
      icon: '👤',
      description: 'Property buyers, sellers, and investors',
      color: 'var(--primary-600)'
    },
    agent: {
      name: 'Agent',
      icon: '🏠',
      description: 'Real estate agents and brokers',
      color: 'var(--success-600)'
    },
    employee: {
      name: 'Employee',
      icon: '👨‍💼',
      description: 'Company staff and employees',
      color: 'var(--warning-600)'
    },
    admin: {
      name: 'Admin',
      icon: '⚙️',
      description: 'System administrators and managers',
      color: 'var(--error-600)'
    }
  };

  useEffect(() => {
    const roleSessionKey = `chatSessionId_${selectedRole}`;
    const existingSessionId = localStorage.getItem(roleSessionKey);
    if (existingSessionId) {
      setSessionId(existingSessionId);
      loadConversation(existingSessionId);
    } else {
      const newSessionId = generateSessionId();
      setSessionId(newSessionId);
      localStorage.setItem(roleSessionKey, newSessionId);
      loadConversation(newSessionId);
    }
  }, [selectedRole]);

  useEffect(() => {
    // Load sample properties data
    loadSampleProperties();
  }, []);

  // Add this useEffect to save messages whenever they change
  useEffect(() => {
    if (sessionId && messages.length > 0) {
      setIsSaving(true);
      localStorage.setItem(`chatMessages_${sessionId}`, JSON.stringify(messages));
      setTimeout(() => setIsSaving(false), 500);
    }
  }, [messages, sessionId]);

  const generateSessionId = () => {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  };

  const loadConversation = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/conversation/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages);
          setConversationId(data.conversation_id);
        } else {
          // If no messages in backend, try localStorage
          loadFromLocalStorage(sessionId);
        }
      } else {
        // If backend fails, try localStorage
        loadFromLocalStorage(sessionId);
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
      // Fallback to localStorage
      loadFromLocalStorage(sessionId);
    }
  };

  // Add localStorage backup function
  const loadFromLocalStorage = (sessionId) => {
    const storedMessages = localStorage.getItem(`chatMessages_${sessionId}`);
    if (storedMessages) {
      try {
        setMessages(JSON.parse(storedMessages));
      } catch (error) {
        console.error('Error parsing stored messages:', error);
        // Add welcome message if parsing fails
        const welcomeMessage = {
          sender: 'ai',
          text: getWelcomeMessage(selectedRole),
          timestamp: new Date().toISOString(),
          sources: []
        };
        setMessages([welcomeMessage]);
      }
    } else {
      // Add welcome message for new session
      const welcomeMessage = {
        sender: 'ai',
        text: getWelcomeMessage(selectedRole),
        timestamp: new Date().toISOString(),
        sources: []
      };
      setMessages([welcomeMessage]);
    }
  };

  const loadSampleProperties = async () => {
    try {
      // For now, we'll use sample data since we have comprehensive data files
      const sampleProperties = [
        {
          id: 1,
          address: "Building 123, Floor 15, Unit 1501, Downtown Dubai, Dubai, UAE",
          price_aed: 2500000,
          bedrooms: 2,
          bathrooms: 2,
          square_feet: 1200,
          property_type: "Apartment",
          area: "Downtown Dubai",
          developer: "Emaar Properties",
          completion_date: "2023-06-15",
          view: "City View",
          amenities: "Swimming Pool, Gym, Spa, Tennis Court, Children's Playground, BBQ Area, Garden, Balcony, Parking, Security, Concierge, 24/7 Maintenance",
          service_charges: 15000,
          agent: "Sarah Johnson",
          agency: "Emaar Real Estate",
          status: "Available"
        },
        {
          id: 2,
          address: "Building 456, Floor 25, Unit 2503, Dubai Marina, Dubai, UAE",
          price_aed: 3200000,
          bedrooms: 3,
          bathrooms: 3,
          square_feet: 1800,
          property_type: "Apartment",
          area: "Dubai Marina",
          developer: "Damac Properties",
          completion_date: "2023-03-20",
          view: "Sea View",
          amenities: "Swimming Pool, Gym, Spa, Tennis Court, Basketball Court, Children's Playground, BBQ Area, Garden, Balcony, Terrace, Parking, Security, Concierge, 24/7 Maintenance, Pet Friendly",
          service_charges: 20000,
          agent: "Michael Chen",
          agency: "Damac Real Estate",
          status: "Under Contract"
        },
        {
          id: 3,
          address: "Villa 789, Palm Jumeirah, Dubai, UAE",
          price_aed: 8500000,
          bedrooms: 5,
          bathrooms: 6,
          square_feet: 4500,
          property_type: "Villa",
          area: "Palm Jumeirah",
          developer: "Nakheel",
          completion_date: "2022-12-10",
          view: "Sea View",
          amenities: "Private Pool, Gym, Spa, Tennis Court, Basketball Court, Children's Playground, BBQ Area, Garden, Balcony, Terrace, Parking, Security, Concierge, 24/7 Maintenance, Pet Friendly, Central AC, Furnished, Built-in Wardrobes, Modern Kitchen, Walk-in Closet, Study Room, Maid's Room, Driver's Room",
          service_charges: 35000,
          agent: "Ahmed Al Mansouri",
          agency: "Nakheel Real Estate",
          status: "Available"
        }
      ];
      setProperties(sampleProperties);
    } catch (error) {
      console.error('Error loading properties:', error);
    }
  };

  const getWelcomeMessage = (role) => {
    const roleInfo = roles[role];
    return `Hello! I'm your real estate AI assistant. I'm here to help you as a ${roleInfo.name} ${roleInfo.icon}\n\nLooking for properties. How can I assist you today?`;
  };

  const handleRoleChange = (newRole) => {
    setSelectedRole(newRole);
    setMessages([]);
    setError(null);
    
    // Clear current session from localStorage
    if (sessionId) {
      localStorage.removeItem(`chatMessages_${sessionId}`);
    }
    
    // Generate new session for the role
    const newSessionId = generateSessionId();
    setSessionId(newSessionId);
    localStorage.setItem(`chatSessionId_${newRole}`, newSessionId);
    
    // Update conversation role in backend
    fetch(`${API_BASE_URL}/conversation/${newSessionId}/role`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ role: newRole })
    }).catch(error => console.error('Error updating conversation role:', error));
    
    // Load conversation for new role
    loadConversation(newSessionId);
  };

  const handleFileUpload = async (files) => {
    setIsUploading(true);
    setError(null);

    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('role', selectedRole);

        const response = await fetch(`${API_BASE_URL}/upload`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Upload failed for ${file.name}`);
        }

        const data = await response.json();
        
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
      setError(`Upload failed: ${error.message}`);
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const sendMessage = async (messageText) => {
    if (!messageText.trim()) return;

    const userMessage = {
      sender: 'user',
      text: messageText,
      timestamp: new Date().toISOString()
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    
    // Save to localStorage immediately
    localStorage.setItem(`chatMessages_${sessionId}`, JSON.stringify(updatedMessages));
    
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          role: selectedRole,
          session_id: sessionId,
          file_upload: selectedFile ? { filename: selectedFile.name } : null
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response from server');
      }

      const data = await response.json();
      
      const aiMessage = {
        sender: 'ai',
        text: data.response,
        timestamp: new Date().toISOString(),
        sources: data.sources || [],
        suggestions: data.suggestions || []
      };

      const finalMessages = [...updatedMessages, aiMessage];
      setMessages(finalMessages);
      
      // Save to localStorage
      localStorage.setItem(`chatMessages_${sessionId}`, JSON.stringify(finalMessages));
      
      setConversationId(data.conversation_id);
    } catch (error) {
      setError(`Error: ${error.message}`);
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
    
    // Clear from localStorage
    localStorage.removeItem(`chatMessages_${sessionId}`);
    
    // Clear from backend
    if (sessionId) {
      fetch(`${API_BASE_URL}/conversation/${sessionId}/clear`, {
        method: 'DELETE'
      }).catch(error => console.error('Error clearing conversation:', error));
    }
    
    // Add welcome message after clearing
    const welcomeMessage = {
      sender: 'ai',
      text: getWelcomeMessage(selectedRole),
      timestamp: new Date().toISOString(),
      sources: []
    };
    setMessages([welcomeMessage]);
    
    // Save welcome message to localStorage
    localStorage.setItem(`chatMessages_${sessionId}`, JSON.stringify([welcomeMessage]));
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'chat':
        return (
          <ModernChat
            messages={messages}
            onSendMessage={sendMessage}
            isLoading={isLoading}
            selectedRole={selectedRole}
            onRoleChange={handleRoleChange}
            onClearChat={clearChat}
            isSaving={isSaving}
            sessionId={sessionId}
            suggestions={messages.length > 0 ? messages[messages.length - 1].suggestions || [] : []}
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
            selectedRole={selectedRole}
            onAnalysisComplete={(results) => {
              console.log('AI Analysis completed:', results);
              // You can handle the analysis results here
            }}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="app">
      {/* Navigation Header */}
      <nav className="app-navigation">
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
            <button
              className={`nav-item ${currentView === 'chat' ? 'active' : ''}`}
              onClick={() => setCurrentView('chat')}
            >
              <span className="nav-icon">💬</span>
              <span className="nav-text">Chat</span>
            </button>
            
            <button
              className={`nav-item ${currentView === 'properties' ? 'active' : ''}`}
              onClick={() => setCurrentView('properties')}
            >
              <span className="nav-icon">🏠</span>
              <span className="nav-text">Properties</span>
            </button>
            
            <button
              className={`nav-item ${currentView === 'upload' ? 'active' : ''}`}
              onClick={() => setCurrentView('upload')}
            >
              <span className="nav-icon">🤖</span>
              <span className="nav-text">AI File Analysis</span>
            </button>
          </div>

          <div className="nav-status">
            <div className="connection-status">
              <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></div>
              <span className="status-text">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="app-main">
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
    </div>
  );
}

export default App;
