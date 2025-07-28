import os
import json
import csv
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import requests

def get_congress_members():
    """Fetch current members of Congress from the Congress.gov API."""
    # Congress.gov API endpoint for current members
    url = "https://api.congress.gov/v3/member"
    
    # You'll need to sign up for an API key at https://api.congress.gov/signup/
    api_key = os.getenv('CONGRESS_GOV_API_KEY')
    if not api_key:
        raise ValueError("Please set the CONGRESS_GOV_API_KEY environment variable")
    
    headers = {
        'X-API-Key': api_key
    }
    
    params = {
        'limit': 250,  # Adjust based on the actual number of members
        'offset': 0
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def process_members_data(data):
    """Process the raw API response into a cleaner format."""
    if not data or 'members' not in data:
        return []
    
    processed = []
    for member in data['members']:
        processed.append({
            'id': member.get('id'),
            'name': f"{member.get('firstName', '')} {member.get('lastName', '')}".strip(),
            'firstName': member.get('firstName'),
            'lastName': member.get('lastName'),
            'party': member.get('party'),
            'state': member.get('state'),
            'district': member.get('district'),
            'chamber': member.get('chamber'),
            'title': member.get('title'),
            'url': member.get('url'),
            'inOffice': member.get('inOffice', False),
            'lastUpdated': datetime.now().isoformat()
        })
    return processed

def save_to_json(data, filename):
    """Save data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def save_to_csv(data, filename):
    """Save data to a CSV file."""
    if not data:
        return
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

def main():
    # Load environment variables
    load_dotenv()
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Get current date for filenames
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Fetch and process data
    print("Fetching Congress member data...")
    raw_data = get_congress_members()
    
    if raw_data:
        processed_data = process_members_data(raw_data)
        
        if processed_data:
            # Save data in multiple formats
            json_filename = f'data/congress_members_{today}.json'
            csv_filename = f'data/congress_members_{today}.csv'
            
            save_to_json(processed_data, json_filename)
            save_to_csv(processed_data, csv_filename)
            
            print(f"Data saved to {json_filename} and {csv_filename}")
            
            # Also save a latest version
            save_to_json(processed_data, 'data/congress_members_latest.json')
            save_to_csv(processed_data, 'data/congress_members_latest.csv')
            print("Latest data also saved as 'latest' version")
        else:
            print("No data to process")
    else:
        print("Failed to fetch data")

if __name__ == "__main__":
    main()
