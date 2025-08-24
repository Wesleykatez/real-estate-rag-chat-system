/**
 * Enhanced Property Management Component for Real Estate RAG Chat System
 * Provides full CRUD operations with authentication and role-based access control
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import PropertyForm from './PropertyForm';
import PropertyCard from './PropertyCard';
import PropertyModal from './PropertyModal';
import './EnhancedPropertyManagement.css';

const EnhancedPropertyManagement = () => {
  const { user, getApiClient, hasPermission, isAgent, isAdmin } = useAuth();
  
  // State management
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    search: '',
    property_type: '',
    status: '',
    emirate: '',
    area: '',
    min_price: '',
    max_price: '',
    min_bedrooms: '',
    max_bedrooms: '',
    min_bathrooms: '',
    max_bathrooms: '',
    min_sqft: '',
    max_sqft: '',
    furnished: '',
    balcony: '',
    parking: '',
    is_featured: '',
    agent_id: ''
  });
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(12);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  
  // Modal states
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showPropertyModal, setShowPropertyModal] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState(null);
  
  // View mode
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'

  // Property types and emirate options
  const propertyTypes = ['apartment', 'villa', 'townhouse', 'penthouse', 'studio', 'duplex', 'land', 'commercial'];
  const emirates = ['Dubai', 'Abu Dhabi', 'Sharjah', 'Ajman', 'Ras Al Khaimah', 'Fujairah', 'Umm Al Quwain'];
  const statusOptions = ['available', 'sold', 'under_contract', 'off_market'];

  // Load properties from API
  const loadProperties = useCallback(async () => {
    if (!hasPermission('read_properties')) {
      setError('You do not have permission to view properties');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const apiClient = getApiClient();
      
      // Build query parameters
      const params = new URLSearchParams();
      params.append('skip', ((currentPage - 1) * itemsPerPage).toString());
      params.append('limit', itemsPerPage.toString());
      params.append('sort_by', sortBy);
      params.append('sort_order', sortOrder);
      
      // Add filters
      Object.entries(filters).forEach(([key, value]) => {
        if (value && value !== '') {
          params.append(key, value);
        }
      });

      const response = await apiClient.get(`/api/properties?${params.toString()}`);
      const data = response.data;
      
      setProperties(data.properties || []);
      setTotalItems(data.pagination?.total || 0);
      setTotalPages(data.pagination?.pages || 1);
      setError(null);
      
    } catch (error) {
      console.error('Error loading properties:', error);
      setError(error.response?.data?.detail || 'Failed to load properties');
    } finally {
      setLoading(false);
    }
  }, [currentPage, itemsPerPage, sortBy, sortOrder, filters, hasPermission, getApiClient]);

  // Load properties on component mount and when dependencies change
  useEffect(() => {
    loadProperties();
  }, [loadProperties]);

  // Handle filter changes
  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
    setCurrentPage(1); // Reset to first page when filters change
  };

  // Handle sorting changes
  const handleSortChange = (newSortBy, newSortOrder) => {
    setSortBy(newSortBy);
    setSortOrder(newSortOrder);
    setCurrentPage(1);
  };

  // Clear all filters
  const clearFilters = () => {
    setFilters({
      search: '',
      property_type: '',
      status: '',
      emirate: '',
      area: '',
      min_price: '',
      max_price: '',
      min_bedrooms: '',
      max_bedrooms: '',
      min_bathrooms: '',
      max_bathrooms: '',
      min_sqft: '',
      max_sqft: '',
      furnished: '',
      balcony: '',
      parking: '',
      is_featured: '',
      agent_id: ''
    });
    setCurrentPage(1);
  };

  // Handle property creation
  const handleCreateProperty = async (propertyData) => {
    try {
      const apiClient = getApiClient();
      await apiClient.post('/api/properties/', propertyData);
      setShowCreateForm(false);
      loadProperties(); // Reload properties
    } catch (error) {
      console.error('Error creating property:', error);
      throw error;
    }
  };

  // Handle property editing
  const handleEditProperty = async (propertyId, propertyData) => {
    try {
      const apiClient = getApiClient();
      await apiClient.put(`/api/properties/${propertyId}`, propertyData);
      setShowEditForm(false);
      setSelectedProperty(null);
      loadProperties(); // Reload properties
    } catch (error) {
      console.error('Error updating property:', error);
      throw error;
    }
  };

  // Handle property deletion
  const handleDeleteProperty = async (propertyId) => {
    if (!window.confirm('Are you sure you want to delete this property?')) {
      return;
    }

    try {
      const apiClient = getApiClient();
      await apiClient.delete(`/api/properties/${propertyId}`);
      loadProperties(); // Reload properties
    } catch (error) {
      console.error('Error deleting property:', error);
      alert('Failed to delete property: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Handle property view
  const handleViewProperty = (property) => {
    setSelectedProperty(property);
    setShowPropertyModal(true);
  };

  // Handle property edit
  const handleEditClick = (property) => {
    setSelectedProperty(property);
    setShowEditForm(true);
  };

  // Pagination handlers
  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Generate page numbers for pagination
  const getPageNumbers = () => {
    const delta = 2;
    const range = [];
    const rangeWithDots = [];

    for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
      range.push(i);
    }

    if (currentPage - delta > 2) {
      rangeWithDots.push(1, '...');
    } else {
      rangeWithDots.push(1);
    }

    rangeWithDots.push(...range);

    if (currentPage + delta < totalPages - 1) {
      rangeWithDots.push('...', totalPages);
    } else {
      rangeWithDots.push(totalPages);
    }

    return rangeWithDots;
  };

  // Check if user can create/edit properties
  const canCreateProperties = hasPermission('create_properties') || isAgent() || isAdmin();
  const canEditProperties = hasPermission('update_properties') || isAgent() || isAdmin();

  if (loading && properties.length === 0) {
    return (
      <div className="property-management-loading">
        <div className="loading-spinner"></div>
        <p>Loading properties...</p>
      </div>
    );
  }

  return (
    <div className="enhanced-property-management">
      {/* Header */}
      <div className="property-header">
        <div className="header-content">
          <div className="header-title">
            <h1>Property Management</h1>
            <p>Manage your real estate portfolio</p>
          </div>
          
          {canCreateProperties && (
            <div className="header-actions">
              <button
                className="create-property-btn"
                onClick={() => setShowCreateForm(true)}
              >
                <span className="btn-icon">➕</span>
                Add New Property
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="property-filters">
        <div className="filters-section">
          <div className="search-bar">
            <input
              type="text"
              placeholder="Search properties..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="search-input"
            />
            <span className="search-icon">🔍</span>
          </div>

          <div className="filter-row">
            <select
              value={filters.property_type}
              onChange={(e) => handleFilterChange('property_type', e.target.value)}
              className="filter-select"
            >
              <option value="">All Types</option>
              {propertyTypes.map(type => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>

            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="filter-select"
            >
              <option value="">All Status</option>
              {statusOptions.map(status => (
                <option key={status} value={status}>
                  {status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
                </option>
              ))}
            </select>

            <select
              value={filters.emirate}
              onChange={(e) => handleFilterChange('emirate', e.target.value)}
              className="filter-select"
            >
              <option value="">All Emirates</option>
              {emirates.map(emirate => (
                <option key={emirate} value={emirate}>{emirate}</option>
              ))}
            </select>

            <input
              type="text"
              placeholder="Area"
              value={filters.area}
              onChange={(e) => handleFilterChange('area', e.target.value)}
              className="filter-input"
            />
          </div>

          <div className="filter-row">
            <input
              type="number"
              placeholder="Min Price (AED)"
              value={filters.min_price}
              onChange={(e) => handleFilterChange('min_price', e.target.value)}
              className="filter-input"
            />

            <input
              type="number"
              placeholder="Max Price (AED)"
              value={filters.max_price}
              onChange={(e) => handleFilterChange('max_price', e.target.value)}
              className="filter-input"
            />

            <select
              value={filters.min_bedrooms}
              onChange={(e) => handleFilterChange('min_bedrooms', e.target.value)}
              className="filter-select"
            >
              <option value="">Min Bedrooms</option>
              {[1, 2, 3, 4, 5, 6].map(num => (
                <option key={num} value={num}>{num}+</option>
              ))}
            </select>

            <select
              value={filters.furnished}
              onChange={(e) => handleFilterChange('furnished', e.target.value)}
              className="filter-select"
            >
              <option value="">Furnished</option>
              <option value="true">Furnished</option>
              <option value="false">Unfurnished</option>
            </select>
          </div>

          <div className="filter-actions">
            <button onClick={clearFilters} className="clear-filters-btn">
              Clear Filters
            </button>
          </div>
        </div>

        {/* Sort and View Controls */}
        <div className="controls-section">
          <div className="sort-controls">
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [newSortBy, newSortOrder] = e.target.value.split('-');
                handleSortChange(newSortBy, newSortOrder);
              }}
              className="sort-select"
            >
              <option value="created_at-desc">Newest First</option>
              <option value="created_at-asc">Oldest First</option>
              <option value="price-asc">Price: Low to High</option>
              <option value="price-desc">Price: High to Low</option>
              <option value="title-asc">Title: A to Z</option>
              <option value="title-desc">Title: Z to A</option>
              <option value="square_feet-desc">Size: Large to Small</option>
              <option value="square_feet-asc">Size: Small to Large</option>
            </select>
          </div>

          <div className="view-controls">
            <button
              className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
            >
              ⊞
            </button>
            <button
              className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
              onClick={() => setViewMode('list')}
            >
              ☰
            </button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Properties Grid/List */}
      <div className="property-content">
        {loading ? (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
            <p>Loading properties...</p>
          </div>
        ) : properties.length === 0 ? (
          <div className="no-properties">
            <div className="no-properties-icon">🏠</div>
            <h3>No Properties Found</h3>
            <p>Try adjusting your filters or create a new property.</p>
            {canCreateProperties && (
              <button
                className="create-property-btn"
                onClick={() => setShowCreateForm(true)}
              >
                Create Your First Property
              </button>
            )}
          </div>
        ) : (
          <div className={`properties-grid ${viewMode}`}>
            {properties.map(property => (
              <PropertyCard
                key={property.id}
                property={property}
                viewMode={viewMode}
                onView={handleViewProperty}
                onEdit={canEditProperties ? handleEditClick : null}
                onDelete={canEditProperties ? handleDeleteProperty : null}
                currentUser={user}
              />
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="pagination-btn"
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
          >
            ← Previous
          </button>
          
          <div className="pagination-numbers">
            {getPageNumbers().map((page, index) => (
              <button
                key={index}
                className={`pagination-number ${page === currentPage ? 'active' : ''} ${page === '...' ? 'dots' : ''}`}
                onClick={() => typeof page === 'number' && handlePageChange(page)}
                disabled={page === '...'}
              >
                {page}
              </button>
            ))}
          </div>
          
          <button
            className="pagination-btn"
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
          >
            Next →
          </button>
        </div>
      )}

      {/* Property Statistics */}
      <div className="property-stats">
        <div className="stat-item">
          <span className="stat-value">{totalItems}</span>
          <span className="stat-label">Total Properties</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{properties.filter(p => p.status === 'available').length}</span>
          <span className="stat-label">Available</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{properties.filter(p => p.status === 'sold').length}</span>
          <span className="stat-label">Sold</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{properties.filter(p => p.is_featured).length}</span>
          <span className="stat-label">Featured</span>
        </div>
      </div>

      {/* Modals */}
      {showCreateForm && (
        <PropertyForm
          mode="create"
          onSubmit={handleCreateProperty}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      {showEditForm && selectedProperty && (
        <PropertyForm
          mode="edit"
          property={selectedProperty}
          onSubmit={(data) => handleEditProperty(selectedProperty.id, data)}
          onCancel={() => {
            setShowEditForm(false);
            setSelectedProperty(null);
          }}
        />
      )}

      {showPropertyModal && selectedProperty && (
        <PropertyModal
          property={selectedProperty}
          onClose={() => {
            setShowPropertyModal(false);
            setSelectedProperty(null);
          }}
          onEdit={canEditProperties ? handleEditClick : null}
          onDelete={canEditProperties ? handleDeleteProperty : null}
        />
      )}
    </div>
  );
};

export default EnhancedPropertyManagement;