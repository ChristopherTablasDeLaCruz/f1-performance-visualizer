import pandas as pd

def get_race_summary(race_session):
    """
    Generate a summary of key race information including winner, podium, fastest lap,
    total laps, and average weather conditions.

    Parameters:
        race_session: FastF1 race session object (must have results and telemetry loaded)

    Returns:
        dict: A dictionary containing race summary statistics for display in the dashboard.
    """
    summary = {}

    # Winner
    winner_row = race_session.results[race_session.results['Position'] == 1].iloc[0]
    summary["Winner"] = f"{winner_row['Abbreviation']} ({winner_row['TeamName']})"

    # Top 3 finishers
    podium = race_session.results[race_session.results['Position'] <= 3]
    summary["Podium"] = list(podium.sort_values("Position")["Abbreviation"])

    # fastest lap data
    fl_lap = race_session.laps.pick_fastest()
    if fl_lap is not None:
        lap_time = pd.to_timedelta(fl_lap['LapTime'])
        # Format time as M:SS.mmm
        formatted_lap_time = f"{int(lap_time.total_seconds() // 60)}:{lap_time.total_seconds() % 60:.3f}"
        driver_code = race_session.get_driver(fl_lap['DriverNumber'])['Abbreviation']
        summary["Fastest Lap"] = f"{driver_code} ({formatted_lap_time}) on Lap {int(fl_lap['LapNumber'])}"
    else:
        summary["Fastest Lap"] = "N/A"

    # Total Laps
    summary["Total Laps"] = race_session.total_laps

    # Average weather metrics 
    weather_data = race_session.weather_data
    if weather_data is not None and not weather_data.empty:
        avg_air_temp = int(weather_data["AirTemp"].mean())
        avg_track_temp = int(weather_data["TrackTemp"].mean())
        wind_speed_kmh = round(weather_data["WindSpeed"].mean() * 3.6, 1)  # 1 m/s = 3.6 km/h
        rainfall = "Yes" if weather_data["Rainfall"].any() else "No"

        summary["Weather"] = (
            f"🌡️ Air: {avg_air_temp}°C | 🛣️ Track: {avg_track_temp}°C | "
            f"💨 Wind: {wind_speed_kmh} km/h | 🌧️ Rain: {rainfall}"
        )
    else:
        summary["Weather"] = "No weather data available"

    return summary