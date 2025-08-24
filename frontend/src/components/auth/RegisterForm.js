/**
 * Registration Form Component for Real Estate RAG Chat System
 * Provides user registration with role selection and validation
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import './AuthForms.css';

const RegisterForm = () => {
  const { register, isLoading, error, clearError, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    phone: '',
    role: 'client',
    company: '',
    jobTitle: '',
    licenseNumber: '',
    bio: '',
    acceptTerms: false
  });

  const [formErrors, setFormErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({ score: 0, feedback: [] });
  const [step, setStep] = useState(1); // Multi-step form

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Clear errors when component mounts
  useEffect(() => {
    clearError();
  }, [clearError]);

  const roles = [
    { value: 'client', label: 'Client', icon: '👤', description: 'Property buyer, seller, or investor' },
    { value: 'agent', label: 'Real Estate Agent', icon: '🏠', description: 'Licensed real estate professional' },
    { value: 'employee', label: 'Employee', icon: '👨‍💼', description: 'Company staff member' }
  ];

  const validatePassword = (password) => {
    const feedback = [];
    let score = 0;

    if (password.length >= 8) score++;
    else feedback.push('Use at least 8 characters');

    if (/[a-z]/.test(password)) score++;
    else feedback.push('Add lowercase letters');

    if (/[A-Z]/.test(password)) score++;
    else feedback.push('Add uppercase letters');

    if (/\d/.test(password)) score++;
    else feedback.push('Add numbers');

    if (/[^A-Za-z0-9]/.test(password)) score++;
    else feedback.push('Add special characters');

    return { score, feedback };
  };

  const validateForm = (currentStep) => {
    const errors = {};

    if (currentStep === 1) {
      // Step 1: Basic Information
      if (!formData.firstName) {
        errors.firstName = 'First name is required';
      }

      if (!formData.lastName) {
        errors.lastName = 'Last name is required';
      }

      if (!formData.email) {
        errors.email = 'Email is required';
      } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
        errors.email = 'Please enter a valid email address';
      }

      if (!formData.username) {
        errors.username = 'Username is required';
      } else if (formData.username.length < 3) {
        errors.username = 'Username must be at least 3 characters';
      }

      if (!formData.role) {
        errors.role = 'Please select a role';
      }
    }

    if (currentStep === 2) {
      // Step 2: Password and Security
      if (!formData.password) {
        errors.password = 'Password is required';
      } else if (passwordStrength.score < 3) {
        errors.password = 'Password is too weak';
      }

      if (!formData.confirmPassword) {
        errors.confirmPassword = 'Please confirm your password';
      } else if (formData.password !== formData.confirmPassword) {
        errors.confirmPassword = 'Passwords do not match';
      }

      if (!formData.acceptTerms) {
        errors.acceptTerms = 'You must accept the terms and conditions';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;

    setFormData(prev => ({
      ...prev,
      [name]: newValue
    }));

    // Update password strength
    if (name === 'password') {
      setPasswordStrength(validatePassword(value));
    }

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

  const handleNextStep = () => {
    if (validateForm(step)) {
      setStep(step + 1);
    }
  };

  const handlePrevStep = () => {
    setStep(step - 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm(2)) {
      return;
    }

    const registrationData = {
      email: formData.email,
      username: formData.username,
      password: formData.password,
      first_name: formData.firstName,
      last_name: formData.lastName,
      phone: formData.phone || null,
      role: formData.role,
      company: formData.company || null,
      job_title: formData.jobTitle || null,
      license_number: formData.licenseNumber || null,
      bio: formData.bio || null
    };

    const result = await register(registrationData);

    if (result.success) {
      navigate('/login', {
        state: {
          message: 'Registration successful! Please sign in to continue.',
          email: formData.email
        }
      });
    }
  };

  const getPasswordStrengthColor = (score) => {
    const colors = ['#ff4757', '#ff6b7a', '#ffa502', '#2ed573', '#2ed573'];
    return colors[score] || colors[0];
  };

  const getPasswordStrengthText = (score) => {
    const texts = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
    return texts[score] || texts[0];
  };

  const renderStep1 = () => (
    <>
      <div className="step-header">
        <h3>Basic Information</h3>
        <p>Let's start with your basic details</p>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="firstName">First Name *</label>
          <input
            type="text"
            id="firstName"
            name="firstName"
            value={formData.firstName}
            onChange={handleChange}
            className={formErrors.firstName ? 'error' : ''}
            placeholder="Enter your first name"
            disabled={isLoading}
          />
          {formErrors.firstName && (
            <span className="field-error">{formErrors.firstName}</span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="lastName">Last Name *</label>
          <input
            type="text"
            id="lastName"
            name="lastName"
            value={formData.lastName}
            onChange={handleChange}
            className={formErrors.lastName ? 'error' : ''}
            placeholder="Enter your last name"
            disabled={isLoading}
          />
          {formErrors.lastName && (
            <span className="field-error">{formErrors.lastName}</span>
          )}
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="email">Email Address *</label>
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
          />
          <span className="input-icon">📧</span>
        </div>
        {formErrors.email && (
          <span className="field-error">{formErrors.email}</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="username">Username *</label>
        <input
          type="text"
          id="username"
          name="username"
          value={formData.username}
          onChange={handleChange}
          className={formErrors.username ? 'error' : ''}
          placeholder="Choose a username"
          disabled={isLoading}
        />
        {formErrors.username && (
          <span className="field-error">{formErrors.username}</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="phone">Phone Number</label>
        <input
          type="tel"
          id="phone"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          placeholder="+971 50 123 4567"
          disabled={isLoading}
        />
      </div>

      <div className="form-group">
        <label>Select Your Role *</label>
        <div className="role-selection">
          {roles.map(role => (
            <label key={role.value} className="role-option">
              <input
                type="radio"
                name="role"
                value={role.value}
                checked={formData.role === role.value}
                onChange={handleChange}
                disabled={isLoading}
              />
              <div className="role-card">
                <span className="role-icon">{role.icon}</span>
                <h4>{role.label}</h4>
                <p>{role.description}</p>
              </div>
            </label>
          ))}
        </div>
        {formErrors.role && (
          <span className="field-error">{formErrors.role}</span>
        )}
      </div>

      {(formData.role === 'agent' || formData.role === 'employee') && (
        <>
          <div className="form-group">
            <label htmlFor="company">Company</label>
            <input
              type="text"
              id="company"
              name="company"
              value={formData.company}
              onChange={handleChange}
              placeholder="Your company name"
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="jobTitle">Job Title</label>
            <input
              type="text"
              id="jobTitle"
              name="jobTitle"
              value={formData.jobTitle}
              onChange={handleChange}
              placeholder="Your job title"
              disabled={isLoading}
            />
          </div>

          {formData.role === 'agent' && (
            <div className="form-group">
              <label htmlFor="licenseNumber">License Number</label>
              <input
                type="text"
                id="licenseNumber"
                name="licenseNumber"
                value={formData.licenseNumber}
                onChange={handleChange}
                placeholder="Your real estate license number"
                disabled={isLoading}
              />
            </div>
          )}
        </>
      )}
    </>
  );

  const renderStep2 = () => (
    <>
      <div className="step-header">
        <h3>Security Setup</h3>
        <p>Choose a strong password to secure your account</p>
      </div>

      <div className="form-group">
        <label htmlFor="password">Password *</label>
        <div className="input-wrapper">
          <input
            type={showPassword ? 'text' : 'password'}
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            className={formErrors.password ? 'error' : ''}
            placeholder="Choose a strong password"
            disabled={isLoading}
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

        {formData.password && (
          <div className="password-strength">
            <div className="strength-bar">
              <div 
                className="strength-fill"
                style={{
                  width: `${(passwordStrength.score / 5) * 100}%`,
                  backgroundColor: getPasswordStrengthColor(passwordStrength.score)
                }}
              ></div>
            </div>
            <span 
              className="strength-text"
              style={{ color: getPasswordStrengthColor(passwordStrength.score) }}
            >
              {getPasswordStrengthText(passwordStrength.score)}
            </span>
            {passwordStrength.feedback.length > 0 && (
              <ul className="strength-feedback">
                {passwordStrength.feedback.map((feedback, index) => (
                  <li key={index}>{feedback}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {formErrors.password && (
          <span className="field-error">{formErrors.password}</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="confirmPassword">Confirm Password *</label>
        <div className="input-wrapper">
          <input
            type={showConfirmPassword ? 'text' : 'password'}
            id="confirmPassword"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            className={formErrors.confirmPassword ? 'error' : ''}
            placeholder="Confirm your password"
            disabled={isLoading}
          />
          <button
            type="button"
            className="password-toggle"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            disabled={isLoading}
          >
            {showConfirmPassword ? '👁️' : '🙈'}
          </button>
        </div>
        {formErrors.confirmPassword && (
          <span className="field-error">{formErrors.confirmPassword}</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="bio">Bio (Optional)</label>
        <textarea
          id="bio"
          name="bio"
          value={formData.bio}
          onChange={handleChange}
          placeholder="Tell us a bit about yourself..."
          rows="3"
          disabled={isLoading}
        />
      </div>

      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            name="acceptTerms"
            checked={formData.acceptTerms}
            onChange={handleChange}
            disabled={isLoading}
          />
          <span className="checkbox-custom"></span>
          I agree to the{' '}
          <Link to="/terms" target="_blank" className="auth-link">
            Terms of Service
          </Link>{' '}
          and{' '}
          <Link to="/privacy" target="_blank" className="auth-link">
            Privacy Policy
          </Link>
        </label>
        {formErrors.acceptTerms && (
          <span className="field-error">{formErrors.acceptTerms}</span>
        )}
      </div>
    </>
  );

  return (
    <div className="auth-container">
      <div className="auth-card register-card">
        <div className="auth-header">
          <div className="auth-logo">
            <span className="logo-icon">🏠</span>
            <h1>Real Estate AI</h1>
          </div>
          <h2>Create Your Account</h2>
          <p>Join thousands of real estate professionals</p>
        </div>

        <div className="step-indicator">
          <div className={`step ${step >= 1 ? 'active' : ''}`}>
            <span>1</span>
            <p>Basic Info</p>
          </div>
          <div className={`step ${step >= 2 ? 'active' : ''}`}>
            <span>2</span>
            <p>Security</p>
          </div>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <span>{typeof error === 'string' ? error : 'Registration failed. Please try again.'}</span>
            </div>
          )}

          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}

          <div className="form-actions">
            {step > 1 && (
              <button
                type="button"
                className="auth-button secondary"
                onClick={handlePrevStep}
                disabled={isLoading}
              >
                Previous
              </button>
            )}

            {step < 2 ? (
              <button
                type="button"
                className="auth-button primary"
                onClick={handleNextStep}
                disabled={isLoading}
              >
                Next Step
              </button>
            ) : (
              <button
                type="submit"
                className="auth-button primary"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <span className="loading-spinner"></span>
                    Creating Account...
                  </>
                ) : (
                  'Create Account'
                )}
              </button>
            )}
          </div>

          <div className="auth-footer">
            <p>
              Already have an account?{' '}
              <Link to="/login" className="auth-link">
                Sign in here
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RegisterForm;