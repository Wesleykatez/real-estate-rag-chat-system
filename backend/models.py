"""
Database Models for Real Estate RAG Chat System
Includes User Authentication, Property Management, Client Management, and Task Management
"""

from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, Boolean, ForeignKey, Table, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

# Association tables for many-to-many relationships
user_roles = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

role_permissions = Table('role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

# User Authentication Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50))
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Profile information
    company = Column(String(255))
    job_title = Column(String(100))
    license_number = Column(String(100))
    bio = Column(Text)
    preferences = Column(JSON)  # User preferences as JSON
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user")
    properties = relationship("Property", back_populates="agent")
    clients = relationship("Client", back_populates="agent")
    tasks_assigned = relationship("Task", foreign_keys="[Task.assigned_to]", back_populates="assignee")
    tasks_created = relationship("Task", foreign_keys="[Task.created_by]", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # client, agent, employee, admin
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # e.g., 'read_properties', 'create_clients'
    resource = Column(String(50), nullable=False)  # e.g., 'properties', 'clients', 'tasks'
    action = Column(String(50), nullable=False)  # e.g., 'create', 'read', 'update', 'delete'
    description = Column(Text)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False)
    device_info = Column(JSON)  # Browser, OS, etc.
    ip_address = Column(String(45))  # IPv4 or IPv6
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")

class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reset_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")

# Property Management Models
class Property(Base):
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    property_type = Column(String(100), nullable=False)  # apartment, villa, townhouse, etc.
    status = Column(String(50), default='available')  # available, sold, under_contract, off_market
    
    # Property details
    bedrooms = Column(Integer)
    bathrooms = Column(Numeric(3, 1))
    square_feet = Column(Integer)
    plot_size = Column(Integer)
    year_built = Column(Integer)
    furnished = Column(Boolean, default=False)
    
    # Pricing
    price = Column(Numeric(12, 2), nullable=False)
    price_per_sqft = Column(Numeric(8, 2))
    service_charge = Column(Numeric(10, 2))
    
    # Location details
    emirate = Column(String(100))
    area = Column(String(100))
    building = Column(String(255))
    floor = Column(Integer)
    unit_number = Column(String(50))
    
    # Features
    amenities = Column(JSON)  # List of amenities
    features = Column(JSON)  # Property features
    parking_spaces = Column(Integer)
    balcony = Column(Boolean, default=False)
    
    # SEO and marketing
    slug = Column(String(255), unique=True, index=True)
    meta_title = Column(String(255))
    meta_description = Column(Text)
    keywords = Column(JSON)
    
    # Management
    agent_id = Column(Integer, ForeignKey('users.id'))
    is_featured = Column(Boolean, default=False)
    views_count = Column(Integer, default=0)
    inquiries_count = Column(Integer, default=0)
    
    # Timestamps
    listed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    agent = relationship("User", back_populates="properties")
    images = relationship("PropertyImage", back_populates="property", cascade="all, delete-orphan")
    inquiries = relationship("PropertyInquiry", back_populates="property")
    viewings = relationship("PropertyViewing", back_populates="property")
    
    # Indexes
    __table_args__ = (
        Index('idx_property_location', 'emirate', 'area'),
        Index('idx_property_price', 'price'),
        Index('idx_property_status', 'status'),
        Index('idx_property_type', 'property_type'),
    )

class PropertyImage(Base):
    __tablename__ = "property_images"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey('properties.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    width = Column(Integer)
    height = Column(Integer)
    is_primary = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    alt_text = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    property = relationship("Property", back_populates="images")

# Client Management Models
class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(50))
    
    # Demographics
    nationality = Column(String(100))
    age_range = Column(String(50))  # 25-35, 35-45, etc.
    occupation = Column(String(255))
    annual_income = Column(String(100))
    
    # Preferences
    budget_min = Column(Numeric(12, 2))
    budget_max = Column(Numeric(12, 2))
    preferred_locations = Column(JSON)  # List of preferred areas
    property_types = Column(JSON)  # List of preferred property types
    bedrooms_min = Column(Integer)
    bedrooms_max = Column(Integer)
    requirements = Column(Text)
    
    # Lead information
    lead_source = Column(String(100))  # website, chat, referral, etc.
    lead_status = Column(String(50), default='new')  # new, qualified, interested, viewing, negotiating, closed, lost
    lead_score = Column(Integer, default=0)  # 0-100 scoring system
    interest_level = Column(String(50))  # low, medium, high
    
    # Assignment
    agent_id = Column(Integer, ForeignKey('users.id'))
    assigned_at = Column(DateTime(timezone=True))
    
    # Notes and tags
    notes = Column(Text)
    tags = Column(JSON)  # List of tags
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_contact = Column(DateTime(timezone=True))
    
    # Relationships
    agent = relationship("User", back_populates="clients")
    interactions = relationship("ClientInteraction", back_populates="client")
    inquiries = relationship("PropertyInquiry", back_populates="client")
    viewings = relationship("PropertyViewing", back_populates="client")

class ClientInteraction(Base):
    __tablename__ = "client_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    interaction_type = Column(String(50), nullable=False)  # call, email, meeting, chat, viewing
    subject = Column(String(255))
    notes = Column(Text)
    duration_minutes = Column(Integer)  # For calls and meetings
    outcome = Column(String(100))  # successful, no_answer, follow_up_needed, etc.
    follow_up_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="interactions")
    user = relationship("User")

class PropertyInquiry(Base):
    __tablename__ = "property_inquiries"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey('properties.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'))
    
    # Inquiry details
    contact_name = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    message = Column(Text)
    inquiry_type = Column(String(50))  # general, viewing, pricing, financing
    
    # Response
    responded = Column(Boolean, default=False)
    responded_at = Column(DateTime(timezone=True))
    responded_by = Column(Integer, ForeignKey('users.id'))
    response_message = Column(Text)
    
    # Source
    source = Column(String(100))  # website, chat, phone, email
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    property = relationship("Property", back_populates="inquiries")
    client = relationship("Client", back_populates="inquiries")
    responder = relationship("User")

class PropertyViewing(Base):
    __tablename__ = "property_viewings"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey('properties.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    agent_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Viewing details
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=60)
    status = Column(String(50), default='scheduled')  # scheduled, confirmed, completed, cancelled, no_show
    
    # Feedback
    client_feedback = Column(Text)
    agent_notes = Column(Text)
    interest_level = Column(String(50))  # low, medium, high
    follow_up_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    property = relationship("Property", back_populates="viewings")
    client = relationship("Client", back_populates="viewings")
    agent = relationship("User")

# Task Management Models
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    task_type = Column(String(50))  # follow_up, viewing, call, email, meeting
    priority = Column(String(20), default='medium')  # low, medium, high, urgent
    status = Column(String(50), default='pending')  # pending, in_progress, completed, cancelled
    
    # Assignment
    assigned_to = Column(Integer, ForeignKey('users.id'))
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    client_id = Column(Integer, ForeignKey('clients.id'))
    property_id = Column(Integer, ForeignKey('properties.id'))
    
    # Timing
    due_date = Column(DateTime(timezone=True))
    reminder_date = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Source information
    source = Column(String(100))  # chat, manual, system, api
    source_data = Column(JSON)  # Additional source information
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="tasks_assigned")
    creator = relationship("User", foreign_keys=[created_by], back_populates="tasks_created")
    client = relationship("Client")
    property = relationship("Property")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")

class TaskComment(Base):
    __tablename__ = "task_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="comments")
    user = relationship("User")

# Conversation and Chat Models
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(String(50), nullable=False)  # client, agent, employee, admin
    title = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default='text')  # text, file, image, system
    metadata = Column(JSON)  # Additional message metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

# Analytics and Audit Models
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)  # login, logout, create, update, delete
    resource_type = Column(String(50))  # user, property, client, task
    resource_id = Column(String(100))  # ID of the affected resource
    details = Column(JSON)  # Additional details about the action
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_timestamp', 'timestamp'),
    )

class SystemMetric(Base):
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Numeric(12, 4))
    metric_data = Column(JSON)  # Additional metric data
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_metric_name_timestamp', 'metric_name', 'timestamp'),
    )