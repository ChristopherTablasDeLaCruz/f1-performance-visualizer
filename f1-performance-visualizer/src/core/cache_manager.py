"""
F1 data caching system.

Saves race data locally so we don't have to download it every time.
Makes the app much faster after the first load of each race.
"""

import os
import pandas as pd
import fastf1
from datetime import datetime
import streamlit as st

class F1DataCache:
    def __init__(self, cache_dir=".f1_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_path(self, year, race_name, session_type):
        """Build the file path where we'll save this race data."""
        safe_name = race_name.replace(" ", "_").lower()
        return os.path.join(
            self.cache_dir, 
            f"{year}_{safe_name}_{session_type}.parquet"
        )
    
    def is_cache_valid(self, cache_path, max_age_days=30):
        """Check if we have recent cached data for this race."""
        if not os.path.exists(cache_path):
            return False
        
        # Don't use really old cached data
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        age = datetime.now() - file_time
        return age.days < max_age_days
    
    @st.cache_data(show_spinner=False)
    def load_race_data(_self, year, race_name):
        """
        Get race data, either from cache or fresh from FastF1.
        
        First time: Downloads from F1 and saves locally (20-30 seconds)
        Later times: Loads from cache (under 2 seconds)
        """
        cache_path = _self.get_cache_path(year, race_name, 'race')
        
        # Try loading from our saved file first
        if _self.is_cache_valid(cache_path):
            try:
                data = pd.read_parquet(cache_path)
                return data.iloc[0].to_dict()
            except Exception as e:
                st.warning(f"Cache read failed: {e}")
                pass
        
        # Download fresh data from FastF1
        session = fastf1.get_session(year, race_name, 'R')
        session.load()
        
        # Save the columns we need for our dashboard
        results_columns = session.results.columns.tolist()
        
        # Package up the essential race data
        race_data = {
            'results': session.results.to_dict('records'),
            'results_columns': results_columns,  # Keep track of what columns we have
            'laps': session.laps[
                ['Driver', 'DriverNumber', 'LapNumber', 'LapTime', 
                 'Position', 'Compound', 'TyreLife', 'Stint']
            ].dropna(subset=['Driver', 'LapNumber']).to_dict('records'),
            'weather': [],
            'event_info': {
                'name': session.event['EventName'],
                'date': str(session.date),
                'total_laps': session.total_laps if hasattr(session, 'total_laps') else len(session.laps['LapNumber'].unique())
            }
        }
        
        # Add weather info if we can get it
        if hasattr(session, 'weather_data') and session.weather_data is not None and not session.weather_data.empty:
            try:
                race_data['weather'] = session.weather_data[
                    ['Time', 'AirTemp', 'TrackTemp', 'WindSpeed', 'Rainfall']
                ].to_dict('records')
            except:
                pass
        
        # Save to cache for next time
        df = pd.DataFrame([race_data])
        df.to_parquet(cache_path, compression='snappy')
        
        return race_data
    
    @st.cache_data(show_spinner=False)
    def load_quali_data(_self, year, race_name):
        """
        Get qualifying session data 
        Uses the same caching system as race data - fast loading after 
        the first download. 
        """

        cache_path = _self.get_cache_path(year, race_name, 'quali')
        
        # Check our cache first
        if _self.is_cache_valid(cache_path):
            try:
                data = pd.read_parquet(cache_path)
                return data.iloc[0].to_dict()
            except:
                pass
        
        # Get fresh qualifying data
        session = fastf1.get_session(year, race_name, 'Q')
        session.load()
        
        # Package the qualifying essentials
        quali_data = {
            'results': session.results.to_dict('records'),
            'laps': session.laps[
                ['Driver', 'DriverNumber', 'LapNumber', 'LapTime', 
                 'Position', 'Compound', 'TyreLife', 'Stint']
            ].dropna(subset=['Driver', 'LapNumber']).to_dict('records'),
            'event_info': {
                'name': session.event['EventName'],
                'date': str(session.date)
            }
        }
        
        # Cache it for later
        df = pd.DataFrame([quali_data])
        df.to_parquet(cache_path, compression='snappy')
        
        return quali_data