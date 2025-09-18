# RunSignUp Race Fetcher

A Python script that fetches running race data from the RunSignUp API for Washington, Oregon, and California, with Unsplash integration for city skyline images.

## Features

- **RunSignUp API Integration**: Fetches race data from the public RunSignUp API
- **Multi-State Support**: Covers Washington, Oregon, and California
- **Pagination Handling**: Automatically handles pagination (50 races per page)
- **Unsplash Integration**: Generates city skyline images for each race location
- **Date Filtering**: Only includes races from today forward
- **Comprehensive Data**: Extracts race name, date, location, distances, difficulty, and more
- **Error Handling**: Robust error handling and logging
- **Clean JSON Output**: Structured output matching specified format

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Set up Unsplash API key for better city images:
```bash
export UNSPLASH_ACCESS_KEY="your_unsplash_access_key_here"
```

## Usage

Run the script:
```bash
python fetch_races.py
```

This will:
1. Fetch race data from RunSignUp API for WA, OR, and CA
2. Process and transform the data
3. Generate city skyline images from Unsplash
4. Filter for future races only
5. Save results to `races.json`

## Output Format

The script generates a `races.json` file with the following structure:

```json
[
  {
    "id": "12345_67890",
    "name": "Seattle Marathon",
    "date": "2024-11-24",
    "city": "Seattle",
    "state": "WA",
    "distance": "Marathon",
    "difficulty": "Expert",
    "description": "Scenic marathon through Seattle...",
    "imageUrl": "https://images.unsplash.com/photo-...",
    "latitude": 47.6062,
    "longitude": -122.3321,
    "hasKidsRace": false,
    "registrationUrl": "https://runsignup.com/Race/12345"
  }
]
```

## Data Fields

- **id**: Unique identifier combining race_id and event_id
- **name**: Race name
- **date**: Race date (YYYY-MM-DD format)
- **city**: City name
- **state**: State abbreviation (WA, OR, CA)
- **distance**: Race distance
- **difficulty**: Calculated difficulty level (Beginner, Easy, Moderate, Hard, Expert, Extreme)
- **description**: Race description
- **imageUrl**: City skyline image from Unsplash
- **latitude**: Race location latitude
- **longitude**: Race location longitude
- **hasKidsRace**: Boolean indicating if race has kids/family events
- **registrationUrl**: Direct link to race registration

## Difficulty Levels

The script automatically determines difficulty based on distance:
- **Beginner**: 1K, 1 mile, fun runs, kids races
- **Easy**: 5K, 3.1 miles
- **Moderate**: 10K, 6.2 miles
- **Hard**: Half marathon, 13.1 miles, 15K
- **Expert**: Marathon, 26.2 miles
- **Extreme**: Ultra marathons, 50K+, 100K+

## Logging

The script creates detailed logs in `race_fetcher.log` including:
- API request status
- Data processing progress
- Error messages
- Summary statistics

## Error Handling

The script includes comprehensive error handling for:
- Network connectivity issues
- API rate limiting
- Invalid JSON responses
- Missing data fields
- Image fetching failures

## Notes

- The script respects API rate limits with built-in delays
- Unsplash integration is optional but recommended for better images
- All races are filtered to only include future dates
- The script handles pagination automatically for each state
