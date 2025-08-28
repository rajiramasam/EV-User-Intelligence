import os
import snowflake.connector
from snowflake.connector import Error as SnowflakeError
from typing import List, Dict, Any, Optional
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SnowflakeManager:
    def __init__(self):
        self.connection_params = {
            'user': os.getenv("SNOWFLAKE_USER"),
            'password': os.getenv("SNOWFLAKE_PASSWORD"),
            'account': os.getenv("SNOWFLAKE_ACCOUNT"),
            'warehouse': os.getenv("SNOWFLAKE_WAREHOUSE"),
            'database': os.getenv("SNOWFLAKE_DATABASE"),
            'schema': os.getenv("SNOWFLAKE_SCHEMA"),
        }
        
        # Validate required parameters
        missing_params = [k for k, v in self.connection_params.items() if not v]
        if missing_params:
            raise ValueError(f"Missing Snowflake configuration: {missing_params}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for Snowflake connections with automatic cleanup."""
        conn = None
        try:
            conn = snowflake.connector.connect(**self.connection_params)
            logger.info("Successfully connected to Snowflake")
            yield conn
        except SnowflakeError as e:
            logger.error(f"Snowflake connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.info("Snowflake connection closed")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results as a list of dictionaries."""
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Fetch results
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    results = []
                    for row in cursor.fetchall():
                        results.append(dict(zip(columns, row)))
                    return results
                else:
                    conn.commit()
                    return []
                    
            except SnowflakeError as e:
                logger.error(f"Query execution error: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute a query with multiple parameter sets."""
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                logger.info(f"Executed {len(params_list)} operations successfully")
            except SnowflakeError as e:
                logger.error(f"Batch execution error: {e}")
                raise
            finally:
                cursor.close()
    
    def create_tables(self) -> None:
        """Create all necessary tables for the EV User Intelligence."""
        tables = {
            'stations': """
                CREATE TABLE IF NOT EXISTS stations (
                    id INTEGER PRIMARY KEY,
                    ocm_id INTEGER,
                    name STRING,
                    latitude FLOAT,
                    longitude FLOAT,
                    energy_type STRING,
                    available BOOLEAN DEFAULT TRUE,
                    address_line1 STRING,
                    address_line2 STRING,
                    town STRING,
                    state STRING,
                    country STRING,
                    postcode STRING,
                    access_comments STRING,
                    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                )
            """,
            'users': """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER AUTOINCREMENT PRIMARY KEY,
                    email STRING UNIQUE,
                    password_hash STRING,
                    eco_score FLOAT DEFAULT 0.0,
                    first_name STRING,
                    last_name STRING,
                    vehicle_type STRING,
                    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                )
            """,
            'sessions': """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER AUTOINCREMENT PRIMARY KEY,
                    user_id INTEGER,
                    station_id INTEGER,
                    start_time TIMESTAMP_NTZ,
                    end_time TIMESTAMP_NTZ,
                    energy_consumed_kwh FLOAT,
                    cost FLOAT,
                    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (station_id) REFERENCES stations(id)
                )
            """,
            'station_usage': """
                CREATE TABLE IF NOT EXISTS station_usage (
                    id INTEGER AUTOINCREMENT PRIMARY KEY,
                    station_id INTEGER,
                    usage_date DATE,
                    total_sessions INTEGER DEFAULT 0,
                    total_energy_kwh FLOAT DEFAULT 0.0,
                    avg_session_duration_minutes FLOAT DEFAULT 0.0,
                    peak_hour INTEGER,
                    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                    FOREIGN KEY (station_id) REFERENCES stations(id)
                )
            """,
            'user_locations': """
                CREATE TABLE IF NOT EXISTS user_locations (
                    user_id INTEGER PRIMARY KEY,
                    latitude FLOAT,
                    longitude FLOAT,
                    status STRING DEFAULT 'active',
                    message STRING,
                    contact_method STRING,
                    last_updated TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                )
            """,
            'ev_stores': """
                CREATE TABLE IF NOT EXISTS ev_stores (
                    id INTEGER AUTOINCREMENT PRIMARY KEY,
                    name STRING,
                    latitude FLOAT,
                    longitude FLOAT,
                    address_line1 STRING,
                    address_line2 STRING,
                    town STRING,
                    state STRING,
                    country STRING,
                    postcode STRING,
                    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                )
            """,
            'floating_services': """
                CREATE TABLE IF NOT EXISTS floating_services (
                    id INTEGER AUTOINCREMENT PRIMARY KEY,
                    name STRING,
                    latitude FLOAT,
                    longitude FLOAT,
                    address_line1 STRING,
                    address_line2 STRING,
                    town STRING,
                    state STRING,
                    country STRING,
                    postcode STRING,
                    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                )
            """
        }
        
        for table_name, create_sql in tables.items():
            try:
                self.execute_query(create_sql)
                logger.info(f"Table '{table_name}' created successfully")
            except Exception as e:
                logger.error(f"Error creating table '{table_name}': {e}")
                raise
    
    def insert_station(self, station_data: Dict[str, Any]) -> None:
        """Insert a single station into the database."""
        query = """
            INSERT INTO stations (
                id, ocm_id, name, latitude, longitude, energy_type, 
                address_line1, address_line2, town, state, country, postcode, access_comments
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params = (
            station_data.get('id'),
            station_data.get('ocm_id'),
            station_data.get('name'),
            station_data.get('latitude'),
            station_data.get('longitude'),
            station_data.get('energy_type'),
            station_data.get('address_line1'),
            station_data.get('address_line2'),
            station_data.get('town'),
            station_data.get('state'),
            station_data.get('country'),
            station_data.get('postcode'),
            station_data.get('access_comments')
        )
        
        self.execute_query(query, params)
    
    def insert_stations_batch(self, stations_data: List[Dict[str, Any]]) -> None:
        """Insert multiple stations in a batch operation."""
        query = """
            INSERT INTO stations (
                id, ocm_id, name, latitude, longitude, energy_type, 
                address_line1, address_line2, town, state, country, postcode, access_comments
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params_list = []
        for station in stations_data:
            params = (
                station.get('id'),
                station.get('ocm_id'),
                station.get('name'),
                station.get('latitude'),
                station.get('longitude'),
                station.get('energy_type'),
                station.get('address_line1'),
                station.get('address_line2'),
                station.get('town'),
                station.get('state'),
                station.get('country'),
                station.get('postcode'),
                station.get('access_comments')
            )
            params_list.append(params)
        
        self.execute_many(query, params_list)
    
    def get_stations(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve stations from the database."""
        query = f"""
            SELECT * FROM stations 
            ORDER BY created_at DESC 
            LIMIT {limit}
        """
        return self.execute_query(query)
    
    def get_stations_by_location(self, lat: float, lon: float, radius_km: float = 10) -> List[Dict[str, Any]]:
        """Get stations within a specified radius of a location."""
        # Using Haversine formula in SQL
        query = """
            SELECT *, 
                   (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) * 
                    cos(radians(longitude) - radians(%s)) + 
                    sin(radians(%s)) * sin(radians(latitude)))) AS distance_km
            FROM stations 
            HAVING distance_km <= %s
            ORDER BY distance_km
        """
        return self.execute_query(query, (lat, lon, lat, radius_km))
    
    def get_station_count(self) -> int:
        """Get total number of stations in the database."""
        query = ('SELECT COUNT(*) AS "count" FROM stations')
        result = self.execute_query(query)
        return result[0]['count'] if result else 0

    # --- USER MANAGEMENT ---
    def create_user(self, email: str, password_hash: str, first_name: str, last_name: str, vehicle_type: str) -> Dict[str, Any]:
        """Create a new user in the database."""
        query = """
            INSERT INTO users (email, password_hash, first_name, last_name, vehicle_type, eco_score)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        self.execute_query(query, (email, password_hash, first_name, last_name, vehicle_type, 0.0))
        
        # Get the created user
        get_user_query = "SELECT id, email, eco_score, first_name, last_name, vehicle_type, created_at FROM users WHERE email = %s"
        user_data = self.execute_query(get_user_query, (email,))
        
        return user_data[0] if user_data else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        query = "SELECT * FROM users WHERE email = %s"
        result = self.execute_query(query, (email,))
        return result[0] if result else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        query = "SELECT * FROM users WHERE id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def update_user_profile(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Update user profile information."""
        allowed_fields = ['first_name', 'last_name', 'vehicle_type', 'eco_score']
        update_fields = []
        update_values = []
        
        for field, value in updates.items():
            if field in allowed_fields and value is not None:
                update_fields.append(f"{field} = %s")
                update_values.append(value)
        
        if not update_fields:
            return False
        
        update_values.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP() WHERE id = %s"
        
        try:
            self.execute_query(query, tuple(update_values))
            return True
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False

    # --- USER LOCATIONS ---
    def upsert_user_location(self, user_id: int, latitude: float, longitude: float, status: str = 'active', message: str = None, contact_method: str = None):
        """Insert or update a user's location."""
        query = '''
            MERGE INTO user_locations AS t
            USING (SELECT %s AS user_id, %s AS latitude, %s AS longitude, %s AS status, %s AS message, %s AS contact_method) AS s
            ON t.user_id = s.user_id
            WHEN MATCHED THEN UPDATE SET latitude = s.latitude, longitude = s.longitude, last_updated = CURRENT_TIMESTAMP(), status = s.status, message = s.message, contact_method = s.contact_method
            WHEN NOT MATCHED THEN INSERT (user_id, latitude, longitude, status, message, contact_method) VALUES (s.user_id, s.latitude, s.longitude, s.status, s.message, s.contact_method)
        '''
        self.execute_query(query, (user_id, latitude, longitude, status, message, contact_method))

    def get_nearby_users(self, latitude: float, longitude: float, radius_km: float = 10) -> list:
        """Get users within a radius (km) of a location."""
        query = '''
            SELECT ul.*, u.email, u.eco_score
            FROM user_locations ul
            JOIN users u ON ul.user_id = u.id
            WHERE ul.status = 'active'
            AND (6371 * acos(cos(radians(%s)) * cos(radians(ul.latitude)) * cos(radians(ul.longitude) - radians(%s)) + sin(radians(%s)) * sin(radians(ul.latitude)))) <= %s
            ORDER BY ul.last_updated DESC
        '''
        return self.execute_query(query, (latitude, longitude, latitude, radius_km))

    # --- EV STORES ---
    def get_nearby_ev_stores(self, latitude: float, longitude: float, radius_km: float = 10) -> list:
        query = '''
            SELECT *, (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) * cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * sin(radians(latitude)))) AS distance_km
            FROM ev_stores
            HAVING distance_km <= %s
            ORDER BY distance_km
        '''
        return self.execute_query(query, (latitude, longitude, latitude, radius_km))

    # --- FLOATING SERVICES ---
    def get_nearby_floating_services(self, latitude: float, longitude: float, radius_km: float = 10) -> list:
        query = '''
            SELECT *, (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) * cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * sin(radians(latitude)))) AS distance_km
            FROM floating_services
            HAVING distance_km <= %s
            ORDER BY distance_km
        '''
        return self.execute_query(query, (latitude, longitude, latitude, radius_km))

    # --- SESSION MANAGEMENT ---
    def log_session(self, user_id: int, station_id: int, start_time: str, end_time: str, energy_consumed: float = 0.0, cost: float = 0.0) -> bool:
        """Log a charging session."""
        query = """
            INSERT INTO sessions (user_id, station_id, start_time, end_time, energy_consumed_kwh, cost)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        try:
            self.execute_query(query, (user_id, station_id, start_time, end_time, energy_consumed, cost))
            return True
        except Exception as e:
            logger.error(f"Error logging session: {e}")
            return False
    
    def get_user_sessions(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get charging sessions for a user."""
        query = """
            SELECT 
                s.*,
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
        
        return self.execute_query(query, (user_id, limit, offset))

# Legacy function for backward compatibility
def get_snowflake_connection():
    """Legacy function - use SnowflakeManager instead."""
    manager = SnowflakeManager()
    return manager.get_connection().__enter__()

# Global instance for easy access (lazy initialization)
snowflake_manager = None

def get_snowflake_manager():
    """Get or create the global SnowflakeManager instance."""
    global snowflake_manager
    if snowflake_manager is None:
        snowflake_manager = SnowflakeManager()
    return snowflake_manager