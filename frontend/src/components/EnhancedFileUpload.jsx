import React, { useState, useRef, useCallback, useEffect } from 'react';
import './EnhancedFileUpload.css';

const EnhancedFileUpload = ({ onFileUpload, selectedRole, onAnalysisComplete }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState({});
  const [previewData, setPreviewData] = useState({});
  const [selectedFile, setSelectedFile] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const fileInputRef = useRef(null);

  const supportedFormats = ['PDF', 'CSV', 'Excel', 'JSON', 'Images', 'Word', 'Text'];
  const maxFileSize = 10; // MB

  // Helper function to add notifications
  const addNotification = (message, type = 'info') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    
    // Auto-remove notification after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  // Helper function to remove notification
  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  // AI Analysis Types
  const analysisTypes = {
    'image': ['Property Analysis', 'Quality Assessment', 'Location Detection', 'Value Estimation'],
    'pdf': ['Document Analysis', 'Content Extraction', 'Legal Review', 'Property Details'],
    'csv': ['Data Analysis', 'Market Trends', 'Property Comparison', 'Statistical Insights'],
    'excel': ['Spreadsheet Analysis', 'Financial Data', 'Market Reports', 'Investment Analysis'],
    'word': ['Document Review', 'Contract Analysis', 'Legal Compliance', 'Content Summary'],
    'text': ['Text Analysis', 'Sentiment Analysis', 'Key Information', 'Summary Generation']
  };

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  }, []);

  const handleFileSelect = useCallback((e) => {
    const files = Array.from(e.target.files);
    handleFiles(files);
  }, []);

  const handleFiles = async (files) => {
    const validFiles = files.filter(file => {
      const isValidFormat = supportedFormats.some(format => 
        file.type.includes(format.toLowerCase()) || 
        file.name.toLowerCase().endsWith(format.toLowerCase())
      );
      
      const isValidSize = file.size <= maxFileSize * 1024 * 1024;
      
      if (!isValidFormat) {
        addNotification(`Unsupported file format: ${file.name}`, 'error');
      }
      if (!isValidSize) {
        addNotification(`File too large: ${file.name} (max ${maxFileSize}MB)`, 'error');
      }
      
      return isValidFormat && isValidSize;
    });

    if (validFiles.length === 0) return;

    setUploading(true);
    
    // Initialize upload progress for each file
    const newProgress = {};
    validFiles.forEach(file => {
      newProgress[file.name] = 0;
    });
    setUploadProgress(newProgress);

    const uploadedFiles = [];

    // Actually upload files to backend
    for (const file of validFiles) {
      try {
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('file', file);
        
        // Upload file to backend
        const response = await fetch('http://localhost:8001/upload-file', {
          method: 'POST',
          body: formData
        });
        
        if (!response.ok) {
          throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
        }
        
        const uploadResult = await response.json();
        
        // Update progress to 100%
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: 100
        }));
        
        // Add to uploaded files list
        const uploadedFile = {
          id: Date.now() + Math.random(),
          name: file.name,
          size: file.size,
          type: file.type,
          uploadedAt: new Date(),
          status: 'completed',
          analysisStatus: 'pending',
          serverPath: uploadResult.file_path // Store server path
        };
        
        uploadedFiles.push(uploadedFile);
        
        addNotification(`Successfully uploaded ${file.name}`, 'success');
        
      } catch (error) {
        console.error(`Upload failed for ${file.name}:`, error);
        
        // Update progress to show error
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: -1 // -1 indicates error
        }));
        
        addNotification(`Upload failed for ${file.name}: ${error.message}`, 'error');
      }
    }

    // Add successfully uploaded files to the list
    setUploadedFiles(prev => [...prev, ...uploadedFiles]);
    setUploading(false);
    
    // Clear progress after a delay
    setTimeout(() => setUploadProgress({}), 2000);

    // Generate preview data for uploaded files
    await generatePreviews(validFiles);

    // Start AI analysis for uploaded files
    if (uploadedFiles.length > 0) {
      await performAIAnalysis(uploadedFiles);
    }

    // Call the parent upload handler
    if (onFileUpload) {
      onFileUpload(uploadedFiles);
    }
  };

  const generatePreviews = async (files) => {
    const newPreviews = {};
    
    for (const file of files) {
      if (file.type.startsWith('image/')) {
        // Generate image preview
        const reader = new FileReader();
        reader.onload = (e) => {
          newPreviews[file.name] = {
            type: 'image',
            data: e.target.result,
            dimensions: 'Loading...'
          };
          setPreviewData(prev => ({ ...prev, ...newPreviews }));
        };
        reader.readAsDataURL(file);
      } else if (file.type === 'application/pdf') {
        // Generate PDF preview
        newPreviews[file.name] = {
          type: 'pdf',
          data: 'PDF Document',
          pages: 'Loading...'
        };
        setPreviewData(prev => ({ ...prev, ...newPreviews }));
      } else if (file.type.includes('csv') || file.type.includes('excel')) {
        // Generate CSV/Excel preview
        const reader = new FileReader();
        reader.onload = (e) => {
          const content = e.target.result;
          const lines = content.split('\n').slice(0, 5); // First 5 lines
          newPreviews[file.name] = {
            type: 'data',
            data: lines.join('\n'),
            rows: content.split('\n').length
          };
          setPreviewData(prev => ({ ...prev, ...newPreviews }));
        };
        reader.readAsText(file);
      } else {
        // Generate text preview
        const reader = new FileReader();
        reader.onload = (e) => {
          const content = e.target.result;
          newPreviews[file.name] = {
            type: 'text',
            data: content.substring(0, 200) + (content.length > 200 ? '...' : ''),
            length: content.length
          };
          setPreviewData(prev => ({ ...prev, ...newPreviews }));
        };
        reader.readAsText(file);
      }
    }
  };

  const performAIAnalysis = async (files) => {
    setAnalyzing(true);
    
    for (const file of files) {
      try {
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('file', file);
        
        // Call the real backend API
        const response = await fetch('/analyze-file', {
          method: 'POST',
          body: formData
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const analysis = await response.json();
        
        // Store the real analysis results
        setAnalysisResults(prev => ({
          ...prev,
          [file.id]: {
            ...analysis,
            fileId: file.id,
            fileName: file.name,
            analysisDate: new Date()
          }
        }));

        // Update file status to completed
        setUploadedFiles(prev => prev.map(f => 
          f.id === file.id 
            ? { ...f, analysisStatus: 'completed' }
            : f
        ));
        
        console.log(`Analysis completed for ${file.name}:`, analysis);
        
      } catch (error) {
        console.error(`Analysis failed for ${file.name}:`, error);
        
        // Update file status to failed
        setUploadedFiles(prev => prev.map(f => 
          f.id === file.id 
            ? { ...f, analysisStatus: 'failed' }
            : f
        ));
        
        // Show error message to user
        alert(`Analysis failed for ${file.name}: ${error.message}`);
      }
    }
    
    setAnalyzing(false);
    
    // Notify parent component
    if (onAnalysisComplete) {
      onAnalysisComplete(analysisResults);
    }
  };

  const generateMockAnalysis = (file, fileType) => {
    const baseAnalysis = {
      fileId: file.id,
      fileName: file.name,
      fileType: fileType,
      analysisDate: new Date(),
      confidence: Math.random() * 0.3 + 0.7, // 70-100%
      processingTime: Math.random() * 2 + 1, // 1-3 seconds
    };

    switch (fileType) {
      case 'image':
        return {
          ...baseAnalysis,
          analysisType: 'Property Image Analysis',
          results: {
            propertyType: ['Apartment', 'Villa', 'Penthouse'][Math.floor(Math.random() * 3)],
            estimatedValue: `AED ${(Math.random() * 5000000 + 500000).toLocaleString()}`,
            quality: ['Excellent', 'Good', 'Average'][Math.floor(Math.random() * 3)],
            features: ['Balcony', 'Pool View', 'Modern Kitchen', 'Spacious Living Room'].slice(0, Math.floor(Math.random() * 4) + 1),
            location: ['Dubai Marina', 'Downtown Dubai', 'Palm Jumeirah'][Math.floor(Math.random() * 3)],
            recommendations: [
              'High rental yield potential',
              'Strong capital appreciation',
              'Excellent location for investment'
            ]
          }
        };
      
      case 'pdf':
        return {
          ...baseAnalysis,
          analysisType: 'Document Analysis',
          results: {
            documentType: ['Property Contract', 'Legal Document', 'Market Report'][Math.floor(Math.random() * 3)],
            keyExtracted: Math.floor(Math.random() * 10) + 5,
            compliance: ['Compliant', 'Needs Review', 'Non-Compliant'][Math.floor(Math.random() * 3)],
            summary: 'Document contains property details, legal terms, and financial information. All clauses appear standard for Dubai real estate transactions.',
            recommendations: [
              'Review legal clauses carefully',
              'Verify all financial terms',
              'Confirm regulatory compliance'
            ]
          }
        };
      
      case 'csv':
      case 'excel':
        return {
          ...baseAnalysis,
          analysisType: 'Data Analysis',
          results: {
            dataType: ['Property Listings', 'Market Data', 'Financial Records'][Math.floor(Math.random() * 3)],
            records: Math.floor(Math.random() * 1000) + 100,
            insights: [
              'Average property price: AED 2.5M',
              'Price range: AED 500K - 15M',
              'Most popular area: Dubai Marina',
              'Average rental yield: 6.5%'
            ],
            trends: [
              'Prices increasing by 8% annually',
              'High demand for 2-3 bedroom units',
              'Strong investor interest in off-plan projects'
            ]
          }
        };
      
      default:
        return {
          ...baseAnalysis,
          analysisType: 'Content Analysis',
          results: {
            contentType: ['Property Description', 'Market Report', 'Legal Document'][Math.floor(Math.random() * 3)],
            keyPoints: Math.floor(Math.random() * 8) + 3,
            sentiment: ['Positive', 'Neutral', 'Negative'][Math.floor(Math.random() * 3)],
            summary: 'Document contains relevant real estate information with detailed property descriptions and market insights.',
            recommendations: [
              'Use for market research',
              'Include in property analysis',
              'Reference for client discussions'
            ]
          }
        };
    }
  };

  const getFileType = (mimeType, fileName) => {
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType === 'application/pdf') return 'pdf';
    if (mimeType.includes('csv') || fileName.toLowerCase().endsWith('.csv')) return 'csv';
    if (mimeType.includes('excel') || fileName.toLowerCase().endsWith('.xlsx') || fileName.toLowerCase().endsWith('.xls')) return 'excel';
    if (mimeType.includes('word') || fileName.toLowerCase().endsWith('.docx') || fileName.toLowerCase().endsWith('.doc')) return 'word';
    if (mimeType.includes('text/') || fileName.toLowerCase().endsWith('.txt')) return 'text';
    return 'document';
  };

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
    setAnalysisResults(prev => {
      const newResults = { ...prev };
      delete newResults[fileId];
      return newResults;
    });
    setPreviewData(prev => {
      const newPreviews = { ...prev };
      const fileName = uploadedFiles.find(f => f.id === fileId)?.name;
      if (fileName) delete newPreviews[fileName];
      return newPreviews;
    });
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileName, fileType) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('csv') || extension === 'csv') return '📊';
    if (fileType.includes('excel') || extension === 'xlsx' || extension === 'xls') return '📈';
    if (fileType.includes('json') || extension === 'json') return '⚙️';
    if (fileType.includes('image')) return '🖼️';
    if (fileType.includes('word') || extension === 'docx' || extension === 'doc') return '📝';
    if (fileType.includes('text') || extension === 'txt') return '📄';
    
    return '📁';
  };

  const getRoleDescription = (role) => {
    const descriptions = {
      client: 'Upload property preferences, requirements, or documents for AI analysis',
      agent: 'Upload property data, client documents, and market reports for enhanced insights',
      employee: 'Upload company documents, policies, and internal reports for processing',
      admin: 'Upload system configurations, user data, and administrative documents'
    };
    return descriptions[role] || descriptions.client;
  };

  const selectFile = (file) => {
    setSelectedFile(file);
  };

  return (
    <div className="enhanced-file-upload">
      {/* Notifications */}
      <div className="notifications-container">
        {notifications.map(notification => (
          <div 
            key={notification.id} 
            className={`notification notification-${notification.type}`}
            onClick={() => removeNotification(notification.id)}
          >
            <span className="notification-message">{notification.message}</span>
            <button className="notification-close">×</button>
          </div>
        ))}
      </div>

      <div className="upload-container">
        {/* Header */}
        <div className="upload-header">
          <div className="header-content">
            <div className="header-title">
              <div className="title-icon">🤖</div>
              <div className="title-text">
                <h1 className="page-title">AI-Enhanced File Upload</h1>
                <p className="page-subtitle">Upload files for intelligent analysis and insights</p>
              </div>
            </div>
          </div>
        </div>

        <div className="upload-main">
          {/* Left Panel - Upload Area */}
          <div className="upload-panel">
            {/* Upload Zone */}
            <div className="upload-section">
              <div className="upload-content">
                <div
                  className={`upload-zone ${isDragOver ? 'drag-over' : ''} ${uploading ? 'uploading' : ''}`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className="upload-zone-content">
                    <div className="upload-icon">
                      <span className="icon-symbol">🧠</span>
                    </div>
                    
                    <h3 className="upload-title">
                      {uploading ? 'Uploading Files...' : 'AI-Powered File Analysis'}
                    </h3>
                    
                    <p className="upload-description">
                      {uploading 
                        ? 'Please wait while your files are being processed by AI'
                        : 'Drag & drop files here for intelligent analysis and insights'
                      }
                    </p>
                    
                    {!uploading && (
                      <button className="btn btn-primary btn-lg browse-btn">
                        <span className="btn-icon">📂</span>
                        Browse Files
                      </button>
                    )}
                  </div>
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.csv,.xlsx,.xls,.json,.jpg,.jpeg,.png,.gif,.docx,.doc,.txt"
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                  />
                </div>

                {/* File Format Info */}
                <div className="upload-info">
                  <div className="info-section">
                    <h4 className="info-title">AI Analysis Capabilities</h4>
                    <div className="ai-capabilities">
                      <div className="capability-item">
                        <span className="capability-icon">🖼️</span>
                        <span className="capability-text">Image Analysis</span>
                      </div>
                      <div className="capability-item">
                        <span className="capability-icon">📄</span>
                        <span className="capability-text">Document Review</span>
                      </div>
                      <div className="capability-item">
                        <span className="capability-icon">📊</span>
                        <span className="capability-text">Data Insights</span>
                      </div>
                      <div className="capability-item">
                        <span className="capability-icon">💡</span>
                        <span className="capability-text">Smart Recommendations</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Upload Progress */}
                {Object.keys(uploadProgress).length > 0 && (
                  <div className="upload-progress">
                    <h4 className="progress-title">Uploading Files</h4>
                    {Object.entries(uploadProgress).map(([fileName, progress]) => (
                      <div key={fileName} className="progress-item">
                        <div className="progress-info">
                          <span className="progress-filename">{fileName}</span>
                          <span className="progress-percentage">{progress === -1 ? 'Failed' : `${progress}%`}</span>
                        </div>
                        <div className="progress-bar">
                          <div 
                            className="progress-fill"
                            style={{ width: `${progress === -1 ? 100 : progress}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* AI Analysis Progress */}
                {analyzing && (
                  <div className="ai-analysis-progress">
                    <h4 className="progress-title">🤖 AI Analysis in Progress</h4>
                    <div className="analysis-status">
                      <div className="analysis-spinner"></div>
                      <p>Analyzing files with advanced AI algorithms...</p>
                    </div>
                  </div>
                )}

                {/* Uploaded Files List */}
                {uploadedFiles.length > 0 && (
                  <div className="uploaded-files">
                    <div className="files-header">
                      <h4 className="files-title">Uploaded Files</h4>
                      <span className="files-count">{uploadedFiles.length} files</span>
                    </div>
                    
                    <div className="files-list">
                      {uploadedFiles.map(file => (
                        <div 
                          key={file.id} 
                          className={`file-item ${selectedFile?.id === file.id ? 'selected' : ''}`}
                          onClick={() => selectFile(file)}
                        >
                          <div className="file-info">
                            <div className="file-icon">
                              <span className="icon">{getFileIcon(file.name, file.type)}</span>
                            </div>
                            
                            <div className="file-details">
                              <div className="file-name">{file.name}</div>
                              <div className="file-meta">
                                <span className="file-size">{formatFileSize(file.size)}</span>
                                <span className="file-date">
                                  {file.uploadedAt.toLocaleDateString()}
                                </span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="file-actions">
                            <span className={`status-badge badge-${file.status}`}>
                              {file.status}
                            </span>
                            <span className={`analysis-badge badge-${file.analysisStatus}`}>
                              {file.analysisStatus === 'completed' ? '🤖 Analyzed' : 
                               file.analysisStatus === 'pending' ? '⏳ Analyzing' : '❌ Failed'}
                            </span>
                            <button
                              className="btn btn-ghost btn-sm remove-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                removeFile(file.id);
                              }}
                              title="Remove file"
                            >
                              <span className="btn-icon">🗑️</span>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Panel - Preview & Analysis */}
          <div className="preview-panel">
            {selectedFile ? (
              <div className="preview-content">
                <div className="preview-header">
                  <h3 className="preview-title">File Analysis</h3>
                  <span className="preview-filename">{selectedFile.name}</span>
                </div>

                {/* File Preview */}
                <div className="file-preview">
                  <h4 className="preview-section-title">📄 File Preview</h4>
                  <div className="preview-container">
                    {previewData[selectedFile.name] && (
                      <div className="preview-data">
                        {previewData[selectedFile.name].type === 'image' && (
                          <img 
                            src={previewData[selectedFile.name].data} 
                            alt="File preview" 
                            className="image-preview"
                          />
                        )}
                        {previewData[selectedFile.name].type === 'text' && (
                          <div className="text-preview">
                            <pre>{previewData[selectedFile.name].data}</pre>
                          </div>
                        )}
                        {previewData[selectedFile.name].type === 'data' && (
                          <div className="data-preview">
                            <pre>{previewData[selectedFile.name].data}</pre>
                          </div>
                        )}
                        {previewData[selectedFile.name].type === 'pdf' && (
                          <div className="pdf-preview">
                            <div className="pdf-placeholder">
                              <span className="pdf-icon">📄</span>
                              <p>PDF Document</p>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* AI Analysis Results */}
                {analysisResults[selectedFile.id] && (
                  <div className="ai-analysis">
                    <h4 className="preview-section-title">🤖 AI Analysis Results</h4>
                    <div className="analysis-container">
                      <div className="analysis-header">
                        <span className="analysis-type">{analysisResults[selectedFile.id].analysisType}</span>
                        <span className="confidence-score">
                          Confidence: {(analysisResults[selectedFile.id].confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                      
                      <div className="analysis-results">
                        {Object.entries(analysisResults[selectedFile.id].results).map(([key, value]) => (
                          <div key={key} className="result-item">
                            <span className="result-label">{key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}:</span>
                            <span className="result-value">
                              {Array.isArray(value) ? value.join(', ') : value}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Analysis Status */}
                {selectedFile.analysisStatus === 'pending' && (
                  <div className="analysis-pending">
                    <div className="pending-content">
                      <div className="pending-spinner"></div>
                      <p>AI analysis in progress...</p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="preview-placeholder">
                <div className="placeholder-content">
                  <span className="placeholder-icon">📁</span>
                  <h3>Select a file to view analysis</h3>
                  <p>Choose any uploaded file to see AI-powered insights and recommendations</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Role Information */}
        <div className="role-info">
          <div className="role-content">
            <div className="role-header">
              <span className="role-icon">👤</span>
              <span className="role-label">Current Role: {selectedRole.charAt(0).toUpperCase() + selectedRole.slice(1)}</span>
            </div>
            <p className="role-description">{getRoleDescription(selectedRole)}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedFileUpload;
