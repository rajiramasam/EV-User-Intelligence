#!/usr/bin/env python3
"""
Production Database Setup Script for EV User Intelligence Platform
This script initializes the Snowflake database with proper tables and sample data.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the db directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'db'))

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'SNOWFLAKE_ACCOUNT',
        'SNOWFLAKE_USER', 
        'SNOWFLAKE_PASSWORD',
        'SNOWFLAKE_WAREHOUSE',
        'SNOWFLAKE_DATABASE',
        'SNOWFLAKE_SCHEMA'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    
    print("✅ All required environment variables are set")
    return True

def initialize_database():
    """Initialize the Snowflake database with tables and sample data."""
    try:
        from snowflake_connector import SnowflakeManager
        
        print("🔌 Connecting to Snowflake...")
        snowflake_manager = SnowflakeManager()
        
        print("📋 Creating database tables...")
        snowflake_manager.create_tables()
        
        print("✅ Database tables created successfully")
        
        # Insert sample stations data
        print("📊 Inserting sample stations data...")
        sample_stations = [
            {
                'id': 1,
                'ocm_id': 1001,
                'name': 'Downtown EV Station',
                'latitude': 40.7128,
                'longitude': -74.0060,
                'energy_type': 'Level 2',
                'address_line1': '123 Main Street',
                'address_line2': 'Suite 100',
                'town': 'New York',
                'state': 'NY',
                'country': 'USA',
                'postcode': '10001',
                'access_comments': '24/7 access, free parking'
            },
            {
                'id': 2,
                'ocm_id': 1002,
                'name': 'Central Park Charging Hub',
                'latitude': 40.7829,
                'longitude': -73.9654,
                'energy_type': 'DC Fast',
                'address_line1': 'Central Park',
                'address_line2': 'Near Bethesda Fountain',
                'town': 'New York',
                'state': 'NY',
                'country': 'USA',
                'postcode': '10024',
                'access_comments': 'Park access required'
            },
            {
                'id': 3,
                'ocm_id': 1003,
                'name': 'Brooklyn Bridge Station',
                'latitude': 40.7061,
                'longitude': -73.9969,
                'energy_type': 'Level 2',
                'address_line1': 'Brooklyn Bridge',
                'address_line2': 'Manhattan side',
                'town': 'New York',
                'state': 'NY',
                'country': 'USA',
                'postcode': '10038',
                'access_comments': 'Public access, paid parking'
            }
        ]
        
        for station in sample_stations:
            try:
                snowflake_manager.insert_station(station)
            except Exception as e:
                print(f"⚠️  Warning: Could not insert station {station['name']}: {e}")
        
        print("✅ Sample stations data inserted")
        
        # Insert sample EV stores
        print("🏪 Inserting sample EV stores...")
        sample_stores = [
            {
                'name': 'Tesla Service Center',
                'store_type': 'Service',
                'latitude': 40.7505,
                'longitude': -73.9934,
                'address': '456 5th Avenue, New York, NY 10018',
                'contact': '+1-212-555-0123',
                'hours': 'Mon-Fri 8AM-6PM, Sat 9AM-4PM',
                'services': 'Sales, Service, Parts',
                'website': 'https://www.tesla.com'
            }
        ]
        
        for store in sample_stores:
            try:
                insert_query = """
                    INSERT INTO ev_stores (name, store_type, latitude, longitude, address, contact, hours, services, website)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                snowflake_manager.execute_query(insert_query, (
                    store['name'], store['store_type'], store['latitude'], store['longitude'],
                    store['address'], store['contact'], store['hours'], store['services'], store['website']
                ))
            except Exception as e:
                print(f"⚠️  Warning: Could not insert store {store['name']}: {e}")
        
        print("✅ Sample EV stores data inserted")
        
        print("\n🎉 Database initialization completed successfully!")
        print("\n📋 Summary:")
        print(f"   • Tables created: stations, users, sessions, station_usage, user_locations, ev_stores, floating_services")
        print(f"   • Sample stations: {len(sample_stations)}")
        print(f"   • Sample stores: {len(sample_stores)}")
        print("\n🚀 Your EV User Intelligence Platform is ready for production!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def main():
    """Main function to run the database setup."""
    print("🚀 EV User Intelligence Platform - Production Database Setup")
    print("=" * 60)
    
    if not check_environment():
        sys.exit(1)
    
    if not initialize_database():
        sys.exit(1)
    
    print("\n✅ Setup completed successfully!")

if __name__ == "__main__":
    main()
