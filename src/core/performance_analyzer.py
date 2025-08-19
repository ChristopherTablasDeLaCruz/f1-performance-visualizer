"""
Performance analysis for F1 races.

Compares how drivers performed in qualifying vs the actual race.
"""

import pandas as pd

# F1's 107% rule: laps more than 7% slower are usually crashes/pit stops
F1_OUTLIER_THRESHOLD = 1.07

def calculate_qualifying_race_delta(quali_session, race_session) -> pd.DataFrame:
    """
    Compare qualifying pace vs race pace for each driver.
    
    Shows who kept their qualifying speed in the race vs who got slower.
    Also tracks position changes from grid to finish.

    Args:
        quali_session: Qualifying data (FastF1 session or cached dict)
        race_session: Race data (FastF1 session or cached dict)

    Returns:
        DataFrame with pace differences and position changes for each driver
    """
    # Handle both live FastF1 sessions and our cached data
    if hasattr(quali_session, 'laps'):
        # Working with live FastF1 session
        quali_laps = quali_session.laps.pick_quicklaps()
        race_laps = race_session.laps.pick_quicklaps()
        race_results = race_session.results
        race_drivers = race_session.drivers
        get_driver_func = race_session.get_driver
    else:
        # Working with our cached data, need to recreate the FastF1 logic
        quali_laps_df = pd.DataFrame(quali_session['laps'])
        race_laps_df = pd.DataFrame(race_session['laps'])
        
        # Make sure we have the basic data we need
        required_columns = ['LapTime', 'Driver']
        
        # Check qualifying data
        if not all(col in quali_laps_df.columns for col in required_columns):
            available_cols = quali_laps_df.columns.tolist()
            raise ValueError(f"Missing required columns in qualifying data. Available: {available_cols}, Required: {required_columns}")
        
        # Check race data
        if not all(col in race_laps_df.columns for col in required_columns):
            available_cols = race_laps_df.columns.tolist()
            raise ValueError(f"Missing required columns in race data. Available: {available_cols}, Required: {required_columns}")
        
        # Convert lap time text to actual time values
        try:
            quali_laps_df['LapTime'] = pd.to_timedelta(quali_laps_df['LapTime'])
            race_laps_df['LapTime'] = pd.to_timedelta(race_laps_df['LapTime'])
        except Exception as e:
            raise ValueError(f"Failed to convert LapTime to timedelta: {e}")
        
        # Remove slow laps (crashes, pit stops, etc.)
        def filter_quick_laps_only(laps_df):
            """Keep only representative racing laps."""
            if laps_df.empty or 'LapTime' not in laps_df.columns:
                return laps_df
            
            # Remove missing lap times
            valid_laps = laps_df.dropna(subset=['LapTime'])
            if valid_laps.empty:
                return valid_laps
            
            # Find the fastest lap time
            fastest_time = valid_laps['LapTime'].min()
            
            # Only keep laps within 7% of the fastest 
            threshold = fastest_time * F1_OUTLIER_THRESHOLD
            return valid_laps[valid_laps['LapTime'] <= threshold]
        
        quali_laps = filter_quick_laps_only(quali_laps_df)
        race_laps = filter_quick_laps_only(race_laps_df)
        race_results = pd.DataFrame(race_session['results'])
        
        # Build a lookup table for driver numbers to names
        driver_map = {}
        for _, row in race_results.iterrows():
            if 'DriverNumber' in row and 'Abbreviation' in row:
                driver_map[row['DriverNumber']] = row['Abbreviation']
        
        get_driver_func = lambda drv_num: {"Abbreviation": driver_map.get(drv_num, "UNK")}
        race_drivers = list(driver_map.keys())
    
    # Make sure data is valid
    if quali_laps.empty:
        raise ValueError("No valid qualifying lap data found")
    if race_laps.empty:
        raise ValueError("No valid race lap data found")
    
    # Get each driver's best qualifying lap
    best_qual_laps = quali_laps.groupby("Driver")["LapTime"].min().dropna()

    # Get each driver's average race lap time
    avg_race_laps = race_laps.groupby("Driver")["LapTime"].mean().dropna()

    # Combine qualifying and race times
    df = pd.DataFrame({
        "QualTime": best_qual_laps,
        "RaceAvgTime": avg_race_laps
    })
    
    if df.empty:
        raise ValueError("No matching drivers found between qualifying and race data")
    
    # Calculate how much slower they were in the race (the "delta")
    df["DeltaTime"] = (df["RaceAvgTime"] - df["QualTime"]).dt.total_seconds()

    # Figure out grid positions and finishing positions
    # Different data sources use different column names, so try a few
    position_col = 'Position' if 'Position' in race_results.columns else 'ClassifiedPosition'
    grid_col = 'GridPosition' if 'GridPosition' in race_results.columns else 'Position'
    
    if position_col not in race_results.columns:
        # Try other common names for finishing position
        position_candidates = ['ClassifiedPosition', 'FinishPosition', 'FinalPosition']
        position_col = next((col for col in position_candidates if col in race_results.columns), None)
        if position_col is None:
            raise ValueError(f"No position column found in results. Available columns: {race_results.columns.tolist()}")
    
    if grid_col not in race_results.columns:
        # Try other common names for starting position
        grid_candidates = ['GridPosition', 'StartPosition', 'Grid']
        grid_col = next((col for col in grid_candidates if col in race_results.columns), None)
        if grid_col is None:
            raise ValueError(f"No grid position column found in results. Available columns: {race_results.columns.tolist()}")
    
    results = race_results[["DriverNumber", position_col, grid_col]].set_index("DriverNumber")

    # Convert driver numbers to driver names
    driver_map = {
        drv: get_driver_func(drv)["Abbreviation"]
        for drv in race_drivers
    }

    pos_df = pd.DataFrame.from_dict(driver_map, orient="index", columns=["Driver"])
    pos_df["GridPosition"] = results[grid_col].values
    pos_df["FinishPosition"] = results[position_col].values
    pos_df["PositionDelta"] = pos_df["GridPosition"] - pos_df["FinishPosition"]

    # Put pace data and position data together
    df = df.reset_index().merge(pos_df.reset_index(drop=True), on="Driver", how="inner")

    # Sort by who maintained their pace best (smallest delta = best)
    return df.sort_values("DeltaTime")

def analyze_performance(quali_session, race_session):
    """
    Old function name - kept so existing code doesn't break.
    
    Use calculate_qualifying_race_delta() instead.
    """
    return calculate_qualifying_race_delta(quali_session, race_session)