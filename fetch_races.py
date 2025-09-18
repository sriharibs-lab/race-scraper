#!/usr/bin/env python3
"""
RunSignUp API Race Fetcher

Fetches running races from RunSignUp API for Washington, Oregon, and California.
Includes Unsplash integration for city skyline images and comprehensive data transformation.
"""

import requests
import json
import logging
import time
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import sys
import os


class RunSignUpRaceFetcher:
    """Fetches and processes race data from RunSignUp API."""
    
    def __init__(self):
        """Initialize the race fetcher."""
        self.base_url = "https://api.runsignup.com/rest/races"
        self.unsplash_url = "https://api.unsplash.com/search/photos"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('race_fetcher.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Target states
        self.target_states = ['WA', 'OR', 'CA']
        self.state_names = {
            'WA': 'Washington',
            'OR': 'Oregon', 
            'CA': 'California'
        }
        
        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # Get Unsplash API key from environment
        self.unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
        if not self.unsplash_key:
            self.logger.warning("UNSPLASH_ACCESS_KEY not found in environment variables")
    
    def fetch_races_for_state(self, state: str, page: int = 1) -> Optional[Dict]:
        """Fetch races for a specific state and page."""
        try:
            params = {
                'format': 'json',
                'state': state,
                'events': 'T',
                'page': page,
                'results_per_page': 50
            }
            
            self.logger.info(f"Fetching races for {self.state_names[state]} ({state}) - page {page}")
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching races for {state} page {page}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON for {state} page {page}: {e}")
            return None
    
    def get_city_image(self, city: str, state: str) -> str:
        """Get city skyline image from Unsplash."""
        if not self.unsplash_key:
            return f"https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=800&h=600&fit=crop&crop=center"
        
        try:
            query = f"{city} {self.state_names[state]} skyline"
            params = {
                'query': query,
                'per_page': 1,
                'orientation': 'landscape'
            }
            headers = {
                'Authorization': f'Client-ID {self.unsplash_key}'
            }
            
            response = self.session.get(self.unsplash_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('results'):
                return data['results'][0]['urls']['regular']
            
        except Exception as e:
            self.logger.warning(f"Error fetching image for {city}, {state}: {e}")
        
        # Fallback image
        return f"https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=800&h=600&fit=crop&crop=center"
    
    def determine_difficulty(self, distance: str) -> str:
        """Determine difficulty level based on distance."""
        distance_lower = distance.lower()
        
        if any(x in distance_lower for x in ['1k', '1 mile', '1mi', 'fun run', 'kids']):
            return 'Beginner'
        elif any(x in distance_lower for x in ['5k', '3.1', '3 mile']):
            return 'Easy'
        elif any(x in distance_lower for x in ['10k', '6.2', '6 mile']):
            return 'Moderate'
        elif any(x in distance_lower for x in ['half marathon', '13.1', '15k']):
            return 'Hard'
        elif any(x in distance_lower for x in ['marathon', '26.2', 'full']):
            return 'Expert'
        elif any(x in distance_lower for x in ['ultra', '50k', '50 mile', '100k', '100 mile']):
            return 'Extreme'
        else:
            return 'Moderate'
    
    def has_kids_race(self, events: List[Dict]) -> bool:
        """Check if race has kids/family events."""
        for event in events:
            event_name = event.get('name', '') or ''
            event_name = event_name.lower()
            if any(keyword in event_name for keyword in ['kids', 'children', 'family', 'youth', 'junior']):
                return True
        return False
    
    def transform_race_data(self, race: Dict, state: str) -> List[Dict[str, Any]]:
        """Transform race data to required format."""
        transformed_races = []
        
        try:
            race_id = race.get('race_id', 0)
            name = race.get('name', 'Unknown Race')
            next_date = race.get('next_date', '')
            
            # Extract city from address
            address = race.get('address', {})
            city = address.get('city', 'Unknown') if address else 'Unknown'
            
            description = race.get('description', '')
            registration_url = race.get('url', '')
            events = race.get('events', [])
            
            # Get coordinates
            latitude = race.get('latitude', 0.0)
            longitude = race.get('longitude', 0.0)
            
            # Get city image
            image_url = self.get_city_image(city, state)
            
            # Process each event/distance
            for event in events:
                distance = event.get('distance', 'Unknown')
                difficulty = self.determine_difficulty(distance)
                
                transformed_race = {
                    'id': f"{race_id}_{event.get('event_id', 0)}",
                    'name': name,
                    'date': next_date,
                    'city': city,
                    'state': state,
                    'distance': distance,
                    'difficulty': difficulty,
                    'description': description,
                    'imageUrl': image_url,
                    'latitude': latitude,
                    'longitude': longitude,
                    'hasKidsRace': self.has_kids_race(events),
                    'registrationUrl': registration_url
                }
                
                transformed_races.append(transformed_race)
            
            # If no events, create a single race entry
            if not events:
                transformed_race = {
                    'id': str(race_id),
                    'name': name,
                    'date': next_date,
                    'city': city,
                    'state': state,
                    'distance': 'Unknown',
                    'difficulty': 'Moderate',
                    'description': description,
                    'imageUrl': image_url,
                    'latitude': latitude,
                    'longitude': longitude,
                    'hasKidsRace': False,
                    'registrationUrl': registration_url
                }
                transformed_races.append(transformed_race)
                
        except Exception as e:
            self.logger.error(f"Error transforming race data: {e}")
        
        return transformed_races
    
    def filter_future_races(self, races: List[Dict]) -> List[Dict]:
        """Filter races to only include future dates."""
        today = date.today()
        future_races = []
        
        for race in races:
            try:
                race_date_str = race.get('date', '')
                if race_date_str:
                    # Parse date string (format: MM/DD/YYYY)
                    race_date = datetime.strptime(race_date_str, '%m/%d/%Y').date()
                    if race_date >= today:
                        future_races.append(race)
                else:
                    # Include races with unknown dates
                    future_races.append(race)
            except ValueError:
                # Include races with unparseable dates
                future_races.append(race)
        
        return future_races
    
    def fetch_all_races(self) -> List[Dict[str, Any]]:
        """Fetch all races for all target states."""
        all_races = []
        
        for state in self.target_states:
            self.logger.info(f"Processing {self.state_names[state]} ({state})")
            page = 1
            
            while True:
                data = self.fetch_races_for_state(state, page)
                if not data or 'races' not in data:
                    break
                
                races = data['races']
                if not races:
                    break
                
                self.logger.info(f"Processing {len(races)} races from page {page}")
                
                for race_item in races:
                    # Extract the actual race data from the nested structure
                    race = race_item.get('race', race_item)
                    transformed_races = self.transform_race_data(race, state)
                    all_races.extend(transformed_races)
                
                page += 1
                time.sleep(0.5)  # Be respectful to API
        
        # Filter for future races
        future_races = self.filter_future_races(all_races)
        
        self.logger.info(f"Total races found: {len(all_races)}")
        self.logger.info(f"Future races: {len(future_races)}")
        
        return future_races
    
    def save_to_json(self, races: List[Dict[str, Any]], filename: str = 'races.json') -> None:
        """Save races data to JSON file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(races, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(races)} races to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {e}")
    
    def run(self) -> None:
        """Main method to run the race fetcher."""
        self.logger.info("Starting RunSignUp race fetcher...")
        self.logger.info(f"Target states: {', '.join(self.target_states)}")
        
        try:
            races = self.fetch_all_races()
            self.save_to_json(races)
            self.logger.info("Race fetching completed successfully!")
            
        except Exception as e:
            self.logger.error(f"Race fetching failed: {e}")
            raise


def main():
    """Main function to run the race fetcher."""
    print("RunSignUp Race Fetcher")
    print("=" * 40)
    print("Fetching race data for Washington, Oregon, and California")
    print("Using RunSignUp API with Unsplash integration")
    print()
    
    fetcher = RunSignUpRaceFetcher()
    fetcher.run()


if __name__ == "__main__":
    main()
