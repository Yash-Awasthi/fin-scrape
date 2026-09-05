"""
Test ACLED API with Cookie-based Authentication
"""

import requests
import json

USERNAME = "manavpthaker@gmail.com"
PASSWORD = "xG*#K^U&xTKX2*xjQHGxP"

def test_cookie_auth():
    """Test using cookie-based authentication"""
    
    print("Testing ACLED API with Cookie Authentication...")
    print("=" * 50)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Login to get session cookie
    print("\n1. Logging in to ACLED...")
    
    login_url = "https://acleddata.com/user/login?_format=json"
    
    login_data = {
        "name": USERNAME,
        "pass": PASSWORD
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = session.post(login_url, json=login_data, headers=headers)
    
    print(f"Login response status: {response.status_code}")
    
    if response.status_code == 200:
        login_response = response.json()
        print(f"✓ Logged in successfully")
        print(f"User ID: {login_response.get('current_user', {}).get('uid')}")
        csrf_token = login_response.get('csrf_token')
        print(f"CSRF Token received: {csrf_token[:20] if csrf_token else 'None'}...")
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return
    
    # Step 2: Test API call with session cookie
    print("\n2. Testing API call with session...")
    
    api_url = "https://acleddata.com/api/acled/read"
    
    params = {
        "limit": 5
    }
    
    # Use the same session which has the authentication cookie
    response = session.get(api_url, params=params)
    
    print(f"API response status: {response.status_code}")
    
    if response.status_code == 200:
        try:
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
        except json.JSONDecodeError:
            print("Response is not JSON, showing first 500 chars:")
            print(response.text[:500])
    else:
        print(f"✗ API call failed: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    
    # Step 3: Test with country filter
    print("\n3. Testing with country filter (Georgia)...")
    
    params = {
        "country": "Georgia",
        "limit": 10,
        "_format": "json"
    }
    
    response = session.get(api_url, params=params)
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"✓ Country-specific call successful!")
            print(f"Number of Georgia events: {len(data.get('data', []))}")
            
            if data.get('data'):
                print("\nGeorgia events summary:")
                for i, event in enumerate(data['data'][:3], 1):
                    print(f"  {i}. {event.get('event_date')} - {event.get('event_type')} in {event.get('location')}")
        except json.JSONDecodeError:
            print("Response is not JSON")
    else:
        print(f"✗ Country filter failed: {response.status_code}")

if __name__ == "__main__":
    test_cookie_auth()