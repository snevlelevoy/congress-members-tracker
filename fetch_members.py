import os
import json
import csv
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import requests

def get_congress_members():
    """Fetch current members of Congress from the Congress.gov API with pagination to get all members."""
    # Congress.gov API endpoint for current members
    url = "https://api.congress.gov/v3/member"
    
    # You'll need to sign up for an API key at https://api.congress.gov/signup/
    api_key = os.getenv('CONGRESS_GOV_API_KEY')
    if not api_key:
        raise ValueError("Please set the CONGRESS_GOV_API_KEY environment variable")
    
    all_members = []
    offset = 0
    limit = 250  # API limit per request
    
    print("Fetching congress members with pagination...")
    print(f"API URL: {url}")
    print(f"Using API key: {'Yes' if api_key else 'No'}")
    
    try:
        while True:
            params = {
                'format': 'json',  # Explicitly specify JSON format
                'limit': limit,
                'offset': offset,
                'api_key': api_key  # Add API key as parameter instead of header
            }
            
            print(f"\n=== API Request {(offset // limit) + 1} ===")
            print(f"Fetching members {offset + 1} to {offset + limit}...")
            print(f"Request params: {params}")
            
            # Remove API key from headers since we're passing it as parameter
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            print(f"Response status: {response.status_code}")
            print(f"Members in this batch: {len(data.get('members', []))}")
            
            # Check if we have members in the response
            if not data or 'members' not in data or len(data['members']) == 0:
                print("No more members found, stopping pagination.")
                break
            
            all_members.extend(data['members'])
            print(f"Total members so far: {len(all_members)}")
            
            # Debug: Print the first member structure only on first iteration
            if offset == 0 and len(data['members']) > 0:
                print("\nSample member data structure:")
                import json
                print(json.dumps(data['members'][0], indent=2))
            
            # Check if API response includes pagination info
            if 'pagination' in data:
                print(f"Pagination info: {data['pagination']}")
                # Use pagination info if available to determine if there are more results
                if 'count' in data['pagination'] and 'next' in data['pagination']:
                    if not data['pagination']['next']:
                        print("API indicates no more results available.")
                        break
            
            # If we got fewer members than the limit, we've reached the end
            if len(data['members']) < limit:
                print(f"Received {len(data['members'])} members (less than limit {limit}), stopping pagination.")
                break
                
            offset += limit
            print(f"Next offset will be: {offset}")
        
        print(f"\n=== FINAL RESULTS ===")
        print(f"Total members fetched: {len(all_members)}")
        
        # Return data in the same format as before
        return {'members': all_members}
        
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
        
        # Determine chamber and title
        chamber = current_term.get('chamber', '') if current_term else ''
        is_senator = 'Senate' in chamber
        
        # Process district - convert to int if it exists and is a number
        district = member.get('district')
        if district is not None:
            try:
                district = int(float(district))  # Handle both string and float inputs
            except (ValueError, TypeError):
                district = None
        
        # For senators, set district to None
        if is_senator:
            district = None
        
        # Get state and party with fallbacks
        state = member.get('state', '')
        party = member.get('partyName', '')
        
        # Create the member record
        member_data = {
            'id': member.get('bioguideId', ''),
            'name': member.get('name', '').strip(),
            'firstName': first_name,
            'lastName': last_name,
            'party': party,
            'state': state,
            'chamber': chamber,
            'title': 'Senator' if is_senator else 'Representative',
            'url': member.get('url', ''),
            'inOffice': current_term is not None,
            'lastUpdated': datetime.now().isoformat()
        }
        
        # Only add district for representatives
        if not is_senator:
            member_data['district'] = district
        
        processed.append(member_data)
    return processed

def save_to_json(data, filename):
    """Save data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def save_to_csv(data, filename):
    """Save data to a CSV file with proper handling of the district column."""
    if not data:
        return
    
    # Create a DataFrame
    df = pd.DataFrame(data)
    
    # Ensure district column is properly handled for both senators and representatives
    if 'district' in df.columns:
        # Convert district to nullable integer type (Int64) to handle None values
        df['district'] = pd.to_numeric(df['district'], errors='coerce')
        df['district'] = df['district'].astype('Int64')  # Capital I for nullable integer
    
    # Reorder columns to put district in a logical position
    columns = ['id', 'name', 'firstName', 'lastName', 'party', 'state', 'chamber', 'title']
    if 'district' in df.columns:
        columns.insert(6, 'district')  # Insert after state and before chamber
    columns.extend(['url', 'inOffice', 'lastUpdated'])
    
    # Only keep columns that exist in the DataFrame
    columns = [col for col in columns if col in df.columns]
    
    # Save to CSV with consistent column order
    df[columns].to_csv(filename, index=False)

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
