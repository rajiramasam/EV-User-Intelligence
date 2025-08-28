from fastapi import APIRouter, HTTPException, Response, Request, Cookie, Depends
import os
import sys
from typing import Optional
from models.schemas import UserLogin, UserResponse, UserRegister
from core.security import verify_password, hash_password
from core.jwt_utils import (
    create_access_token, create_refresh_token, verify_token, blacklist_token, get_token_from_request
)
from slowapi.util import get_remote_address
from slowapi import Limiter

# Add parent directory to path to access db module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

router = APIRouter(prefix="/users", tags=["Users"])

limiter = Limiter(key_func=get_remote_address)

# Lazy import and initialization of Snowflake manager
def get_snowflake_manager():
    """Get SnowflakeManager instance with lazy initialization."""
    try:
        from db.snowflake_connector import SnowflakeManager
        return SnowflakeManager()
    except Exception as e:
        print(f"Snowflake not available: {e}")
        return None

def is_snowflake_available():
    """Check if Snowflake is available."""
    try:
        manager = get_snowflake_manager()
        return manager is not None
    except:
        return False

@router.post("/register", response_model=UserResponse)
@limiter.limit("3/minute")
def register_user(user: UserRegister, response: Response, request: Request):
    """Register a new user."""
    try:
        if not is_snowflake_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        snowflake_manager = get_snowflake_manager()
        
        # Check if user already exists
        check_query = "SELECT id FROM users WHERE email = %s"
        existing_user = snowflake_manager.execute_query(check_query, (user.email,))
        
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Hash password
        hashed_password = hash_password(user.password)
        
        # Insert new user
        insert_query = """
            INSERT INTO users (email, password_hash, eco_score, first_name, last_name, vehicle_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        snowflake_manager.execute_query(insert_query, (
            user.email,
            hashed_password,
            0.0,  # Default eco score
            user.first_name,
            user.last_name,
            user.vehicle_type
        ))
        
        # Get the created user
        get_user_query = "SELECT id, email, eco_score FROM users WHERE email = %s"
        new_user = snowflake_manager.execute_query(get_user_query, (user.email,))
        
        if not new_user:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        user_data = new_user[0]
        
        # Issue tokens
        payload = {"user_id": user_data["id"], "email": user_data["email"]}
        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)
        
        # Set refresh token in HttpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # Set True in production
            samesite="lax",
            max_age=7*24*60*60
        )
        
        return {
            "id": user_data["id"],
            "email": user_data["email"],
            "eco_score": user_data["eco_score"],
            "access_token": access_token
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in user registration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login", response_model=UserResponse)
@limiter.limit("5/minute")
def login(user: UserLogin, response: Response, request: Request):
    """Login user and issue JWT tokens."""
    try:
        if not is_snowflake_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        snowflake_manager = get_snowflake_manager()
        
        # Get user from database
        query = "SELECT id, email, password_hash, eco_score FROM users WHERE email = %s"
        user_data = snowflake_manager.execute_query(query, (user.email,))
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user_data = user_data[0]
        
        # Verify password
        if not verify_password(user.password, user_data["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Issue tokens
        payload = {"user_id": user_data["id"], "email": user_data["email"]}
        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)
        
        # Set refresh token in HttpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # Set True in production
            samesite="lax",
            max_age=7*24*60*60
        )
        
        return {
            "id": user_data["id"],
            "email": user_data["email"],
            "eco_score": user_data["eco_score"],
            "access_token": access_token
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/refresh-token")
@limiter.limit("10/minute")
def refresh_token(request: Request, refresh_token: Optional[str] = Cookie(None)):
    """Issue a new access token using a valid refresh token."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    
    try:
        payload = verify_token(refresh_token, token_type='refresh')
        new_access_token = create_access_token({"user_id": payload["user_id"], "email": payload["email"]})
        return {"access_token": new_access_token}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/logout")
def logout(request: Request, response: Response, access_token: Optional[str] = Cookie(None)):
    """Logout user by blacklisting access token and clearing refresh token cookie."""
    # Try to get access token from header or cookie
    token = access_token
    if not token:
        try:
            token = get_token_from_request(request)
        except Exception:
            token = None
    
    if token:
        blacklist_token(token)
    
    response.delete_cookie("refresh_token")
    return {"success": True, "message": "Logged out"}

@router.get("/profile")
def get_user_profile(request: Request):
    """Get current user's profile information."""
    try:
        # Get token from request
        token = get_token_from_request(request)
        if not token:
            raise HTTPException(status_code=401, detail="Missing access token")
        
        # Verify token
        payload = verify_token(token, token_type='access')
        
        if not is_snowflake_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        snowflake_manager = get_snowflake_manager()
        
        # Get user profile
        query = """
            SELECT id, email, eco_score, first_name, last_name, vehicle_type, created_at
            FROM users WHERE id = %s
        """
        user_data = snowflake_manager.execute_query(query, (payload["user_id"],))
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user_data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/profile")
def update_user_profile(request: Request, profile_update: dict):
    """Update current user's profile information."""
    try:
        # Get token from request
        token = get_token_from_request(request)
        if not token:
            raise HTTPException(status_code=401, detail="Missing access token")
        
        # Verify token
        payload = verify_token(token, token_type='access')
        
        if not is_snowflake_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        snowflake_manager = get_snowflake_manager()
        
        # Update user profile
        allowed_fields = ['first_name', 'last_name', 'vehicle_type']
        update_fields = []
        update_values = []
        
        for field, value in profile_update.items():
            if field in allowed_fields and value is not None:
                update_fields.append(f"{field} = %s")
                update_values.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        update_values.append(payload["user_id"])
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        
        snowflake_manager.execute_query(query, tuple(update_values))
        
        return {"success": True, "message": "Profile updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")