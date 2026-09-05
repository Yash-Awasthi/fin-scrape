"""
ACLED API Client
Handles authentication and data retrieval from ACLED (Armed Conflict Location & Event Data Project)
"""

import requests
import json
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time


class ACLEDClient:
    """Client for interacting with the ACLED API"""
    
    def __init__(self, username: str, password: str):
        """
        Initialize ACLED API client
        
        Args:
            username: Your ACLED account email
            password: Your ACLED account password
        """
        self.username = username
        self.password = password
        self.base_url = "https://acleddata.com/api"
        self.token_url = "https://acleddata.com/oauth/token"
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        
    def authenticate(self) -> str:
        """
        Get access token using OAuth authentication
        
        Returns:
            Access token string
        """
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        data = {
            'username': self.username,
            'password': self.password,
            'grant_type': 'password',
            'client_id': 'acled'
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data['refresh_token']
            # Token expires in 24 hours (86400 seconds)
            self.token_expiry = datetime.now() + timedelta(seconds=token_data['expires_in'])
            
            print("✓ Authentication successful")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to authenticate: {e}")
    
    def refresh_access_token(self) -> str:
        """
        Refresh the access token using the refresh token
        
        Returns:
            New access token string
        """
        if not self.refresh_token:
            raise Exception("No refresh token available. Please authenticate first.")
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        data = {
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token',
            'client_id': 'acled'
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data['refresh_token']
            self.token_expiry = datetime.now() + timedelta(seconds=token_data['expires_in'])
            
            print("✓ Token refreshed successfully")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to refresh token: {e}")
    
    def ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.access_token:
            self.authenticate()
        elif self.token_expiry and datetime.now() >= self.token_expiry:
            print("Token expired, refreshing...")
            self.refresh_access_token()
    
    def get_data(self, 
                 endpoint: str = "acled",
                 format: str = "json",
                 **filters) -> Dict[str, Any]:
        """
        Retrieve data from ACLED API
        
        Args:
            endpoint: API endpoint (acled, deleted, cast)
            format: Response format (json, csv, xml)
            **filters: Query filters (country, event_date, limit, etc.)
            
        Returns:
            API response data
        """
        self.ensure_authenticated()
        
        # Build URL
        url = f"{self.base_url}/{endpoint}/read"
        
        # Add format if not JSON (JSON is default)
        if format != "json":
            url += f"?_format={format}"
        else:
            url += "?"
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, params=filters, headers=headers)
            response.raise_for_status()
            
            if format == "json":
                return response.json()
            else:
                return response.text
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to retrieve data: {e}")
    
    def get_events_by_country_and_date(self,
                                      country: str,
                                      start_date: str,
                                      end_date: str,
                                      limit: Optional[int] = None,
                                      fields: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Get events for a specific country within a date range
        
        Args:
            country: Country name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum number of events to return
            fields: List of fields to include in response
            
        Returns:
            DataFrame with event data
        """
        filters = {
            'country': country,
            'event_date': f"{start_date}|{end_date}",
            'event_date_where': 'BETWEEN'
        }
        
        if limit:
            filters['limit'] = limit
            
        if fields:
            filters['fields'] = '|'.join(fields)
        
        response = self.get_data(**filters)
        
        if response.get('status') == 200:
            df = pd.DataFrame(response.get('data', []))
            print(f"✓ Retrieved {len(df)} events")
            return df
        else:
            raise Exception(f"API request failed: {response}")
    
    def get_recent_events(self, 
                         countries: Optional[List[str]] = None,
                         days_back: int = 7,
                         event_types: Optional[List[str]] = None,
                         limit: Optional[int] = 1000) -> pd.DataFrame:
        """
        Get recent events from specified countries
        
        Args:
            countries: List of country names
            days_back: Number of days to look back
            event_types: List of event types to filter
            limit: Maximum number of events
            
        Returns:
            DataFrame with event data
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        filters = {
            'event_date': f"{start_date}|{end_date}",
            'event_date_where': 'BETWEEN',
            'limit': limit
        }
        
        if countries:
            # Handle multiple countries with OR logic
            country_filter = ':OR:country='.join(countries)
            filters['country'] = country_filter
            
        if event_types:
            event_filter = ':OR:event_type='.join(event_types)
            filters['event_type'] = event_filter
        
        response = self.get_data(**filters)
        
        if response.get('status') == 200:
            df = pd.DataFrame(response.get('data', []))
            print(f"✓ Retrieved {len(df)} recent events")
            return df
        else:
            raise Exception(f"API request failed: {response}")
    
    def search_events(self, **custom_filters) -> pd.DataFrame:
        """
        Search events with custom filters
        
        Args:
            **custom_filters: Any valid ACLED API filters
            
        Returns:
            DataFrame with event data
        """
        response = self.get_data(**custom_filters)
        
        if response.get('status') == 200:
            df = pd.DataFrame(response.get('data', []))
            print(f"✓ Retrieved {len(df)} events")
            return df
        else:
            raise Exception(f"API request failed: {response}")


def main():
    """Example usage of ACLED API client"""
    
    # You'll need to replace these with your actual credentials
    USERNAME = "your_email@example.com"
    PASSWORD = "your_password"
    
    # Initialize client
    client = ACLEDClient(USERNAME, PASSWORD)
    
    # Example 1: Get events from Georgia between specific dates
    print("\n1. Getting events from Georgia (2022-2023)...")
    georgia_events = client.get_events_by_country_and_date(
        country="Georgia",
        start_date="2022-01-01",
        end_date="2023-02-01",
        limit=100,
        fields=['event_id_cnty', 'event_date', 'event_type', 'location', 'fatalities']
    )
    
    if not georgia_events.empty:
        print(f"Sample events from Georgia:")
        print(georgia_events.head())
        print(f"\nEvent types distribution:")
        print(georgia_events['event_type'].value_counts())
    
    # Example 2: Get recent events from multiple countries
    print("\n2. Getting recent events from Caucasus region...")
    recent_events = client.get_recent_events(
        countries=["Georgia", "Armenia", "Azerbaijan"],
        days_back=30,
        event_types=["Protests", "Riots"],
        limit=500
    )
    
    if not recent_events.empty:
        print(f"\nRecent protest/riot events in Caucasus:")
        print(recent_events[['country', 'event_date', 'event_type', 'location']].head(10))
    
    # Example 3: Custom search with specific filters
    print("\n3. Custom search for high-fatality events...")
    custom_search = client.search_events(
        region="Caucasus and Central Asia",
        year=2023,
        fatalities="5|100",
        fatalities_where="BETWEEN",
        limit=50
    )
    
    if not custom_search.empty:
        print(f"\nHigh-fatality events in 2023:")
        print(custom_search[['country', 'event_date', 'event_type', 'fatalities', 'location']].head())
    
    # Save data to CSV
    if not georgia_events.empty:
        georgia_events.to_csv('georgia_events_2022_2023.csv', index=False)
        print("\n✓ Data saved to georgia_events_2022_2023.csv")


if __name__ == "__main__":
    main()