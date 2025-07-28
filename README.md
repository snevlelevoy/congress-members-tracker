# Congress Members Tracker

This project fetches and stores information about current members of the U.S. Congress using the Congress.gov API.

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Get an API key from [Congress.gov API](https://api.congress.gov/signup/)
4. Create a `.env` file in the project root and add your API key:
   ```
   CONGRESS_GOV_API_KEY=your_api_key_here
   ```

## Usage

To fetch the latest Congress member data and save it to JSON and CSV files:

```bash
python fetch_members.py
```

The script will create a `data` directory and save the files:
- `data/congress_members_YYYY-MM-DD.json`
- `data/congress_members_YYYY-MM-DD.csv`
- `data/congress_members_latest.json`
- `data/congress_members_latest.csv`

## Data Fields

The saved files include the following information for each member:
- `id`: Unique identifier
- `name`: Full name
- `firstName`: First name
- `lastName`: Last name
- `party`: Political party
- `state`: State represented
- `district`: District number (for House members)
- `chamber`: Chamber (House or Senate)
- `title`: Official title
- `url`: URL to member's page
- `inOffice`: Boolean indicating if currently in office
- `lastUpdated`: Timestamp of when the data was fetched

## Automation

To run this script daily, you can set up a cron job:

```bash
# Edit crontab
crontab -e

# Add this line to run the script daily at 3 AM
0 3 * * * cd /path/to/congress-members-tracker && /usr/bin/python3 /path/to/congress-members-tracker/fetch_members.py >> /path/to/congress-members-tracker/cron.log 2>&1
```

Or use GitHub Actions by creating a workflow file (see `.github/workflows/update_data.yml`).

## License

MIT
