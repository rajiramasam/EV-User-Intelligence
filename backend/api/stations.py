from fastapi import APIRouter, Query, HTTPException
import os
import sys
import requests
import math
from typing import List, Optional
from models.schemas import Station, NearbyStation

# Add parent directory to path to access db module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
router = APIRouter(prefix="/stations", tags=["Stations"])

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

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula."""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def estimate_travel_time(distance_km: float, avg_speed_kmh: float = 30) -> int:
    """Estimate travel time in minutes."""
    return int((distance_km / avg_speed_kmh) * 60)

def fetch_ocm_stations(lat: float, lon: float, radius: float = 10) -> List[dict]:
    """Fetch stations from Open Charge Map API."""
    try:
        ocm_api_key = os.getenv("OCM_API_KEY", "")
        if not ocm_api_key:
            return []
        
        url = "https://api.openchargemap.io/v3/poi"
        params = {
            "key": ocm_api_key,
            "latitude": lat,
            "longitude": lon,
            "distance": radius,
            "distanceunit": "km",
            "maxresults": 50,
            "compact": True,
            "verbose": False
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"OCM API error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching OCM stations: {e}")
        return []

@router.get("/", response_model=List[Station])
def get_stations():
    """Fetch all charging stations from Snowflake database."""
    try:
        if not is_snowflake_available():
            raise HTTPException(status_code=503, detail="Snowflake database not available")
        
        snowflake_manager = get_snowflake_manager()
        stations_data = snowflake_manager.get_stations(limit=1000)
        
        if not stations_data:
            return []
        
        stations = []
        for station in stations_data:
            stations.append(Station(
                id=station["id"],
                name=station["name"],
                latitude=station["latitude"],
                longitude=station["longitude"],
                energy_type=station["energy_type"],
                available=station["available"]
            ))
        
        return stations
        
    except Exception as e:
        print(f"Error loading stations: {e}")
        raise HTTPException(status_code=500, detail="Failed to load stations")

@router.get("/nearby", response_model=List[NearbyStation])
def get_nearby_stations(
    lat: float = Query(..., description="User's latitude"),
    lon: float = Query(..., description="User's longitude"),
    radius: float = Query(10, description="Search radius in kilometers"),
    use_ocm: bool = Query(True, description="Use Open Charge Map API"),
    limit: int = Query(5, description="Number of nearest stations to return")
):
    """Get nearby charging stations with distance and time calculations."""
    try:
        if not is_snowflake_available():
            raise HTTPException(status_code=503, detail="Snowflake database not available")
        
        nearby_stations = []
        snowflake_manager = get_snowflake_manager()
        
        # Get stations from Snowflake
        try:
            snowflake_stations = snowflake_manager.get_stations_by_location(lat, lon, radius)
            
            for station in snowflake_stations:
                distance = station.get('distance_km', 0)
                if distance <= radius:
                    travel_time = estimate_travel_time(distance)
                    nearby_stations.append(NearbyStation(
                        id=str(station["id"]),
                        name=station["name"],
                        latitude=station["latitude"],
                        longitude=station["longitude"],
                        energy_type=station["energy_type"],
                        available=station["available"],
                        distance_km=round(distance, 2),
                        travel_time_minutes=travel_time,
                        source="snowflake"
                    ))
        except Exception as e:
            print(f"Error getting stations from Snowflake: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve stations from database")
        
        # Fetch from Open Charge Map API if enabled
        if use_ocm:
            ocm_stations = fetch_ocm_stations(lat, lon, radius)
            for station in ocm_stations:
                try:
                    # Extract station data from OCM response
                    station_lat = station.get("AddressInfo", {}).get("Latitude", 0)
                    station_lon = station.get("AddressInfo", {}).get("Longitude", 0)
                    
                    if station_lat and station_lon:
                        distance = calculate_distance(lat, lon, station_lat, station_lon)
                        if distance <= radius:
                            travel_time = estimate_travel_time(distance)
                            
                            # Get station name
                            station_name = station.get("AddressInfo", {}).get("Title", "Unknown Station")
                            if not station_name or station_name == "Unknown Station":
                                station_name = f"Station at {station.get('AddressInfo', {}).get('AddressLine1', 'Unknown Location')}"
                            
                            # Get connection info
                            connections = station.get("Connections", [])
                            energy_types = []
                            for conn in connections:
                                connection_type = conn.get("ConnectionType", {}).get("Title", "Unknown")
                                if connection_type not in energy_types:
                                    energy_types.append(connection_type)
                            
                            energy_type = ", ".join(energy_types) if energy_types else "Unknown"
                            
                            nearby_stations.append(NearbyStation(
                                id=f"ocm_{station.get('ID', len(nearby_stations) + 1000)}",
                                name=station_name,
                                latitude=station_lat,
                                longitude=station_lon,
                                energy_type=energy_type,
                                available=True,  # OCM doesn't provide real-time availability
                                distance_km=round(distance, 2),
                                travel_time_minutes=travel_time,
                                source="ocm"
                            ))
                except Exception as e:
                    print(f"Error processing OCM station: {e}")
                    continue
        
        # Sort by distance
        nearby_stations.sort(key=lambda x: x.distance_km)
        
        return nearby_stations[:limit]  # Return top N nearest stations
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting nearby stations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve nearby stations")

@router.get("/count")
def get_station_count():
    """Get total number of stations in the database."""
    try:
        if not is_snowflake_available():
            raise HTTPException(status_code=503, detail="Snowflake database not available")
        
        snowflake_manager = get_snowflake_manager()
        count = snowflake_manager.get_station_count()
        return {"count": count, "source": "snowflake"}
        
    except Exception as e:
        print(f"Error getting station count: {e}")
        raise HTTPException(status_code=500, detail="Failed to get station count")

@router.get("/statistics")
def get_station_statistics():
    """Get station statistics from Snowflake."""
    try:
        if not is_snowflake_available():
            raise HTTPException(status_code=503, detail="Snowflake database not available")
        
        snowflake_manager = get_snowflake_manager()
        
        # Get statistics from Snowflake
        query = """
            SELECT 
                COUNT(*) as total_stations,
                COUNT(DISTINCT country) as countries,
                COUNT(DISTINCT energy_type) as energy_types,
                AVG(CASE WHEN available THEN 1 ELSE 0 END) * 100 as availability_percentage
            FROM stations
        """
        
        result = snowflake_manager.execute_query(query)
        if result:
            return {
                "total_stations": result[0]["total_stations"],
                "countries": result[0]["countries"],
                "energy_types": result[0]["energy_types"],
                "availability_percentage": round(result[0]["availability_percentage"], 2)
            }
        else:
            return {"error": "No statistics available"}
            
    except Exception as e:
        print(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {e}")

@router.get("/search")
def search_stations(
    query: str = Query(..., description="Search term for station name or location"),
    limit: int = Query(20, description="Maximum number of results")
):
    """Search stations by name or location."""
    try:
        if not is_snowflake_available():
            raise HTTPException(status_code=503, detail="Snowflake database not available")
        
        snowflake_manager = get_snowflake_manager()
        
        # Search query
        search_query = """
            SELECT * FROM stations 
            WHERE LOWER(name) LIKE LOWER(%s) 
               OR LOWER(town) LIKE LOWER(%s) 
               OR LOWER(state) LIKE LOWER(%s)
            ORDER BY name
            LIMIT %s
        """
        
        search_term = f"%{query}%"
        results = snowflake_manager.execute_query(search_query, (search_term, search_term, search_term, limit))
        
        return results
        
    except Exception as e:
        print(f"Error searching stations: {e}")
        raise HTTPException(status_code=500, detail="Failed to search stations")