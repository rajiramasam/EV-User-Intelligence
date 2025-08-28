from fastapi import APIRouter, HTTPException, Request, Depends
import os
import sys
from typing import List, Optional
from models.schemas import UserSession, SessionResponse
from core.jwt_utils import get_token_from_request, verify_token

# Add parent directory to path to access db module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

router = APIRouter(prefix="/sessions", tags=["Sessions"])

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

def get_current_user_id(request: Request) -> int:
    """Get current user ID from JWT token."""
    try:
        token = get_token_from_request(request)
        if not token:
            raise HTTPException(status_code=401, detail="Missing access token")
        
        payload = verify_token(token, token_type='access')
        return payload["user_id"]
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/", response_model=dict)
def log_session(session: UserSession, request: Request):
    """Log a user charging session to Snowflake database."""
    try:
        if not is_snowflake_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Verify the user is authenticated and owns the session
        current_user_id = get_current_user_id(request)
        if current_user_id != session.user_id:
            raise HTTPException(status_code=403, detail="Cannot log session for another user")
        
        snowflake_manager = get_snowflake_manager()
        
        # Insert new session
        insert_query = """
            INSERT INTO sessions (user_id, station_id, start_time, end_time, energy_consumed_kwh, cost)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # Calculate session duration and energy consumption (placeholder values)
        # In production, these would come from actual charging data
        energy_consumed = 0.0  # kWh
        cost = 0.0  # Currency
        
        snowflake_manager.execute_query(insert_query, (
            session.user_id,
            session.station_id,
            session.timestamp,  # start_time
            session.timestamp,  # end_time (same as start for now)
            energy_consumed,
            cost
        ))
        
        return {"status": "success", "message": "Session logged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error logging session: {e}")
        raise HTTPException(status_code=500, detail="Failed to log session")

@router.get("/", response_model=List[SessionResponse])
def get_user_sessions(request: Request, limit: int = 50, offset: int = 0):
    """Get charging sessions for the current user."""
    try:
        if not is_snowflake_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        current_user_id = get_current_user_id(request)
        snowflake_manager = get_snowflake_manager()
        
        # Get user sessions with station information
        query = """
            SELECT 
                s.id,
                s.user_id,
                s.station_id,
                s.start_time,
                s.end_time,
                s.energy_consumed_kwh,
                s.cost,
                s.created_at,
                st.name as station_name,
                st.latitude as station_latitude,
                st.longitude as station_longitude,
                st.energy_type as station_energy_type
            FROM sessions s
            LEFT JOIN stations st ON s.station_id = st.id
            WHERE s.user_id = %s
            ORDER BY s.start_time DESC
            LIMIT %s OFFSET %s
        """
        
        sessions_data = snowflake_manager.execute_query(query, (current_user_id, limit, offset))
        
        sessions = []
        for session_data in sessions_data:
            sessions.append(SessionResponse(
                id=session_data["id"],
                user_id=session_data["user_id"],
                station_id=session_data["station_id"],
                start_time=session_data["start_time"],
                end_time=session_data["end_time"],
                energy_consumed_kwh=session_data["energy_consumed_kwh"],
                cost=session_data["cost"],
                created_at=session_data["created_at"],
                station_name=session_data["station_name"],
                station_latitude=session_data["station_latitude"],
                station_longitude=session_data["station_longitude"],
                station_energy_type=session_data["station_energy_type"]
            ))
        
        return sessions
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")

@router.get("/statistics")
def get_session_statistics(request: Request):
    """Get charging session statistics for the current user."""
    try:
        if not is_snowflake_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        current_user_id = get_current_user_id(request)
        snowflake_manager = get_snowflake_manager()
        
        # Get session statistics
        stats_query = """
            SELECT 
                COUNT(*) as total_sessions,
                SUM(energy_consumed_kwh) as total_energy_kwh,
                SUM(cost) as total_cost,
                AVG(energy_consumed_kwh) as avg_energy_per_session,
                MIN(start_time) as first_session,
                MAX(start_time) as last_session
            FROM sessions 
            WHERE user_id = %s
        """
        
        stats_data = snowflake_manager.execute_query(stats_query, (current_user_id,))
        
        if not stats_data:
            return {
                "total_sessions": 0,
                "total_energy_kwh": 0.0,
                "total_cost": 0.0,
                "avg_energy_per_session": 0.0,
                "first_session": None,
                "last_session": None
            }
        
        return stats_data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting session statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session statistics")

@router.get("/recent")
def get_recent_sessions(request: Request, count: int = 5):
    """Get recent charging sessions for the current user."""
    try:
        if not is_snowflake_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        current_user_id = get_current_user_id(request)
        snowflake_manager = get_snowflake_manager()
        
        # Get recent sessions
        query = """
            SELECT 
                s.id,
                s.station_id,
                s.start_time,
                s.energy_consumed_kwh,
                s.cost,
                st.name as station_name,
                st.latitude as station_latitude,
                st.longitude as station_longitude
            FROM sessions s
            LEFT JOIN stations st ON s.station_id = st.id
            WHERE s.user_id = %s
            ORDER BY s.start_time DESC
            LIMIT %s
        """
        
        recent_sessions = snowflake_manager.execute_query(query, (current_user_id, count))
        return recent_sessions
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting recent sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent sessions")