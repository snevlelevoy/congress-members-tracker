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
        data = response.json()
        
        # Debug: Print the first member to inspect the structure
        if data and 'members' in data and len(data['members']) > 0:
            print("\nSample member data structure:")
            import json
            print(json.dumps(data['members'][0], indent=2))
            
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def process_members_data(data):
    """Process the raw API response into a cleaner format."""
    if not data or 'members' not in data:
        return []
    
    processed = []
    for member in data['members']:
        # Extract first and last name from the 'name' field
        name_parts = member.get('name', '').split(',')
        last_name = name_parts[0].strip() if len(name_parts) > 0 else ''
        first_name = name_parts[1].strip() if len(name_parts) > 1 else ''
        
        # Get the most recent term to determine current chamber and status
        current_term = None
        if 'terms' in member and 'item' in member['terms'] and len(member['terms']['item']) > 0:
            current_term = member['terms']['item'][-1]  # Get the most recent term
        
        processed.append({
            'id': member.get('bioguideId'),
            'name': member.get('name', '').strip(),
            'firstName': first_name,
            'lastName': last_name,
            'party': member.get('partyName', ''),
            'state': member.get('state', ''),
            'district': member.get('district'),
            'chamber': current_term.get('chamber') if current_term else '',
            'title': 'Senator' if current_term and 'Senate' in current_term.get('chamber', '') else 'Representative',
            'url': member.get('url', ''),
            'inOffice': current_term is not None,
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
