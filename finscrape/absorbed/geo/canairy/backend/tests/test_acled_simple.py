"""
Simple ACLED API Test
"""

import requests
import json

# Your credentials
USERNAME = "manavpthaker@gmail.com"
PASSWORD = "xG*#K^U&xTKX2*xjQHGxP"

def test_simple():
    """Test with minimal parameters"""
    
    print("Testing ACLED API...")
    print("=" * 50)
    
    # Step 1: Get access token
    print("\n1. Getting access token...")
    
    token_url = "https://acleddata.com/oauth/token"
    
    data = {
        'username': USERNAME,
        'password': PASSWORD,
        'grant_type': 'password',
        'client_id': 'acled'
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        print("✓ Got access token successfully")
        print(f"Token (first 20 chars): {access_token[:20]}...")
    else:
        print(f"✗ Failed to get token: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    # Step 2: Test simple API call with just limit
    print("\n2. Testing API call with minimal parameters...")
    
    api_url = "https://acleddata.com/api/acled/read"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Very simple request - just get 5 recent events
    params = {
        "limit": 5
    }
    
    response = requests.get(api_url, headers=headers, params=params)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ API call successful!")
        print(f"Response status from API: {data.get('status')}")
        print(f"Number of events retrieved: {len(data.get('data', []))}")
        
        if data.get('data'):
            event = data['data'][0]
            print(f"\nFirst event:")
            print(f"  Country: {event.get('country')}")
            print(f"  Date: {event.get('event_date')}")
            print(f"  Type: {event.get('event_type')}")
    else:
        print(f"✗ API call failed: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    
    # Step 3: Test with a specific country
    print("\n3. Testing with country filter...")
    
    params = {
        "country": "Georgia",
        "limit": 5
    }
    
    response = requests.get(api_url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Country-specific call successful!")
        print(f"Number of Georgia events: {len(data.get('data', []))}")
    else:
        print(f"✗ Country filter failed: {response.status_code}")

if __name__ == "__main__":
    test_simple()