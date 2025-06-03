import datetime
import streamlit as st
from fastf1 import get_event_schedule
import pandas as pd
from src.analysis import analyze_performance
from src.visualizer import plot_results
from src.strategy import plot_strategy_chart
from src.summary import get_race_summary
from src.laptimes import plot_driver_laptimes
from src.position_chart import plot_position_changes
from src.telemetry import plot_telemetry_charts_multiselect

@st.cache_data(show_spinner=False)
def get_cached_schedule(year):
    """Returns all completed race sessions for a given year"""
    schedule = get_event_schedule(year, include_testing=False)
    schedule["Session5Date"] = pd.to_datetime(schedule["Session5Date"], utc=True)
    now = pd.Timestamp.now(tz="UTC")
    completed_races = schedule[schedule["Session5Date"] < now]
    return completed_races

@st.cache_data(show_spinner=False)
def get_cached_session(year, grand_prix, session_type):
    from fastf1 import get_session
    session = get_session(year, grand_prix, session_type)
    session.load()
    return session

@st.cache_data(show_spinner="Analyzing performance...")
def get_cached_analysis(_quali_session, _race_session):
    return analyze_performance(_quali_session, _race_session)

@st.cache_data(show_spinner="Getting summary...")
def get_cached_summary(_race_session):
    return get_race_summary(_race_session)

@st.cache_data(show_spinner="Getting laptimes...")
def get_driver_laps(_race_session, driver_code):
    return _race_session.laps.pick_drivers(driver_code).pick_quicklaps().reset_index()

def main():
    """
    app.py

    Streamlit dashboard for visualizing F1 race data using FastF1.

    Features:
    - Select race season and Grand Prix
    - View race summary (winner, podium, weather, fastest lap)
    - Analyze performance delta between qualifying and race
    - Visualize tyre strategies per driver
    - Plot driver position changes and lap times
    - Compare telemetry between multiple driver-lap selections
    """
    st.set_page_config(page_title="F1 Race Dashboard", layout="wide")
    st.title("\U0001F3CE️ F1 Race Analysis Dashboard")

    # Select year (2018 earliest)
    current_year = datetime.datetime.now().year
    season_years = list(range(2018, current_year + 1))[::-1]
    default_year_index = season_years.index(2024)
    selected_year = st.selectbox("Select Season", season_years, index=default_year_index)

    # Select Grand Prix 
    try:
        schedule = get_cached_schedule(selected_year)
        schedule['Session5Date'] = pd.to_datetime(schedule['Session5Date'], errors='coerce')
        if selected_year == current_year:
            today = pd.Timestamp.now(tz='UTC')
            schedule = schedule[schedule['Session5Date'] < today]
        schedule = schedule.sort_values(by="Session5Date")
        race_names = schedule['EventName'].tolist()
        selected_race = st.selectbox("Select Grand Prix", race_names)

    except Exception as e:
        st.error(f"Could not load races for {selected_year}: {e}")
        return

    # Load sessions and analysis
    with st.spinner("⏳ Loading session data... This may take up to 55 seconds for new races. Please wait..."):
        quali_session = get_cached_session(selected_year, selected_race, 'Q')
        race_session = get_cached_session(selected_year, selected_race, 'R')
        summary = get_cached_summary(race_session)

    # Display race summary
    st.header("\U0001F4CB Race Summary")
    st.markdown(f"**\U0001F3C1 Winner**: {summary['Winner']}")
    st.markdown(f"**\U0001F949 Podium**: {', '.join(summary['Podium'])}")
    st.markdown(f"**\U0001F4A8 Fastest Lap**: {summary['Fastest Lap']}")
    st.markdown(f"**\U0001F4CA Total Laps**: {summary['Total Laps']}")
    st.markdown(f"**\U0001F321️ Weather**: {summary['Weather']}")

    # Visualize position changes
    st.subheader("\U0001F4C9 Driver Position Changes During Race")
    plot_position_changes(race_session)

    # Visualize Qualifying vs Race Performance
    results_df = get_cached_analysis(quali_session, race_session)
    plot_results(results_df)

    # Visualize Tyre Strategy
    st.subheader("\U0001F97E Tyre Strategy Timeline")
    plot_strategy_chart(race_session)

    # Plot lap times for selected driver
    st.subheader("\U0001F4C8 Driver Laptimes")
    selected_driver = st.selectbox("Select Driver", race_session.results['Abbreviation'].tolist())
    plot_driver_laptimes(race_session, selected_driver)

    # Plot telemetry comparisons
    st.subheader("📉 Telemetry Comparison")
    available_drivers = race_session.results['Abbreviation'].tolist()
    selected_telemetry_drivers = st.multiselect("Select Driver(s)", available_drivers)

    if selected_telemetry_drivers:
        selected_laps = st.multiselect("Select Lap(s)", sorted(race_session.laps['LapNumber'].unique()))
        driver_lap_pairs = [(d, l) for d in selected_telemetry_drivers for l in selected_laps]

        plot_telemetry_charts_multiselect(race_session, driver_lap_pairs)

if __name__ == "__main__":
    main()
