"""
Race summary utilities.

Pulls together the key race info that users want to see first:
winner, podium, fastest lap, and weather conditions.
"""

import pandas as pd

def get_race_summary(race_session):
    """
    Get the essential race info for the dashboard summary.
    
    Grabs winner, podium finishers, fastest lap, and weather
    so users can quickly see what happened in the race.

    Args:
        race_session: FastF1 race session with results and lap data loaded

    Returns:
        Dictionary with race highlights ready for display
    """
    summary = {}

    # Find the race winner
    winner_row = race_session.results[race_session.results['Position'] == 1].iloc[0]
    summary["Winner"] = f"{winner_row['Abbreviation']} ({winner_row['TeamName']})"

    # Get the podium finishers
    podium = race_session.results[race_session.results['Position'] <= 3]
    summary["Podium"] = list(podium.sort_values("Position")["Abbreviation"])

    # Find fastest lap info
    fl_lap = race_session.laps.pick_fastest()
    if fl_lap is not None:
        lap_time = pd.to_timedelta(fl_lap['LapTime'])
        # Format as M:SS.mmm
        formatted_lap_time = f"{int(lap_time.total_seconds() // 60)}:{lap_time.total_seconds() % 60:.3f}"
        driver_code = race_session.get_driver(fl_lap['DriverNumber'])['Abbreviation']
        summary["Fastest Lap"] = f"{driver_code} ({formatted_lap_time}) on Lap {int(fl_lap['LapNumber'])}"
    else:
        summary["Fastest Lap"] = "N/A"

    # Total race distance
    summary["Total Laps"] = race_session.total_laps

    # Weather summary
    weather_data = race_session.weather_data
    if weather_data is not None and not weather_data.empty:
        avg_air_temp = int(weather_data["AirTemp"].mean())
        avg_track_temp = int(weather_data["TrackTemp"].mean())
        wind_speed_kmh = round(weather_data["WindSpeed"].mean() * 3.6, 1)  # Convert m/s to km/h
        rainfall = "Yes" if weather_data["Rainfall"].any() else "No"

        summary["Weather"] = (
            f"🌡️ Air: {avg_air_temp}°C | 🛣️ Track: {avg_track_temp}°C | "
            f"💨 Wind: {wind_speed_kmh} km/h | 🌧️ Rain: {rainfall}"
        )
    else:
        summary["Weather"] = "No weather data available"

    return summary