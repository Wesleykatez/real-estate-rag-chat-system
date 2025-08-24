import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';

// Authentication components
import LoginForm from './components/auth/LoginForm';
import RegisterForm from './components/auth/RegisterForm';
import ProtectedRoute, { PublicRoute, AdminRoute, AgentRoute } from './components/auth/ProtectedRoute';

// Main application components
import Dashboard from './components/Dashboard';
import EnhancedChat from './components/EnhancedChat';
import ModernPropertyManagement from './components/ModernPropertyManagement';
import EnhancedFileUpload from './components/EnhancedFileUpload';

// Styles
import './App.css';
import './styles/modern-design-system.css';
import './components/auth/AuthForms.css';

// Placeholder for missing components
const AdminDashboard = () => (
  <div style={{ padding: '2rem', textAlign: 'center' }}>
    <h2>Admin Dashboard</h2>
    <p>Coming Soon - Advanced admin features in development</p>
  </div>
);

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="app">
          <Routes>
            {/* Public routes */}
            <Route 
              path="/login" 
              element={
                <PublicRoute>
                  <LoginForm />
                </PublicRoute>
              } 
            />
            <Route 
              path="/register" 
              element={
                <PublicRoute>
                  <RegisterForm />
                </PublicRoute>
              } 
            />

            {/* Protected routes */}
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/chat" 
              element={
                <ProtectedRoute>
                  <EnhancedChat />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/properties" 
              element={
                <ProtectedRoute>
                  <ModernPropertyManagement />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/upload" 
              element={
                <ProtectedRoute>
                  <EnhancedFileUpload />
                </ProtectedRoute>
              } 
            />

            {/* Admin routes */}
            <Route 
              path="/admin/*" 
              element={
                <AdminRoute>
                  <AdminDashboard />
                </AdminRoute>
              } 
            />

            {/* Default redirects */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;