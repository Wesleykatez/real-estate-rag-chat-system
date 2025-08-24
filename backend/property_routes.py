"""
Property Management Routes for Real Estate RAG Chat System
Provides comprehensive CRUD operations for properties with role-based access control
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from database import get_db
from auth_middleware import get_current_user, require_permission, PermissionChecker
from models import Property, PropertyImage, User, PropertyInquiry, PropertyViewing
import logging

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/properties", tags=["Properties"])

# Pydantic models
class PropertyCreate(BaseModel):
    title: str
    address: str
    description: Optional[str] = None
    property_type: str
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    plot_size: Optional[int] = None
    year_built: Optional[int] = None
    furnished: bool = False
    price: float
    price_per_sqft: Optional[float] = None
    service_charge: Optional[float] = None
    emirate: Optional[str] = None
    area: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[int] = None
    unit_number: Optional[str] = None
    amenities: Optional[List[str]] = []
    features: Optional[List[str]] = []
    parking_spaces: Optional[int] = None
    balcony: bool = False
    is_featured: bool = False
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: Optional[List[str]] = []
    
    @validator('property_type')
    def validate_property_type(cls, v):
        allowed_types = ['apartment', 'villa', 'townhouse', 'penthouse', 'studio', 'duplex', 'land', 'commercial']
        if v.lower() not in allowed_types:
            raise ValueError(f'Property type must be one of: {", ".join(allowed_types)}')
        return v.lower()
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[str] = None
    status: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    plot_size: Optional[int] = None
    year_built: Optional[int] = None
    furnished: Optional[bool] = None
    price: Optional[float] = None
    price_per_sqft: Optional[float] = None
    service_charge: Optional[float] = None
    emirate: Optional[str] = None
    area: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[int] = None
    unit_number: Optional[str] = None
    amenities: Optional[List[str]] = None
    features: Optional[List[str]] = None
    parking_spaces: Optional[int] = None
    balcony: Optional[bool] = None
    is_featured: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: Optional[List[str]] = None

class PropertyResponse(BaseModel):
    id: int
    uuid: str
    title: str
    address: str
    description: Optional[str]
    property_type: str
    status: str
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    square_feet: Optional[int]
    plot_size: Optional[int]
    year_built: Optional[int]
    furnished: bool
    price: float
    price_per_sqft: Optional[float]
    service_charge: Optional[float]
    emirate: Optional[str]
    area: Optional[str]
    building: Optional[str]
    floor: Optional[int]
    unit_number: Optional[str]
    amenities: Optional[List[str]]
    features: Optional[List[str]]
    parking_spaces: Optional[int]
    balcony: bool
    agent_id: Optional[int]
    agent_name: Optional[str]
    is_featured: bool
    views_count: int
    inquiries_count: int
    slug: Optional[str]
    meta_title: Optional[str]
    meta_description: Optional[str]
    keywords: Optional[List[str]]
    listed_at: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    images: List[Dict[str, Any]] = []

class PropertySearchFilters(BaseModel):
    search: Optional[str] = None
    property_type: Optional[str] = None
    status: Optional[str] = None
    emirate: Optional[str] = None
    area: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    min_bathrooms: Optional[float] = None
    max_bathrooms: Optional[float] = None
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None
    furnished: Optional[bool] = None
    balcony: Optional[bool] = None
    parking: Optional[bool] = None
    is_featured: Optional[bool] = None
    agent_id: Optional[int] = None

class PropertyInquiryCreate(BaseModel):
    property_id: int
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    message: str
    inquiry_type: str = "general"

class PropertyViewingCreate(BaseModel):
    property_id: int
    client_id: Optional[int] = None
    scheduled_at: datetime
    duration_minutes: int = 60

# Helper functions
def generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title"""
    import re
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def calculate_price_per_sqft(price: float, square_feet: int) -> float:
    """Calculate price per square foot"""
    if square_feet and square_feet > 0:
        return round(price / square_feet, 2)
    return 0

def build_property_query(db: Session, filters: PropertySearchFilters, current_user: User):
    """Build filtered property query"""
    query = db.query(Property).options(
        joinedload(Property.agent),
        joinedload(Property.images)
    )
    
    # Apply access control
    if not PermissionChecker.can_read_properties(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view properties"
        )
    
    # Agents can only see their own properties unless they're admin
    user_roles = [role.name for role in current_user.roles]
    if "agent" in user_roles and "admin" not in user_roles:
        query = query.filter(Property.agent_id == current_user.id)
    
    # Apply filters
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.filter(
            or_(
                Property.title.ilike(search_term),
                Property.description.ilike(search_term),
                Property.address.ilike(search_term),
                Property.area.ilike(search_term),
                Property.building.ilike(search_term)
            )
        )
    
    if filters.property_type:
        query = query.filter(Property.property_type == filters.property_type)
    
    if filters.status:
        query = query.filter(Property.status == filters.status)
    
    if filters.emirate:
        query = query.filter(Property.emirate == filters.emirate)
    
    if filters.area:
        query = query.filter(Property.area.ilike(f"%{filters.area}%"))
    
    if filters.min_price is not None:
        query = query.filter(Property.price >= filters.min_price)
    
    if filters.max_price is not None:
        query = query.filter(Property.price <= filters.max_price)
    
    if filters.min_bedrooms is not None:
        query = query.filter(Property.bedrooms >= filters.min_bedrooms)
    
    if filters.max_bedrooms is not None:
        query = query.filter(Property.bedrooms <= filters.max_bedrooms)
    
    if filters.min_bathrooms is not None:
        query = query.filter(Property.bathrooms >= filters.min_bathrooms)
    
    if filters.max_bathrooms is not None:
        query = query.filter(Property.bathrooms <= filters.max_bathrooms)
    
    if filters.min_sqft is not None:
        query = query.filter(Property.square_feet >= filters.min_sqft)
    
    if filters.max_sqft is not None:
        query = query.filter(Property.square_feet <= filters.max_sqft)
    
    if filters.furnished is not None:
        query = query.filter(Property.furnished == filters.furnished)
    
    if filters.balcony is not None:
        query = query.filter(Property.balcony == filters.balcony)
    
    if filters.parking is not None:
        if filters.parking:
            query = query.filter(Property.parking_spaces > 0)
        else:
            query = query.filter(or_(Property.parking_spaces == 0, Property.parking_spaces.is_(None)))
    
    if filters.is_featured is not None:
        query = query.filter(Property.is_featured == filters.is_featured)
    
    if filters.agent_id is not None:
        query = query.filter(Property.agent_id == filters.agent_id)
    
    return query

# CRUD endpoints
@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: PropertyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new property"""
    # Check permissions
    if not PermissionChecker.can_create_properties(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create properties"
        )
    
    try:
        # Generate slug
        slug = generate_slug(property_data.title)
        
        # Check if slug exists and make it unique
        existing_slug = db.query(Property).filter(Property.slug == slug).first()
        if existing_slug:
            slug = f"{slug}-{uuid.uuid4().hex[:8]}"
        
        # Calculate price per sqft
        price_per_sqft = None
        if property_data.square_feet:
            price_per_sqft = calculate_price_per_sqft(property_data.price, property_data.square_feet)
        
        # Create property
        property_dict = property_data.dict()
        property_dict.update({
            'agent_id': current_user.id,
            'slug': slug,
            'price_per_sqft': price_per_sqft,
            'status': 'available'
        })
        
        property_obj = Property(**property_dict)
        db.add(property_obj)
        db.commit()
        db.refresh(property_obj)
        
        # Format response
        return PropertyResponse(
            id=property_obj.id,
            uuid=property_obj.uuid,
            title=property_obj.title,
            address=property_obj.address,
            description=property_obj.description,
            property_type=property_obj.property_type,
            status=property_obj.status,
            bedrooms=property_obj.bedrooms,
            bathrooms=property_obj.bathrooms,
            square_feet=property_obj.square_feet,
            plot_size=property_obj.plot_size,
            year_built=property_obj.year_built,
            furnished=property_obj.furnished,
            price=property_obj.price,
            price_per_sqft=property_obj.price_per_sqft,
            service_charge=property_obj.service_charge,
            emirate=property_obj.emirate,
            area=property_obj.area,
            building=property_obj.building,
            floor=property_obj.floor,
            unit_number=property_obj.unit_number,
            amenities=property_obj.amenities or [],
            features=property_obj.features or [],
            parking_spaces=property_obj.parking_spaces,
            balcony=property_obj.balcony,
            agent_id=property_obj.agent_id,
            agent_name=f"{property_obj.agent.first_name} {property_obj.agent.last_name}" if property_obj.agent else None,
            is_featured=property_obj.is_featured,
            views_count=property_obj.views_count,
            inquiries_count=property_obj.inquiries_count,
            slug=property_obj.slug,
            meta_title=property_obj.meta_title,
            meta_description=property_obj.meta_description,
            keywords=property_obj.keywords or [],
            listed_at=property_obj.listed_at,
            created_at=property_obj.created_at,
            updated_at=property_obj.updated_at,
            images=[]
        )
        
    except Exception as e:
        logger.error(f"Error creating property: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create property"
        )

@router.get("/", response_model=Dict[str, Any])
async def list_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|price|title|area|bedrooms|square_feet|views_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    search: Optional[str] = Query(None),
    property_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    emirate: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_bedrooms: Optional[int] = Query(None, ge=0),
    max_bedrooms: Optional[int] = Query(None, ge=0),
    min_bathrooms: Optional[float] = Query(None, ge=0),
    max_bathrooms: Optional[float] = Query(None, ge=0),
    min_sqft: Optional[int] = Query(None, ge=0),
    max_sqft: Optional[int] = Query(None, ge=0),
    furnished: Optional[bool] = Query(None),
    balcony: Optional[bool] = Query(None),
    parking: Optional[bool] = Query(None),
    is_featured: Optional[bool] = Query(None),
    agent_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List properties with advanced filtering and pagination"""
    try:
        # Build filters
        filters = PropertySearchFilters(
            search=search,
            property_type=property_type,
            status=status,
            emirate=emirate,
            area=area,
            min_price=min_price,
            max_price=max_price,
            min_bedrooms=min_bedrooms,
            max_bedrooms=max_bedrooms,
            min_bathrooms=min_bathrooms,
            max_bathrooms=max_bathrooms,
            min_sqft=min_sqft,
            max_sqft=max_sqft,
            furnished=furnished,
            balcony=balcony,
            parking=parking,
            is_featured=is_featured,
            agent_id=agent_id
        )
        
        # Build query
        query = build_property_query(db, filters, current_user)
        
        # Get total count
        total_count = query.count()
        
        # Apply sorting
        sort_column = getattr(Property, sort_by)
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        # Apply pagination
        properties = query.offset(skip).limit(limit).all()
        
        # Format response
        properties_list = []
        for prop in properties:
            # Increment view count
            prop.views_count += 1
            
            properties_list.append(PropertyResponse(
                id=prop.id,
                uuid=prop.uuid,
                title=prop.title,
                address=prop.address,
                description=prop.description,
                property_type=prop.property_type,
                status=prop.status,
                bedrooms=prop.bedrooms,
                bathrooms=prop.bathrooms,
                square_feet=prop.square_feet,
                plot_size=prop.plot_size,
                year_built=prop.year_built,
                furnished=prop.furnished,
                price=prop.price,
                price_per_sqft=prop.price_per_sqft,
                service_charge=prop.service_charge,
                emirate=prop.emirate,
                area=prop.area,
                building=prop.building,
                floor=prop.floor,
                unit_number=prop.unit_number,
                amenities=prop.amenities or [],
                features=prop.features or [],
                parking_spaces=prop.parking_spaces,
                balcony=prop.balcony,
                agent_id=prop.agent_id,
                agent_name=f"{prop.agent.first_name} {prop.agent.last_name}" if prop.agent else None,
                is_featured=prop.is_featured,
                views_count=prop.views_count,
                inquiries_count=prop.inquiries_count,
                slug=prop.slug,
                meta_title=prop.meta_title,
                meta_description=prop.meta_description,
                keywords=prop.keywords or [],
                listed_at=prop.listed_at,
                created_at=prop.created_at,
                updated_at=prop.updated_at,
                images=[
                    {
                        "id": img.id,
                        "filename": img.filename,
                        "file_path": img.file_path,
                        "is_primary": img.is_primary,
                        "order": img.order,
                        "alt_text": img.alt_text
                    }
                    for img in prop.images
                ]
            ))
        
        db.commit()  # Commit view count updates
        
        return {
            "properties": properties_list,
            "pagination": {
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "pages": (total_count + limit - 1) // limit
            },
            "filters": filters.dict(),
            "sort": {
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing properties: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve properties"
        )

@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific property by ID"""
    try:
        # Check permissions
        if not PermissionChecker.can_read_properties(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view properties"
            )
        
        # Get property
        property_obj = db.query(Property).options(
            joinedload(Property.agent),
            joinedload(Property.images)
        ).filter(Property.id == property_id).first()
        
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Check if agent can view this property
        user_roles = [role.name for role in current_user.roles]
        if "agent" in user_roles and "admin" not in user_roles:
            if property_obj.agent_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own properties"
                )
        
        # Increment view count
        property_obj.views_count += 1
        db.commit()
        
        return PropertyResponse(
            id=property_obj.id,
            uuid=property_obj.uuid,
            title=property_obj.title,
            address=property_obj.address,
            description=property_obj.description,
            property_type=property_obj.property_type,
            status=property_obj.status,
            bedrooms=property_obj.bedrooms,
            bathrooms=property_obj.bathrooms,
            square_feet=property_obj.square_feet,
            plot_size=property_obj.plot_size,
            year_built=property_obj.year_built,
            furnished=property_obj.furnished,
            price=property_obj.price,
            price_per_sqft=property_obj.price_per_sqft,
            service_charge=property_obj.service_charge,
            emirate=property_obj.emirate,
            area=property_obj.area,
            building=property_obj.building,
            floor=property_obj.floor,
            unit_number=property_obj.unit_number,
            amenities=property_obj.amenities or [],
            features=property_obj.features or [],
            parking_spaces=property_obj.parking_spaces,
            balcony=property_obj.balcony,
            agent_id=property_obj.agent_id,
            agent_name=f"{property_obj.agent.first_name} {property_obj.agent.last_name}" if property_obj.agent else None,
            is_featured=property_obj.is_featured,
            views_count=property_obj.views_count,
            inquiries_count=property_obj.inquiries_count,
            slug=property_obj.slug,
            meta_title=property_obj.meta_title,
            meta_description=property_obj.meta_description,
            keywords=property_obj.keywords or [],
            listed_at=property_obj.listed_at,
            created_at=property_obj.created_at,
            updated_at=property_obj.updated_at,
            images=[
                {
                    "id": img.id,
                    "filename": img.filename,
                    "file_path": img.file_path,
                    "is_primary": img.is_primary,
                    "order": img.order,
                    "alt_text": img.alt_text
                }
                for img in property_obj.images
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting property {property_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve property"
        )

@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a property"""
    try:
        # Get property
        property_obj = db.query(Property).options(
            joinedload(Property.agent),
            joinedload(Property.images)
        ).filter(Property.id == property_id).first()
        
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Check permissions
        if not PermissionChecker.can_edit_properties(current_user, property_obj.agent_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this property"
            )
        
        # Update property fields
        update_data = property_data.dict(exclude_unset=True)
        
        # Recalculate price per sqft if price or square_feet changed
        if 'price' in update_data or 'square_feet' in update_data:
            new_price = update_data.get('price', property_obj.price)
            new_sqft = update_data.get('square_feet', property_obj.square_feet)
            if new_sqft:
                update_data['price_per_sqft'] = calculate_price_per_sqft(new_price, new_sqft)
        
        # Update slug if title changed
        if 'title' in update_data:
            new_slug = generate_slug(update_data['title'])
            existing_slug = db.query(Property).filter(
                and_(Property.slug == new_slug, Property.id != property_id)
            ).first()
            if existing_slug:
                new_slug = f"{new_slug}-{uuid.uuid4().hex[:8]}"
            update_data['slug'] = new_slug
        
        for field, value in update_data.items():
            setattr(property_obj, field, value)
        
        property_obj.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(property_obj)
        
        return PropertyResponse(
            id=property_obj.id,
            uuid=property_obj.uuid,
            title=property_obj.title,
            address=property_obj.address,
            description=property_obj.description,
            property_type=property_obj.property_type,
            status=property_obj.status,
            bedrooms=property_obj.bedrooms,
            bathrooms=property_obj.bathrooms,
            square_feet=property_obj.square_feet,
            plot_size=property_obj.plot_size,
            year_built=property_obj.year_built,
            furnished=property_obj.furnished,
            price=property_obj.price,
            price_per_sqft=property_obj.price_per_sqft,
            service_charge=property_obj.service_charge,
            emirate=property_obj.emirate,
            area=property_obj.area,
            building=property_obj.building,
            floor=property_obj.floor,
            unit_number=property_obj.unit_number,
            amenities=property_obj.amenities or [],
            features=property_obj.features or [],
            parking_spaces=property_obj.parking_spaces,
            balcony=property_obj.balcony,
            agent_id=property_obj.agent_id,
            agent_name=f"{property_obj.agent.first_name} {property_obj.agent.last_name}" if property_obj.agent else None,
            is_featured=property_obj.is_featured,
            views_count=property_obj.views_count,
            inquiries_count=property_obj.inquiries_count,
            slug=property_obj.slug,
            meta_title=property_obj.meta_title,
            meta_description=property_obj.meta_description,
            keywords=property_obj.keywords or [],
            listed_at=property_obj.listed_at,
            created_at=property_obj.created_at,
            updated_at=property_obj.updated_at,
            images=[
                {
                    "id": img.id,
                    "filename": img.filename,
                    "file_path": img.file_path,
                    "is_primary": img.is_primary,
                    "order": img.order,
                    "alt_text": img.alt_text
                }
                for img in property_obj.images
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating property {property_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update property"
        )

@router.delete("/{property_id}")
async def delete_property(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a property"""
    try:
        # Get property
        property_obj = db.query(Property).filter(Property.id == property_id).first()
        
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Check permissions
        if not PermissionChecker.can_delete_properties(current_user, property_obj.agent_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this property"
            )
        
        # Delete property (cascade will handle related records)
        db.delete(property_obj)
        db.commit()
        
        return {"message": "Property deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting property {property_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete property"
        )

# Property inquiry endpoints
@router.post("/{property_id}/inquiries", status_code=status.HTTP_201_CREATED)
async def create_property_inquiry(
    property_id: int,
    inquiry_data: PropertyInquiryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a property inquiry"""
    try:
        # Check if property exists
        property_obj = db.query(Property).filter(Property.id == property_id).first()
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Create inquiry
        inquiry = PropertyInquiry(
            property_id=property_id,
            contact_name=inquiry_data.contact_name,
            contact_email=inquiry_data.contact_email,
            contact_phone=inquiry_data.contact_phone,
            message=inquiry_data.message,
            inquiry_type=inquiry_data.inquiry_type,
            source="web_form"
        )
        
        db.add(inquiry)
        
        # Increment inquiries count
        property_obj.inquiries_count += 1
        
        db.commit()
        
        return {"message": "Inquiry submitted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating inquiry for property {property_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit inquiry"
        )

# Property analytics endpoints
@router.get("/{property_id}/analytics")
async def get_property_analytics(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get property analytics"""
    try:
        # Get property
        property_obj = db.query(Property).filter(Property.id == property_id).first()
        
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Check permissions
        if not PermissionChecker.can_edit_properties(current_user, property_obj.agent_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view analytics for this property"
            )
        
        # Get analytics data
        inquiries_count = db.query(PropertyInquiry).filter(
            PropertyInquiry.property_id == property_id
        ).count()
        
        viewings_count = db.query(PropertyViewing).filter(
            PropertyViewing.property_id == property_id
        ).count()
        
        return {
            "property_id": property_id,
            "views_count": property_obj.views_count,
            "inquiries_count": inquiries_count,
            "viewings_count": viewings_count,
            "days_on_market": (datetime.utcnow() - property_obj.listed_at).days,
            "price_per_sqft": property_obj.price_per_sqft,
            "status": property_obj.status,
            "is_featured": property_obj.is_featured
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics for property {property_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )