#!/usr/bin/env python3
"""
Database Initialization Script for Real Estate RAG Chat System
Sets up the database with tables, default roles, permissions, and sample data
"""

import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_database, get_database_info, check_database_connection
from models import Base, User, Role, Property
from auth_service import AuthService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_users(db_session):
    """Create sample users for testing"""
    auth_service = AuthService(db_session)
    
    sample_users = [
        {
            "email": "demo.admin@example.com",
            "username": "demo_admin",
            "password": "demo123",
            "first_name": "Admin",
            "last_name": "User",
            "phone": "+971501234567",
            "role": "admin",
            "company": "Real Estate Solutions",
            "job_title": "System Administrator"
        },
        {
            "email": "demo.agent@example.com",
            "username": "demo_agent",
            "password": "demo123",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "phone": "+971501234568",
            "role": "agent",
            "company": "Dubai Properties",
            "job_title": "Senior Real Estate Agent",
            "license_number": "RERA123456"
        },
        {
            "email": "demo.employee@example.com",
            "username": "demo_employee",
            "password": "demo123",
            "first_name": "Michael",
            "last_name": "Chen",
            "phone": "+971501234569",
            "role": "employee",
            "company": "Real Estate Solutions",
            "job_title": "Property Manager"
        },
        {
            "email": "demo.client@example.com",
            "username": "demo_client",
            "password": "demo123",
            "first_name": "Ahmed",
            "last_name": "Al Mansouri",
            "phone": "+971501234570",
            "role": "client"
        }
    ]
    
    created_users = []
    for user_data in sample_users:
        try:
            # Check if user already exists
            existing_user = db_session.query(User).filter(User.email == user_data["email"]).first()
            if existing_user:
                logger.info(f"User {user_data['email']} already exists, skipping...")
                created_users.append(existing_user)
                continue
            
            result = auth_service.register_user(user_data, user_data["role"])
            logger.info(f"Created user: {user_data['email']} with role: {user_data['role']}")
            
            # Get the created user
            user = db_session.query(User).filter(User.email == user_data["email"]).first()
            created_users.append(user)
            
        except Exception as e:
            logger.error(f"Error creating user {user_data['email']}: {str(e)}")
    
    return created_users

def create_sample_properties(db_session, users):
    """Create sample properties"""
    # Find an agent user
    agent_user = None
    for user in users:
        if any(role.name == 'agent' for role in user.roles):
            agent_user = user
            break
    
    if not agent_user:
        logger.warning("No agent user found, skipping property creation")
        return []
    
    sample_properties = [
        {
            "title": "Luxury 2BR Apartment in Downtown Dubai",
            "address": "Building 123, Floor 15, Unit 1501, Downtown Dubai, Dubai, UAE",
            "description": "Experience the pinnacle of urban living in this stunning 2-bedroom apartment located in the heart of Downtown Dubai. This meticulously designed residence offers breathtaking city views and premium finishes throughout.",
            "property_type": "apartment",
            "bedrooms": 2,
            "bathrooms": 2.0,
            "square_feet": 1200,
            "year_built": 2023,
            "furnished": True,
            "price": 2500000.00,
            "service_charge": 15000.00,
            "emirate": "Dubai",
            "area": "Downtown Dubai",
            "building": "Building 123",
            "floor": 15,
            "unit_number": "1501",
            "amenities": ["Swimming Pool", "Gym", "Spa", "Tennis Court", "Children's Playground", "BBQ Area", "Garden", "Balcony", "Parking", "Security", "Concierge", "24/7 Maintenance"],
            "features": ["City View", "Central AC", "Built-in Wardrobes", "Modern Kitchen", "Walk-in Closet"],
            "parking_spaces": 1,
            "balcony": True,
            "agent_id": agent_user.id,
            "is_featured": True,
            "meta_title": "Luxury 2BR Apartment Downtown Dubai - Premium Living",
            "meta_description": "Stunning 2-bedroom apartment in Downtown Dubai with city views, premium amenities, and modern finishes. Perfect for luxury living in the heart of the city.",
            "keywords": ["Downtown Dubai", "Luxury Apartment", "2 Bedroom", "City View", "Premium"]
        },
        {
            "title": "Spectacular 3BR Marina Apartment with Sea View",
            "address": "Building 456, Floor 25, Unit 2503, Dubai Marina, Dubai, UAE",
            "description": "Indulge in waterfront luxury with this exceptional 3-bedroom apartment in Dubai Marina. Featuring panoramic sea views and world-class amenities, this residence epitomizes sophisticated coastal living.",
            "property_type": "apartment",
            "bedrooms": 3,
            "bathrooms": 3.0,
            "square_feet": 1800,
            "year_built": 2023,
            "furnished": False,
            "price": 3200000.00,
            "service_charge": 20000.00,
            "emirate": "Dubai",
            "area": "Dubai Marina",
            "building": "Building 456",
            "floor": 25,
            "unit_number": "2503",
            "amenities": ["Swimming Pool", "Gym", "Spa", "Tennis Court", "Basketball Court", "Children's Playground", "BBQ Area", "Garden", "Balcony", "Terrace", "Parking", "Security", "Concierge", "24/7 Maintenance", "Pet Friendly"],
            "features": ["Sea View", "Marina View", "Central AC", "Built-in Wardrobes", "Modern Kitchen", "Walk-in Closet", "Study Room"],
            "parking_spaces": 2,
            "balcony": True,
            "agent_id": agent_user.id,
            "status": "under_contract",
            "is_featured": True,
            "meta_title": "3BR Marina Apartment Sea View - Waterfront Luxury",
            "meta_description": "Exceptional 3-bedroom apartment in Dubai Marina with panoramic sea views and premium amenities. Sophisticated coastal living at its finest.",
            "keywords": ["Dubai Marina", "Sea View", "3 Bedroom", "Waterfront", "Luxury"]
        },
        {
            "title": "Exclusive 5BR Villa on Palm Jumeirah",
            "address": "Villa 789, Palm Jumeirah, Dubai, UAE",
            "description": "Discover unparalleled luxury in this magnificent 5-bedroom villa on the iconic Palm Jumeirah. This architectural masterpiece offers direct beach access, private pool, and stunning sea views in one of Dubai's most prestigious locations.",
            "property_type": "villa",
            "bedrooms": 5,
            "bathrooms": 6.0,
            "square_feet": 4500,
            "plot_size": 8000,
            "year_built": 2022,
            "furnished": True,
            "price": 8500000.00,
            "service_charge": 35000.00,
            "emirate": "Dubai",
            "area": "Palm Jumeirah",
            "amenities": ["Private Pool", "Private Beach", "Gym", "Spa", "Tennis Court", "Basketball Court", "Children's Playground", "BBQ Area", "Garden", "Balcony", "Terrace", "Parking", "Security", "Concierge", "24/7 Maintenance", "Pet Friendly", "Central AC", "Furnished", "Built-in Wardrobes", "Modern Kitchen", "Walk-in Closet", "Study Room", "Maid's Room", "Driver's Room"],
            "features": ["Sea View", "Beach Access", "Private Pool", "Garden", "Premium Finishes", "Smart Home", "Wine Cellar", "Home Theater"],
            "parking_spaces": 4,
            "balcony": True,
            "agent_id": agent_user.id,
            "is_featured": True,
            "meta_title": "Exclusive 5BR Villa Palm Jumeirah - Beachfront Luxury",
            "meta_description": "Magnificent 5-bedroom villa on Palm Jumeirah with private beach access, pool, and stunning sea views. Ultimate luxury living in Dubai's most prestigious location.",
            "keywords": ["Palm Jumeirah", "Villa", "5 Bedroom", "Private Beach", "Luxury", "Sea View"]
        },
        {
            "title": "Modern 1BR Studio in Business Bay",
            "address": "Tower ABC, Floor 20, Unit 2001, Business Bay, Dubai, UAE",
            "description": "Perfect for professionals and investors, this contemporary 1-bedroom studio in Business Bay offers modern living with stunning canal views and excellent connectivity to Dubai's business district.",
            "property_type": "studio",
            "bedrooms": 1,
            "bathrooms": 1.0,
            "square_feet": 700,
            "year_built": 2024,
            "furnished": False,
            "price": 1200000.00,
            "service_charge": 8000.00,
            "emirate": "Dubai",
            "area": "Business Bay",
            "building": "Tower ABC",
            "floor": 20,
            "unit_number": "2001",
            "amenities": ["Swimming Pool", "Gym", "Business Center", "Parking", "Security", "Concierge", "24/7 Maintenance"],
            "features": ["Canal View", "Central AC", "Built-in Wardrobes", "Modern Kitchen", "High Ceilings"],
            "parking_spaces": 1,
            "balcony": True,
            "agent_id": agent_user.id,
            "is_featured": False,
            "meta_title": "Modern 1BR Studio Business Bay - Investment Opportunity",
            "meta_description": "Contemporary studio apartment in Business Bay with canal views. Perfect for professionals and investors seeking modern urban living.",
            "keywords": ["Business Bay", "Studio", "Investment", "Canal View", "Modern"]
        },
        {
            "title": "Spacious 4BR Townhouse in Dubai Hills Estate",
            "address": "Townhouse 101, Dubai Hills Estate, Dubai, UAE",
            "description": "Embrace family living in this spacious 4-bedroom townhouse in the prestigious Dubai Hills Estate. Featuring a private garden, community amenities, and golf course views, this home offers the perfect blend of luxury and comfort.",
            "property_type": "townhouse",
            "bedrooms": 4,
            "bathrooms": 4.0,
            "square_feet": 2800,
            "plot_size": 3500,
            "year_built": 2023,
            "furnished": False,
            "price": 4200000.00,
            "service_charge": 25000.00,
            "emirate": "Dubai",
            "area": "Dubai Hills Estate",
            "amenities": ["Community Pool", "Golf Course", "Gym", "Tennis Court", "Children's Playground", "BBQ Area", "Garden", "Parking", "Security", "24/7 Maintenance", "Pet Friendly"],
            "features": ["Golf Course View", "Private Garden", "Central AC", "Built-in Wardrobes", "Modern Kitchen", "Walk-in Closet", "Study Room", "Maid's Room"],
            "parking_spaces": 2,
            "balcony": False,
            "agent_id": agent_user.id,
            "is_featured": False,
            "meta_title": "Spacious 4BR Townhouse Dubai Hills Estate - Family Living",
            "meta_description": "Beautiful 4-bedroom townhouse in Dubai Hills Estate with golf course views and private garden. Perfect for family living in a prestigious community.",
            "keywords": ["Dubai Hills Estate", "Townhouse", "4 Bedroom", "Golf Course", "Family", "Garden"]
        }
    ]
    
    created_properties = []
    for prop_data in sample_properties:
        try:
            # Check if property already exists
            existing_property = db_session.query(Property).filter(Property.title == prop_data["title"]).first()
            if existing_property:
                logger.info(f"Property '{prop_data['title']}' already exists, skipping...")
                created_properties.append(existing_property)
                continue
            
            # Calculate price per sqft
            if prop_data.get("square_feet"):
                prop_data["price_per_sqft"] = round(prop_data["price"] / prop_data["square_feet"], 2)
            
            # Generate slug
            import re
            slug = re.sub(r'[^\w\s-]', '', prop_data["title"].lower())
            slug = re.sub(r'[-\s]+', '-', slug)
            prop_data["slug"] = slug.strip('-')
            
            property_obj = Property(**prop_data)
            db_session.add(property_obj)
            db_session.commit()
            db_session.refresh(property_obj)
            
            created_properties.append(property_obj)
            logger.info(f"Created property: {prop_data['title']}")
            
        except Exception as e:
            logger.error(f"Error creating property '{prop_data['title']}': {str(e)}")
            db_session.rollback()
    
    return created_properties

def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")
    
    # Check database connection
    if not check_database_connection():
        logger.error("Database connection failed. Please check your database configuration.")
        return False
    
    try:
        # Initialize database (create tables, roles, permissions)
        logger.info("Initializing database tables and default data...")
        init_database()
        
        # Create database session
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password123@localhost:5432/real_estate_db")
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db_session = SessionLocal()
        
        try:
            # Create sample users
            logger.info("Creating sample users...")
            users = create_sample_users(db_session)
            
            # Create sample properties
            logger.info("Creating sample properties...")
            properties = create_sample_properties(db_session, users)
            
            # Get database info
            db_info = get_database_info()
            
            logger.info("Database initialization completed successfully!")
            logger.info(f"Database Status: {db_info['status']}")
            logger.info(f"Tables Created: {db_info.get('table_count', 0)}")
            logger.info(f"Sample Users Created: {len(users)}")
            logger.info(f"Sample Properties Created: {len(properties)}")
            
            # Print login credentials
            print("\n" + "="*60)
            print("SAMPLE USER CREDENTIALS")
            print("="*60)
            print("Admin User:")
            print("  Email: demo.admin@example.com")
            print("  Password: demo123")
            print("\nAgent User:")
            print("  Email: demo.agent@example.com")
            print("  Password: demo123")
            print("\nEmployee User:")
            print("  Email: demo.employee@example.com")
            print("  Password: demo123")
            print("\nClient User:")
            print("  Email: demo.client@example.com")
            print("  Password: demo123")
            print("="*60)
            
            return True
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)