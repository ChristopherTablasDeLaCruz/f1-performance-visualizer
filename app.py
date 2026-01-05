"""
F1 Race Analysis Dashboard.

"""

import datetime
import os
import shutil
import pandas as pd
import streamlit as st
import fastf1
from fastf1 import get_event_schedule

from src.core.performance_analyzer import analyze_performance
from src.visualizers.performance_charts import plot_performance_comparison
from src.visualizers.strategy_charts import plot_tire_strategy_timeline
from src.visualizers.lap_time_charts import plot_driver_pace_progression
from src.visualizers.position_charts import plot_position_changes
from src.visualizers.telemetry_charts import plot_telemetry_charts_multiselect

# -----------------------------------------------------------------------------
# Caching & Setup
# -----------------------------------------------------------------------------

CACHE_DIR = ".f1_cache"

def setup_cache():
    """Configures FastF1's native file-based caching."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    fastf1.Cache.enable_cache(CACHE_DIR)

@st.cache_data(show_spinner=False)
def get_schedule(year):
    """
    Retrieves the race schedule for a given year.
    Filters for completed races only (where the event date is in the past).
    """
    schedule = get_event_schedule(year, include_testing=False)
    if 'EventDate' in schedule.columns:
        schedule["EventDate"] = pd.to_datetime(schedule["EventDate"], utc=True)
        now = pd.Timestamp.now(tz="UTC")
        return schedule[schedule["EventDate"] < now]
    return pd.DataFrame()

@st.cache_resource(show_spinner=False)
def load_race_base(year, race_name):
    """
    Lightweight Loader: Retrieves only the Race Results (Winner, Podium).
    FastF1 params are set to False to minimize download/parsing time.
    """
    session = fastf1.get_session(year, race_name, 'R')
    session.load(laps=False, telemetry=False, weather=True, messages=False)
    return session

def ensure_laps_loaded(session):
    """
    Lazy Loader: Ensures lap timing data is present in the session.
    Checks for the '.laps' property safely to avoid DataNotLoadedError.
    """
    try:
        _ = session.laps
    except Exception:
        session.load(laps=True, telemetry=False, weather=True, messages=False)
    return session

def ensure_telemetry_loaded(session):
    """
    On-Demand Loader: Ensures high-frequency telemetry (speed, throttle) is loaded.
    This is the heaviest operation, so it's guarded.
    """
    try:
        if session.car_data is None or session.car_data.empty:
            raise ValueError("Telemetry missing")
    except Exception:
        session.load(telemetry=True, weather=True)
    return session

@st.cache_resource(show_spinner="Loading Qualifying Data...")
def load_quali_session(year, race_name):
    """Retrieves Qualifying session data for performance comparison."""
    session = fastf1.get_session(year, race_name, 'Q')
    session.load(laps=True, telemetry=False, weather=False, messages=False)
    return session

# -----------------------------------------------------------------------------
# Main App Structure
# -----------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="F1 Race Dashboard", layout="wide", page_icon="🏎️")
    setup_cache()
    
    # --- Sidebar Configuration ---
    with st.sidebar:
        st.header("🏁 Race Selection")
        current_year = datetime.datetime.now().year
        season_years = list(range(2018, current_year + 1))[::-1]
        
        # Initialize session state for year selection
        if 'selected_year' not in st.session_state:
            latest_schedule = get_schedule(current_year)
            if latest_schedule.empty:
                st.session_state.selected_year = 2025
            else:
                st.session_state.selected_year = current_year
            
        try:
            default_year_index = season_years.index(st.session_state.selected_year)
        except ValueError:
            default_year_index = 0

        selected_year = st.selectbox(
            "Select Season", 
            season_years, 
            index=default_year_index, 
            key='year_select'
        )
        
        # Invalidate telemetry if season changes
        if selected_year != st.session_state.selected_year:
            st.session_state.telemetry_loaded = False
            st.session_state.selected_year = selected_year

        try:
            schedule = get_schedule(selected_year)
            if schedule.empty:
                st.info("No completed races found.")
                return
            
            schedule = schedule.sort_values(by="EventDate")
            race_names = schedule['EventName'].tolist()
            
            # Default to the most recent race
            default_ix = len(race_names) - 1
            selected_race = st.selectbox("Select Grand Prix", race_names, index=default_ix, key='race_select')
            
            # Invalidate telemetry if race changes
            if 'last_race' not in st.session_state or st.session_state.last_race != selected_race:
                st.session_state.telemetry_loaded = False
                st.session_state.last_race = selected_race
            
        except Exception as e:
            st.error(f"Error loading schedule: {e}")
            return
            
        st.divider()
        st.caption("Data provided by FastF1")

    # --- Main Dashboard ---
    st.title("🏎️ F1 Race Analysis Dashboard")
    st.header(f"{selected_race} {selected_year}")
    
    # Phase 1: Instant Load (Results)
    try:
        race_session = load_race_base(selected_year, selected_race)
        
        st.subheader("📋 Race Summary")
        col1, col2, col3 = st.columns(3)
        results = race_session.results
        
        if not results.empty:
            pos_col = 'Position' if 'Position' in results.columns else 'ClassifiedPosition'
            try:
                winner = results[results[pos_col] == 1.0].iloc[0]
                st.markdown(f"**🏆 Winner**: {winner['Abbreviation']}")
            except Exception: 
                pass
            
            try:
                podium = results[results[pos_col] <= 3].sort_values(pos_col)['Abbreviation'].tolist()
                st.markdown(f"**🥇🥈🥉 Podium**: {', '.join(podium)}")
            except Exception: 
                pass

        if hasattr(race_session, 'weather_data'):
            w = race_session.weather_data
            if w is not None and not w.empty:
                 st.markdown(f"**🌡️ Temp**: {w['AirTemp'].mean():.1f}°C")
            
    except Exception as e:
        st.error(f"Failed to load race results: {e}")
        return

    st.divider()

    # Phase 2: Background Load (Laps)
    with st.spinner("Processing lap data..."):
        race_session = ensure_laps_loaded(race_session)
    
    # Phase 3: Visualization Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Position", "⚡ Performance", "🛞 Strategy", "⏱️ Pace", "📈 Telemetry"
    ])
    
    drivers = list(race_session.results['Abbreviation'])
    
    with tab1:
        plot_position_changes(race_session)
    
    with tab2:
        try:
            quali = load_quali_session(selected_year, selected_race)
            perf_df = analyze_performance(quali, race_session)
            plot_performance_comparison(perf_df)
        except Exception:
            st.info("Qualifying data unavailable for comparison.")
    
    with tab3:
        sel = st.multiselect("Drivers", drivers, default=drivers[:5], key="strat")
        if sel: 
            plot_tire_strategy_timeline(race_session, sel)
            
    with tab4:
        drv = st.selectbox("Driver", drivers, key="pace")
        plot_driver_pace_progression(race_session, drv)

    with tab5:
        st.subheader("Telemetry Comparison")
        
        # Phase 4: On-Demand Load (Telemetry)
        if st.session_state.get('telemetry_loaded', False):
            with st.spinner("Loading telemetry..."):
                ensure_telemetry_loaded(race_session)
            
            c1, c2 = st.columns(2)
            with c1:
                cmp_drivers = st.multiselect("Compare", drivers, default=drivers[:2], max_selections=3)
            with c2:
                if cmp_drivers:
                    d_laps = race_session.laps.pick_driver(cmp_drivers[0])
                    if not d_laps.empty:
                        min_l, max_l = int(d_laps.LapNumber.min()), int(d_laps.LapNumber.max())
                        def_l = int((min_l + max_l)/2)
                        sel_lap = st.number_input("Lap", min_l, max_l, def_l)
                    else:
                        sel_lap = 1
                else:
                    sel_lap = 1
            
            if cmp_drivers:
                combos = [(d, sel_lap) for d in cmp_drivers]
                plot_telemetry_charts_multiselect(race_session, combos)
                
        else:
            
            if st.button("Load Telemetry Data", type="primary"):
                st.session_state.telemetry_loaded = True
                st.rerun()

if __name__ == "__main__":
    main()