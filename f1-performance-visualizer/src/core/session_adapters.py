"""
Session adapters for cached F1 data.

Makes our cached data work with FastF1 functions that expect 
the original FastF1 data format. 
"""

import pandas as pd

# F1's 107% rule for filtering out crashes, pit stops, etc.
F1_OUTLIER_THRESHOLD = 1.07

class F1EventAdapter:
    """
    Makes cached event info work like FastF1 event objects.
    
    The problem: FastF1 functions access event data inconsistently.
    Some use event['EventName'], others use event.year
    
    The fix: Support both ways so nothing breaks.
    """
    def __init__(self, event_name, year, event_date=None):
        self.EventName = event_name  # For attribute access
        self.year = year
        
        # Set up event date for FastF1 compatibility
        if event_date:
            if isinstance(event_date, str):
                event_date = pd.to_datetime(event_date)
            self.EventDate = event_date
        else:
            # Default to January 1st if no date given
            self.EventDate = pd.to_datetime(f"{year}-01-01")
        
        # Dictionary for bracket access
        self._dict = {
            'EventName': event_name,
            'year': year,
            'EventDate': self.EventDate
        }
    
    def __getitem__(self, key):
        """Let code use event['EventName'] style."""
        return self._dict[key]
    
    def __contains__(self, key):
        """Let code check if 'EventName' in event."""
        return key in self._dict

class F1LapsAdapter:
    """
    Makes cached lap data work like FastF1's special lap objects.
    
    FastF1 has custom methods like pick_drivers() and pick_quicklaps()
    that our regular pandas DataFrames don't have. This adds them back.
    """
    def __init__(self, laps_df):
        self._df = laps_df.copy()
        
    def filter_by_driver(self, driver_code):
        """
        Get laps for just one driver.
        
        Args:
            driver_code: Driver like 'HAM', 'VER', 'LEC'
        
        Returns:
            New adapter with just that driver's laps
        """
        filtered_df = self._df[self._df['Driver'] == driver_code].copy()
        return F1LapsAdapter(filtered_df)
    
    def pick_drivers(self, driver_code):
        """
        Old FastF1 method name - redirects to the clearer version.
        
        Keeping this around so existing code doesn't break.
        """
        return self.filter_by_driver(driver_code)
    
    def filter_quick_laps_only(self):
        """
        Remove slow laps that aren't representative.
        
        In F1, laps that are 7% slower than the fastest are usually
        crashes, pit stops, or yellow flags - not normal racing.
        """
        if self._df.empty or 'LapTime' not in self._df.columns:
            return F1LapsAdapter(self._df)
        
        # Make sure lap times are in the right format
        df_copy = self._df.copy()
        if not pd.api.types.is_timedelta64_dtype(df_copy['LapTime']):
            df_copy['LapTime'] = pd.to_timedelta(df_copy['LapTime'])
        
        # Remove invalid laps
        valid_laps = df_copy.dropna(subset=['LapTime'])
        if valid_laps.empty:
            return F1LapsAdapter(valid_laps)
        
        # Apply F1's 107% rule
        fastest_time = valid_laps['LapTime'].min()
        threshold = fastest_time * F1_OUTLIER_THRESHOLD
        filtered_laps = valid_laps[valid_laps['LapTime'] <= threshold]
        return F1LapsAdapter(filtered_laps)
    
    def pick_quicklaps(self):
        """
        Old FastF1 method name - redirects to the clearer version.
        """
        return self.filter_quick_laps_only()
    
    def reset_index(self):
        """Reset the DataFrame index and return the data."""
        return self._df.reset_index(drop=True)
    
    def __getattr__(self, name):
        """Pass through any other requests to the DataFrame."""
        return getattr(self._df, name)
    
    def __getitem__(self, key):
        """Let code access data like a normal DataFrame."""
        return self._df[key]

class CachedF1Session:
    """
    Puts together cached data to look like a FastF1 session.
    
    Takes our cached dictionaries and wraps them with the adapters
    so existing analysis code works without changes.
    """
    def __init__(self, cached_data, event_name, year, event_date=None):
        self.laps = F1LapsAdapter(pd.DataFrame(cached_data['laps']))
        self.results = pd.DataFrame(cached_data['results'])
        self.event = F1EventAdapter(event_name, year, event_date)

# Keep old names working for any code that uses them
HybridEvent = F1EventAdapter  
LapsWrapper = F1LapsAdapter