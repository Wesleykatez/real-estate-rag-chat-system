import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './ModernPropertyManagement.css';

const ModernPropertyManagement = ({ properties = [] }) => {
  const [filteredProperties, setFilteredProperties] = useState(properties);
  const [filters, setFilters] = useState({
    minPrice: '',
    maxPrice: '',
    bedrooms: 'any',
    bathrooms: 'any',
    propertyType: 'any',
    location: 'any',
    minSqFt: '',
    maxSqFt: ''
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('price');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'

  // Sample property types and locations for filters
  const propertyTypes = ['Apartment', 'Villa', 'Townhouse', 'Penthouse', 'Studio', 'Duplex'];
  const locations = ['Downtown Dubai', 'Dubai Marina', 'Palm Jumeirah', 'Business Bay', 'Dubai Hills Estate'];

  useEffect(() => {
    let filtered = [...properties];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(property =>
        property.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
        property.property_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        property.area.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply price filters
    if (filters.minPrice) {
      filtered = filtered.filter(property => property.price_aed >= parseInt(filters.minPrice));
    }
    if (filters.maxPrice) {
      filtered = filtered.filter(property => property.price_aed <= parseInt(filters.maxPrice));
    }

    // Apply bedroom filter
    if (filters.bedrooms !== 'any') {
      filtered = filtered.filter(property => property.bedrooms === parseInt(filters.bedrooms));
    }

    // Apply bathroom filter
    if (filters.bathrooms !== 'any') {
      filtered = filtered.filter(property => property.bathrooms === parseInt(filters.bathrooms));
    }

    // Apply property type filter
    if (filters.propertyType !== 'any') {
      filtered = filtered.filter(property => property.property_type === filters.propertyType);
    }

    // Apply location filter
    if (filters.location !== 'any') {
      filtered = filtered.filter(property => property.area === filters.location);
    }

    // Apply square footage filters
    if (filters.minSqFt) {
      filtered = filtered.filter(property => property.square_feet >= parseInt(filters.minSqFt));
    }
    if (filters.maxSqFt) {
      filtered = filtered.filter(property => property.square_feet <= parseInt(filters.maxSqFt));
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'price':
          return a.price_aed - b.price_aed;
        case 'price-desc':
          return b.price_aed - a.price_aed;
        case 'size':
          return a.square_feet - b.square_feet;
        case 'bedrooms':
          return b.bedrooms - a.bedrooms;
        default:
          return 0;
      }
    });

    setFilteredProperties(filtered);
  }, [properties, filters, searchTerm, sortBy]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      minPrice: '',
      maxPrice: '',
      bedrooms: 'any',
      bathrooms: 'any',
      propertyType: 'any',
      location: 'any',
      minSqFt: '',
      maxSqFt: ''
    });
    setSearchTerm('');
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-AE', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(price);
  };

  const getPropertyIcon = (type) => {
    const icons = {
      'Apartment': '🏢',
      'Villa': '🏡',
      'Townhouse': '🏘️',
      'Penthouse': '🏙️',
      'Studio': '🏠',
      'Duplex': '🏘️'
    };
    return icons[type] || '🏠';
  };

  const getStatusColor = (status) => {
    const colors = {
      'Available': 'success',
      'Under Contract': 'warning',
      'Sold': 'error',
      'Rented': 'primary'
    };
    return colors[status] || 'secondary';
  };

  return (
    <div className="modern-property-container">
      {/* Header */}
      <div className="property-header">
        <div className="header-content">
          <div className="header-title">
            <div className="title-icon">🏠</div>
            <div className="title-text">
              <h1 className="page-title">Property Management</h1>
              <p className="page-subtitle">Search and manage properties with advanced filtering</p>
            </div>
          </div>
          
          <div className="header-actions">
            <div className="view-toggle">
              <button
                className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
                onClick={() => setViewMode('grid')}
                title="Grid view"
              >
                <span className="view-icon">⊞</span>
              </button>
              <button
                className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
                onClick={() => setViewMode('list')}
                title="List view"
              >
                <span className="view-icon">☰</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="filters-section">
        <div className="filters-content">
          {/* Search Bar */}
          <div className="search-container">
            <div className="search-input-wrapper">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                className="search-input"
                placeholder="Search properties by address, type, or area..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          {/* Filter Controls */}
          <div className="filters-grid">
            <div className="filter-group">
              <label className="filter-label">Price Range (AED)</label>
              <div className="price-inputs">
                <input
                  type="number"
                  className="filter-input"
                  placeholder="Min Price"
                  value={filters.minPrice}
                  onChange={(e) => handleFilterChange('minPrice', e.target.value)}
                />
                <span className="price-separator">-</span>
                <input
                  type="number"
                  className="filter-input"
                  placeholder="Max Price"
                  value={filters.maxPrice}
                  onChange={(e) => handleFilterChange('maxPrice', e.target.value)}
                />
              </div>
            </div>

            <div className="filter-group">
              <label className="filter-label">Bedrooms</label>
              <select
                className="filter-select"
                value={filters.bedrooms}
                onChange={(e) => handleFilterChange('bedrooms', e.target.value)}
              >
                <option value="any">Any</option>
                <option value="0">Studio</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4+</option>
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Bathrooms</label>
              <select
                className="filter-select"
                value={filters.bathrooms}
                onChange={(e) => handleFilterChange('bathrooms', e.target.value)}
              >
                <option value="any">Any</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4+</option>
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Property Type</label>
              <select
                className="filter-select"
                value={filters.propertyType}
                onChange={(e) => handleFilterChange('propertyType', e.target.value)}
              >
                <option value="any">Any Type</option>
                {propertyTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Location</label>
              <select
                className="filter-select"
                value={filters.location}
                onChange={(e) => handleFilterChange('location', e.target.value)}
              >
                <option value="any">Any Location</option>
                {locations.map(location => (
                  <option key={location} value={location}>{location}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Square Feet</label>
              <div className="sqft-inputs">
                <input
                  type="number"
                  className="filter-input"
                  placeholder="Min Sq Ft"
                  value={filters.minSqFt}
                  onChange={(e) => handleFilterChange('minSqFt', e.target.value)}
                />
                <span className="sqft-separator">-</span>
                <input
                  type="number"
                  className="filter-input"
                  placeholder="Max Sq Ft"
                  value={filters.maxSqFt}
                  onChange={(e) => handleFilterChange('maxSqFt', e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Filter Actions */}
          <div className="filter-actions">
            <button className="btn btn-primary" onClick={() => {}}>
              <span className="btn-icon">🔍</span>
              Search Properties
            </button>
            <button className="btn btn-secondary" onClick={clearFilters}>
              <span className="btn-icon">🗑️</span>
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Results Header */}
      <div className="results-header">
        <div className="results-info">
          <span className="results-count">
            {filteredProperties.length} properties found
          </span>
        </div>
        
        <div className="sort-controls">
          <label className="sort-label">Sort by:</label>
          <select
            className="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="price">Price (Low to High)</option>
            <option value="price-desc">Price (High to Low)</option>
            <option value="size">Size (Small to Large)</option>
            <option value="bedrooms">Bedrooms (Most)</option>
          </select>
        </div>
      </div>

      {/* Properties Grid/List */}
      <div className={`properties-container ${viewMode}`}>
        {filteredProperties.length === 0 ? (
          <div className="empty-results">
            <div className="empty-icon">🏠</div>
            <h3 className="empty-title">No properties found</h3>
            <p className="empty-description">
              Try adjusting your search criteria or filters
            </p>
          </div>
        ) : (
          <div className={`properties-${viewMode}`}>
            {filteredProperties.map((property, index) => (
              <div key={property.id || index} className="property-card">
                <div className="property-image">
                  <div className="image-placeholder">
                    <span className="property-icon">{getPropertyIcon(property.property_type)}</span>
                  </div>
                  <div className="property-status">
                    <span className={`status-badge badge-${getStatusColor(property.status)}`}>
                      {property.status}
                    </span>
                  </div>
                </div>
                
                <div className="property-content">
                  <div className="property-header">
                    <h3 className="property-title">{property.property_type}</h3>
                    <div className="property-price">{formatPrice(property.price_aed)}</div>
                  </div>
                  
                  <div className="property-location">
                    <span className="location-icon">📍</span>
                    <span className="location-text">{property.area}</span>
                  </div>
                  
                  <div className="property-details">
                    <div className="detail-item">
                      <span className="detail-icon">🛏️</span>
                      <span className="detail-text">{property.bedrooms} beds</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-icon">🚿</span>
                      <span className="detail-text">{property.bathrooms} baths</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-icon">📏</span>
                      <span className="detail-text">{property.square_feet} sq ft</span>
                    </div>
                  </div>
                  
                  <div className="property-amenities">
                    {property.amenities && property.amenities.split(', ').slice(0, 3).map((amenity, idx) => (
                      <span key={idx} className="amenity-tag">{amenity}</span>
                    ))}
                    {property.amenities && property.amenities.split(', ').length > 3 && (
                      <span className="amenity-more">+{property.amenities.split(', ').length - 3} more</span>
                    )}
                  </div>
                  
                  <div className="property-footer">
                    <div className="property-agent">
                      <span className="agent-icon">👤</span>
                      <span className="agent-name">{property.agent}</span>
                    </div>
                    <button className="btn btn-primary btn-sm">
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ModernPropertyManagement;
