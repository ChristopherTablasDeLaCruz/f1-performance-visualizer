"""
Analyzes driver performance by comparing Qualifying pace vs. Race pace.
"""

import pandas as pd

def calculate_qualifying_race_delta(quali_session, race_session) -> pd.DataFrame:
    """
    Calculates the pace deficit between Qualifying (1-lap speed) and Race (long-run average).
    Also correlates this delta with positions gained or lost.

    Args:
        quali_session: FastF1 Session object for Qualifying.
        race_session: FastF1 Session object for the Race.

    Returns:
        pd.DataFrame: Merged data containing pace deltas and position changes, 
                      sorted by smallest time delta.
    """
    # Filter for representative laps
    # Qualifying: Use absolute fastest laps (pick_quicklaps handles yellow flags)
    quali_laps = quali_session.laps.pick_quicklaps()
    
    # Race: Exclude pit stops (in/out laps) and safety car variance
    race_laps = race_session.laps.pick_wo_box().pick_quicklaps()
    
    if quali_laps.empty or race_laps.empty:
        raise ValueError("Insufficient lap data for analysis.")

    # Calculate Pace Metrics
    best_qual_laps = quali_laps.groupby("Driver")["LapTime"].min().dropna()
    avg_race_laps = race_laps.groupby("Driver")["LapTime"].mean().dropna()
    
    pace_df = pd.DataFrame({
        "QualTime": best_qual_laps,
        "RaceAvgTime": avg_race_laps
    })
    
    # Calculate the "Race Pace Deficit" (Race Avg - Qual Best)
    pace_df["DeltaTime"] = (pace_df["RaceAvgTime"] - pace_df["QualTime"]).dt.total_seconds()
    pace_df = pace_df.reset_index()
    
    # 3. specific position data
    results = race_session.results.copy()
    
    # Handle FastF1 column naming variations
    pos_col = 'Position' if 'Position' in results.columns else 'ClassifiedPosition'
    grid_col = 'GridPosition'
    
    if pos_col not in results.columns:
        raise ValueError(f"Position column missing. Available: {results.columns.tolist()}")

    # Rename 'Abbreviation' to 'Driver' to match the lap data join key
    pos_df = results[['Abbreviation', grid_col, pos_col]].rename(columns={
        'Abbreviation': 'Driver',
        grid_col: 'GridPosition',
        pos_col: 'FinishPosition'
    })
    
    pos_df["PositionDelta"] = pos_df["GridPosition"] - pos_df["FinishPosition"]

    # 4. Merge and Sort
    final_df = pace_df.merge(pos_df, on="Driver", how="inner")
    
    if final_df.empty:
        raise ValueError("No matching drivers found between qualifying and race data.")

    return final_df.sort_values("DeltaTime")

def analyze_performance(quali_session, race_session):
    """
    Legacy wrapper for calculate_qualifying_race_delta.
    """
    return calculate_qualifying_race_delta(quali_session, race_session)