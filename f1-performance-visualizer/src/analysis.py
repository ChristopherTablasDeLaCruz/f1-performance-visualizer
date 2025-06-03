import pandas as pd

def analyze_performance(quali_session, race_session) -> pd.DataFrame:
    """
    Analyze driver performance by comparing best qualifying laps to average race laps
    and tracking position changes from grid to race finish.

    Parameters:
        quali_session: FastF1 session object for qualifying
        race_session: FastF1 session object for the race

    Returns:
        pd.DataFrame: Combined performance and position change data for each driver.
    """
    # Get best qualifying laps
    quali_laps = quali_session.laps.pick_quicklaps()
    best_qual_laps = quali_laps.groupby("Driver")["LapTime"].min().dropna()

    # Get average race laps
    race_laps = race_session.laps.pick_quicklaps()
    avg_race_laps = race_laps.groupby("Driver")["LapTime"].mean().dropna()

    # Combine qualifying and race performance
    df = pd.DataFrame({
        "QualTime": best_qual_laps,
        "RaceAvgTime": avg_race_laps
    })
    df["DeltaTime"] = (df["RaceAvgTime"] - df["QualTime"]).dt.total_seconds()

    # Get grid and finishing positions
    results = race_session.results[["DriverNumber", "Position", "GridPosition"]].set_index("DriverNumber")

    # Map driver numbers to abbreviations
    driver_map = {
        drv: race_session.get_driver(drv)["Abbreviation"]
        for drv in race_session.drivers
    }

    pos_df = pd.DataFrame.from_dict(driver_map, orient="index", columns=["Driver"])
    pos_df["GridPosition"] = results["GridPosition"].values
    pos_df["FinishPosition"] = results["Position"].values
    pos_df["PositionDelta"] = pos_df["GridPosition"] - pos_df["FinishPosition"]

    # Combine performance and position data
    df = df.reset_index().merge(pos_df.reset_index(drop=True), on="Driver", how="inner")

    return df.sort_values("DeltaTime")
