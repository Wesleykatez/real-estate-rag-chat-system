"""
Database configuration and initialization for Real Estate RAG Chat System
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from models import Base, Role, Permission

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:password123@localhost:5432/real_estate_db"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def init_database():
    """Initialize database with default data"""
    try:
        # Create tables
        create_tables()
        
        # Create default roles and permissions
        db = SessionLocal()
        try:
            init_roles_and_permissions(db)
            logger.info("Database initialized successfully")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def init_roles_and_permissions(db: Session):
    """Initialize default roles and permissions"""
    
    # Define permissions
    permissions_data = [
        # Property permissions
        {"name": "read_properties", "resource": "properties", "action": "read", "description": "View properties"},
        {"name": "create_properties", "resource": "properties", "action": "create", "description": "Create new properties"},
        {"name": "update_properties", "resource": "properties", "action": "update", "description": "Update properties"},
        {"name": "delete_properties", "resource": "properties", "action": "delete", "description": "Delete properties"},
        {"name": "manage_properties", "resource": "properties", "action": "manage", "description": "Full property management"},
        
        # Client permissions
        {"name": "read_clients", "resource": "clients", "action": "read", "description": "View clients"},
        {"name": "create_clients", "resource": "clients", "action": "create", "description": "Create new clients"},
        {"name": "update_clients", "resource": "clients", "action": "update", "description": "Update clients"},
        {"name": "delete_clients", "resource": "clients", "action": "delete", "description": "Delete clients"},
        {"name": "manage_clients", "resource": "clients", "action": "manage", "description": "Full client management"},
        
        # Task permissions
        {"name": "read_tasks", "resource": "tasks", "action": "read", "description": "View tasks"},
        {"name": "create_tasks", "resource": "tasks", "action": "create", "description": "Create new tasks"},
        {"name": "update_tasks", "resource": "tasks", "action": "update", "description": "Update tasks"},
        {"name": "delete_tasks", "resource": "tasks", "action": "delete", "description": "Delete tasks"},
        {"name": "assign_tasks", "resource": "tasks", "action": "assign", "description": "Assign tasks to users"},
        
        # User permissions
        {"name": "read_users", "resource": "users", "action": "read", "description": "View users"},
        {"name": "create_users", "resource": "users", "action": "create", "description": "Create new users"},
        {"name": "update_users", "resource": "users", "action": "update", "description": "Update users"},
        {"name": "delete_users", "resource": "users", "action": "delete", "description": "Delete users"},
        {"name": "manage_users", "resource": "users", "action": "manage", "description": "Full user management"},
        
        # Analytics permissions
        {"name": "view_analytics", "resource": "analytics", "action": "read", "description": "View analytics"},
        {"name": "export_analytics", "resource": "analytics", "action": "export", "description": "Export analytics data"},
        
        # System permissions
        {"name": "admin_access", "resource": "system", "action": "admin", "description": "Administrative access"},
        {"name": "system_config", "resource": "system", "action": "config", "description": "System configuration"},
        
        # Chat permissions
        {"name": "chat_access", "resource": "chat", "action": "read", "description": "Access chat system"},
        {"name": "chat_history", "resource": "chat", "action": "history", "description": "View chat history"},
        
        # File permissions
        {"name": "upload_files", "resource": "files", "action": "create", "description": "Upload files"},
        {"name": "download_files", "resource": "files", "action": "read", "description": "Download files"},
        {"name": "delete_files", "resource": "files", "action": "delete", "description": "Delete files"}
    ]
    
    # Create permissions if they don't exist
    for perm_data in permissions_data:
        existing_permission = db.query(Permission).filter(
            Permission.name == perm_data["name"]
        ).first()
        
        if not existing_permission:
            permission = Permission(**perm_data)
            db.add(permission)
    
    db.commit()
    
    # Define roles with their permissions
    roles_data = [
        {
            "name": "client",
            "display_name": "Client",
            "description": "Property buyers, sellers, and investors",
            "permissions": [
                "read_properties", "chat_access", "upload_files", "download_files"
            ]
        },
        {
            "name": "agent",
            "display_name": "Real Estate Agent",
            "description": "Real estate agents and brokers",
            "permissions": [
                "read_properties", "create_properties", "update_properties",
                "read_clients", "create_clients", "update_clients", "manage_clients",
                "read_tasks", "create_tasks", "update_tasks",
                "chat_access", "chat_history", "view_analytics",
                "upload_files", "download_files", "delete_files"
            ]
        },
        {
            "name": "employee",
            "display_name": "Employee",
            "description": "Company staff and employees",
            "permissions": [
                "read_properties", "read_clients", "read_users",
                "read_tasks", "create_tasks", "update_tasks",
                "chat_access", "chat_history", "view_analytics",
                "upload_files", "download_files"
            ]
        },
        {
            "name": "admin",
            "display_name": "Administrator",
            "description": "System administrators and managers",
            "permissions": [
                "manage_properties", "manage_clients", "manage_users",
                "read_tasks", "create_tasks", "update_tasks", "delete_tasks", "assign_tasks",
                "chat_access", "chat_history", "view_analytics", "export_analytics",
                "admin_access", "system_config",
                "upload_files", "download_files", "delete_files"
            ]
        }
    ]
    
    # Create roles and assign permissions
    for role_data in roles_data:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        
        if not existing_role:
            role = Role(
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"]
            )
            
            # Add permissions to role
            for perm_name in role_data["permissions"]:
                permission = db.query(Permission).filter(Permission.name == perm_name).first()
                if permission:
                    role.permissions.append(permission)
            
            db.add(role)
        else:
            # Update existing role permissions
            existing_role.permissions.clear()
            for perm_name in role_data["permissions"]:
                permission = db.query(Permission).filter(Permission.name == perm_name).first()
                if permission:
                    existing_role.permissions.append(permission)
    
    db.commit()
    logger.info("Roles and permissions initialized")

def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def get_database_info() -> dict:
    """Get database information"""
    try:
        with engine.connect() as conn:
            # Get database version
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            
            # Get table count
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.scalar()
            
            return {
                "status": "connected",
                "version": version,
                "table_count": table_count,
                "url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "unknown"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def reset_database():
    """Reset database (DROP ALL TABLES - USE WITH CAUTION)"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
        init_database()
        logger.info("Database reset and reinitialized")
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise

def backup_database(backup_path: str):
    """Create database backup (PostgreSQL specific)"""
    import subprocess
    
    try:
        # Extract connection details from DATABASE_URL
        from urllib.parse import urlparse
        parsed = urlparse(DATABASE_URL)
        
        command = [
            "pg_dump",
            "-h", parsed.hostname,
            "-p", str(parsed.port or 5432),
            "-U", parsed.username,
            "-d", parsed.path.lstrip('/'),
            "-f", backup_path,
            "--verbose"
        ]
        
        # Set password via environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        result = subprocess.run(command, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Database backup created: {backup_path}")
            return True
        else:
            logger.error(f"Backup failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False

def restore_database(backup_path: str):
    """Restore database from backup (PostgreSQL specific)"""
    import subprocess
    
    try:
        # Extract connection details from DATABASE_URL
        from urllib.parse import urlparse
        parsed = urlparse(DATABASE_URL)
        
        command = [
            "psql",
            "-h", parsed.hostname,
            "-p", str(parsed.port or 5432),
            "-U", parsed.username,
            "-d", parsed.path.lstrip('/'),
            "-f", backup_path,
            "--verbose"
        ]
        
        # Set password via environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        result = subprocess.run(command, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Database restored from: {backup_path}")
            return True
        else:
            logger.error(f"Restore failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error restoring database: {e}")
        return False

# Database migration utilities
class DatabaseMigration:
    """Database migration utilities"""
    
    @staticmethod
    def get_current_version(db: Session) -> str:
        """Get current database schema version"""
        try:
            result = db.execute(text("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1"))
            return result.scalar() or "0.0.0"
        except:
            return "0.0.0"
    
    @staticmethod
    def set_version(db: Session, version: str):
        """Set database schema version"""
        try:
            db.execute(text("CREATE TABLE IF NOT EXISTS schema_version (id SERIAL PRIMARY KEY, version VARCHAR(20), applied_at TIMESTAMP DEFAULT NOW())"))
            db.execute(text("INSERT INTO schema_version (version) VALUES (:version)"), {"version": version})
            db.commit()
        except Exception as e:
            logger.error(f"Error setting schema version: {e}")
    
    @staticmethod
    def run_migration(db: Session, migration_sql: str, version: str):
        """Run a database migration"""
        try:
            # Run migration SQL
            for statement in migration_sql.split(';'):
                if statement.strip():
                    db.execute(text(statement))
            
            # Update version
            DatabaseMigration.set_version(db, version)
            
            logger.info(f"Migration to version {version} completed")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            db.rollback()
            raise

# Connection pooling monitoring
def get_pool_status():
    """Get connection pool status"""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid()
    }