import hashlib
import os
import sys

# Add parent directory to path to access db module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt for production security."""
    # In production, you should use bcrypt or similar
    # For now, using SHA-256 with a salt
    salt = os.getenv("PASSWORD_SALT", "default_salt_change_in_production")
    salted_password = password + salt
    return hashlib.sha256(salted_password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed

def get_user_by_email_from_db(email: str):
    """Get user from Snowflake database by email."""
    try:
        from db.snowflake_connector import SnowflakeManager
        snowflake_manager = SnowflakeManager()
        
        query = "SELECT id, email, password_hash, eco_score FROM users WHERE email = %s"
        user_data = snowflake_manager.execute_query(query, (email,))
        
        if user_data:
            user = user_data[0]
            return type('User', (), {
                'id': user["id"],
                'email': user["email"],
                'password_hash': user["password_hash"],
                'eco_score': user["eco_score"]
            })()
        return None
        
    except Exception as e:
        print(f"Error loading user from database: {e}")
        return None

def create_user_in_db(email: str, password: str, first_name: str, last_name: str, vehicle_type: str):
    """Create a new user in Snowflake database."""
    try:
        from db.snowflake_connector import SnowflakeManager
        snowflake_manager = SnowflakeManager()
        
        # Check if user already exists
        check_query = "SELECT id FROM users WHERE email = %s"
        existing_user = snowflake_manager.execute_query(check_query, (email,))
        
        if existing_user:
            return {"status": "error", "message": "User already exists"}
        
        # Hash password and insert user
        password_hash = hash_password(password)
        insert_query = """
            INSERT INTO users (email, password_hash, eco_score, first_name, last_name, vehicle_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        snowflake_manager.execute_query(insert_query, (
            email, password_hash, 0.0, first_name, last_name, vehicle_type
        ))
        
        return {"status": "success", "message": "User created successfully"}
        
    except Exception as e:
        print(f"Error creating user in database: {e}")
        return {"status": "error", "message": "Failed to create user"} 