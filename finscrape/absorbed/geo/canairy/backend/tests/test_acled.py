"""
Test ACLED API Connection
"""

from acled_api import ACLEDClient
import pandas as pd

# Your ACLED credentials
USERNAME = "manavpthaker@gmail.com"
PASSWORD = "xG*#K^U&xTKX2*xjQHGxP"

def test_connection():
    """Test basic API connection and authentication"""
    
    print("Testing ACLED API Connection...")
    print("=" * 50)
    
    try:
        # Initialize client
        client = ACLEDClient(USERNAME, PASSWORD)
        
        # Test authentication
        print("\n1. Testing authentication...")
        client.authenticate()
        
        # Test basic data retrieval - get recent events
        print("\n2. Testing data retrieval - Recent events...")
        recent_events = client.get_recent_events(
            countries=["Ukraine", "Russia"],
            days_back=7,
            limit=10
        )
        
        if not recent_events.empty:
            print(f"\n✓ Successfully retrieved {len(recent_events)} events")
            print("\nSample data:")
            print(recent_events[['country', 'event_date', 'event_type', 'location']].head(5))
        
        # Test specific country search
        print("\n3. Testing country-specific search...")
        georgia_events = client.get_events_by_country_and_date(
            country="Georgia",
            start_date="2024-01-01",
            end_date="2024-12-31",
            limit=20,
            fields=['event_id_cnty', 'event_date', 'event_type', 'location', 'fatalities']
        )
        
        if not georgia_events.empty:
            print(f"\n✓ Found {len(georgia_events)} events in Georgia for 2024")
            print("\nEvent types found:")
            print(georgia_events['event_type'].value_counts())
        
        print("\n" + "=" * 50)
        print("✓ All tests passed successfully!")
        print("Your ACLED API connection is working properly.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nPlease check:")
        print("1. Your credentials are correct")
        print("2. You have an active ACLED account")
        print("3. Your internet connection is working")
        return False


if __name__ == "__main__":
    success = test_connection()
    
    if success:
        print("\nYou can now use the ACLEDClient in your projects!")
        print("\nExample usage:")
        print("```python")
        print("from acled_api import ACLEDClient")
        print(f'client = ACLEDClient("{USERNAME}", "your_password")')
        print("df = client.get_recent_events(countries=['Yemen'], days_back=30)")
        print("```")