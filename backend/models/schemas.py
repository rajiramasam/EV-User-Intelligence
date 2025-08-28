from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

class Station(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    energy_type: str
    available: bool

class NearbyStation(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    energy_type: str
    available: bool
    distance_km: float
    travel_time_minutes: int
    source: str  # "snowflake" or "ocm"

class UserSession(BaseModel):
    user_id: int
    station_id: int
    timestamp: str

class SessionResponse(BaseModel):
    id: int
    user_id: int
    station_id: int
    start_time: str
    end_time: str
    energy_consumed_kwh: float
    cost: float
    created_at: str
    station_name: Optional[str] = None
    station_latitude: Optional[float] = None
    station_longitude: Optional[float] = None
    station_energy_type: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=3, max_length=128)

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    vehicle_type: str = Field(..., description="Type of electric vehicle")

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    eco_score: float
    access_token: Optional[str] = None

class UserProfile(BaseModel):
    id: int
    email: EmailStr
    eco_score: float
    first_name: str
    last_name: str
    vehicle_type: str
    created_at: str

class RecommendationResponse(BaseModel):
    user_id: int
    recommended_station_ids: List[int]

# --- New Models for Advanced Features ---
class UserLocationIn(BaseModel):
    user_id: int
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    status: Optional[str] = Field('active', pattern='^(active|hidden|offline)$')
    message: Optional[str] = Field(None, max_length=200)
    contact_method: Optional[str] = Field(None, max_length=100)

class UserLocationOut(UserLocationIn):
    last_updated: str
    email: Optional[EmailStr] = None
    eco_score: Optional[float] = None

class EVStoreIn(BaseModel):
    name: str
    store_type: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str]
    contact: Optional[str]
    hours: Optional[str]
    services: Optional[str]
    website: Optional[str]

class EVStoreOut(EVStoreIn):
    id: int
    created_at: str
    distance_km: Optional[float] = None

class FloatingServiceIn(BaseModel):
    name: str
    service_type: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    contact: Optional[str]
    hours: Optional[str]
    description: Optional[str]
    website: Optional[str]

class FloatingServiceOut(FloatingServiceIn):
    id: int
    created_at: str
    distance_km: Optional[float] = None