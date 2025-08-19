"""
F1 Race Analysis Dashboard

Interactive Streamlit app for analyzing Formula 1 race data.
Shows race results, driver performance, strategy, and telemetry.
"""

import datetime
import streamlit as st
from fastf1 import get_event_schedule
import pandas as pd
import os
import shutil
from src.core.cache_manager import F1DataCache
from src.core.session_adapters import CachedF1Session
from src.core.performance_analyzer import analyze_performance
from src.visualizers.performance_charts import plot_performance_comparison
from src.visualizers.strategy_charts import plot_tire_strategy_timeline
from src.utils.race_summary import get_race_summary
from src.visualizers.lap_time_charts import plot_driver_pace_progression
from src.visualizers.position_charts import plot_position_changes
from src.visualizers.telemetry_charts import plot_telemetry_charts_multiselect

@st.cache_data(show_spinner=False)
def get_cached_schedule(year):
    """Get all completed races for a season."""
    schedule = get_event_schedule(year, include_testing=False)
    schedule["Session5Date"] = pd.to_datetime(schedule["Session5Date"], utc=True)
    now = pd.Timestamp.now(tz="UTC")
    completed_races = schedule[schedule["Session5Date"] < now]
    return completed_races

@st.cache_data(show_spinner="Analyzing performance...")
def get_cached_performance_analysis(quali_data, race_data):
    """Compare qualifying vs race performance using cached data."""
    return analyze_performance(quali_data, race_data)

def main():
    """
    F1 Race Analysis Dashboard
    
    Main Streamlit app that lets users explore F1 race data with:
    - Race summaries and results
    - Driver performance comparisons  
    - Strategy and tire analysis
    - Lap time progressions
    - Telemetry comparisons
    
    Uses smart caching so data loads fast after the first time.
    """
    st.set_page_config(
        page_title="F1 Race Dashboard", 
        layout="wide",
        page_icon="🏎️"
    )
    
    # Set up the caching system
    cache_manager = F1DataCache()
    
    # Sidebar for race selection and settings
    with st.sidebar:
        st.header("🏁 Race Selection")
        
        # Pick the season
        current_year = datetime.datetime.now().year
        season_years = list(range(2018, current_year + 1))[::-1]
        default_year_index = season_years.index(2024)
        selected_year = st.selectbox("Select Season", season_years, index=default_year_index)

        # Pick the race
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
        
        # Cache management
        st.divider()
        st.subheader("⚙️ Cache Settings")
        
        # Show cache info
        cache_dir = ".f1_cache"
        if os.path.exists(cache_dir):
            cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.parquet')]
            cache_count = len(cache_files)
            
            if cache_files:
                cache_size = sum(
                    os.path.getsize(os.path.join(cache_dir, f))
                    for f in cache_files
                ) / (1024 * 1024)  # Convert to MB
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Cached Races", cache_count)
                with col2:
                    st.metric("Cache Size", f"{cache_size:.1f} MB")
            else:
                st.info("Cache is empty")
        else:
            st.info("No cache directory")
        
        # Clear cache button
        if st.button("Clear All Cache", type="secondary", use_container_width=True):
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir, ignore_errors=True)
            st.cache_data.clear()
            st.success("✅ Cache cleared!")
            st.rerun()
        
        # Performance tips
        st.divider()
        st.caption("💡 First load: ~20-30s")
        st.caption("⚡ Cached loads: <2s")

    # Main dashboard area
    st.title("🏎️ F1 Race Analysis Dashboard")
    st.header(f"{selected_race} {selected_year}")
    
    # Load the race data
    try:
        # Check if we already have this data cached
        race_cache_path = cache_manager.get_cache_path(selected_year, selected_race, 'race')
        quali_cache_path = cache_manager.get_cache_path(selected_year, selected_race, 'quali')
        
        is_cached = cache_manager.is_cache_valid(race_cache_path) and cache_manager.is_cache_valid(quali_cache_path)
        
        if is_cached:
            load_message = "Loading from cache..."
        else:
            load_message = "First time loading this race (this will take 20-30 seconds)..."
        
        with st.spinner(load_message):
            race_data = cache_manager.load_race_data(selected_year, selected_race)
            quali_data = cache_manager.load_quali_data(selected_year, selected_race)
        
        if not is_cached:
            st.success("✅ Data loaded and cached! Future loads will be instant.")
        
    except Exception as e:
        st.error(f"Failed to load race data: {e}")
        st.info("Try selecting a different race or clearing the cache.")
        return
    
    # Show race summary
    st.subheader("📋 Race Summary")

    # Build summary from cached data
    col1, col2, col3 = st.columns(3)

    with col1:
        results_df = pd.DataFrame(race_data['results'])
        
        # Handle different column names for position
        position_col = 'Position'
        if 'Position' not in results_df.columns:
            position_col = 'ClassifiedPosition' if 'ClassifiedPosition' in results_df.columns else 'GridPosition'
        
        # Show the winner
        try:
            winner = results_df[results_df[position_col] == 1.0].iloc[0]
            st.markdown(f"**🏆 Winner**")
            st.markdown(f"{winner['Abbreviation']} ({winner['TeamName']})")
        except:
            st.markdown(f"**🏆 Winner**")
            st.markdown("Data not available")

    with col2:
        try:
            podium = results_df[results_df[position_col] <= 3].sort_values(position_col)
            podium_names = ', '.join(podium['Abbreviation'].tolist())
            st.markdown(f"**🥇🥈🥉 Podium**")
            st.markdown(podium_names)
        except:
            st.markdown(f"**🥇🥈🥉 Podium**")
            st.markdown("Data not available")

    with col3:
        st.markdown(f"**📊 Total Laps**")
        st.markdown(f"{race_data['event_info'].get('total_laps', 'N/A')}")
        
        # Show fastest lap
        laps_df = pd.DataFrame(race_data['laps'])
        if not laps_df.empty and 'LapTime' in laps_df.columns:
            laps_df['LapTime'] = pd.to_timedelta(laps_df['LapTime'])
            fastest_lap_idx = laps_df['LapTime'].idxmin()
            if pd.notna(fastest_lap_idx):
                fastest_lap = laps_df.loc[fastest_lap_idx]
                lap_time = fastest_lap['LapTime']
                formatted_time = f"{int(lap_time.total_seconds() // 60)}:{lap_time.total_seconds() % 60:.3f}"
                st.markdown(f"**🚀 Fastest Lap**: {fastest_lap['Driver']} ({formatted_time}) on Lap {int(fastest_lap['LapNumber'])}")
        
    # Weather info if available
    weather_data = race_data.get('weather')
    if weather_data is not None and len(weather_data) > 0:
        weather_df = pd.DataFrame(weather_data)
        if not weather_df.empty and 'AirTemp' in weather_df.columns and 'TrackTemp' in weather_df.columns:
            try:
                avg_air_temp = int(weather_df["AirTemp"].mean())
                avg_track_temp = int(weather_df["TrackTemp"].mean())
                st.markdown(f"**🌡️ Conditions**: Air {avg_air_temp}°C | Track {avg_track_temp}°C")
            except Exception:
                pass
    
    st.divider()
    
    # Analysis tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Position Changes", 
        "⚡ Performance Analysis", 
        "🛞 Strategy", 
        "⏱️ Lap Times",
        "📈 Telemetry"
    ])
    
    with tab1:
        st.subheader("Position Changes During Race")
        # Create session object from cached data
        cached_session = CachedF1Session(
            race_data,
            race_data['event_info']['name'],
            selected_year,
            race_data['event_info'].get('date')
        )
        plot_position_changes(cached_session)
    
    with tab2:
        st.subheader("Driver Performance Analysis")
        # Compare qualifying vs race performance
        results_df = get_cached_performance_analysis(quali_data, race_data)
        plot_performance_comparison(results_df)
    
    with tab3:
        st.subheader("Tyre Strategy Timeline")
        
        # Create session object from cached data
        cached_session = CachedF1Session(
            race_data,
            race_data['event_info']['name'],
            selected_year,
            race_data['event_info'].get('date')
        )
    
        # Let user pick which drivers to show
        drivers = cached_session.results['Abbreviation'].tolist()
        selected_strategy_drivers = st.multiselect(
            "Select drivers to display", 
            drivers, 
            default=drivers[:10]  # Show top 10 by default
        )
        
        if selected_strategy_drivers:
            plot_tire_strategy_timeline(cached_session, selected_strategy_drivers)
    
    with tab4:
        st.subheader("Driver Lap Times")
        results_df = pd.DataFrame(race_data['results'])
        selected_driver = st.selectbox("Select Driver", results_df['Abbreviation'].tolist())
        
        # Create session object from cached data
        cached_session = CachedF1Session(
            race_data,
            race_data['event_info']['name'],
            selected_year,
            race_data['event_info'].get('date')
        )
        plot_driver_pace_progression(cached_session, selected_driver)
    
    with tab5:
        st.subheader("Telemetry Comparison")
        
        # Telemetry needs full session data, not cached
        if 'telemetry_loaded' not in st.session_state:
            st.session_state.telemetry_loaded = False
            st.session_state.telemetry_session = None
        
        if not st.session_state.telemetry_loaded:
            st.info("⚠️ Telemetry data requires full session loading with all data.")
            st.caption("This will take 30-60 seconds as it needs to download detailed telemetry data.")
            
            if st.button("Load Full Telemetry Data", type="primary"):
                with st.spinner("Loading full telemetry data... This may take 30-60 seconds"):
                    try:
                        # Load complete session with telemetry
                        import fastf1
                        session = fastf1.get_session(selected_year, selected_race, 'R')
                        session.load(laps=True, messages=True)
                        
                        # Save in session state
                        st.session_state.telemetry_session = session
                        st.session_state.telemetry_loaded = True
                        
                        st.success("✅ Telemetry data loaded successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Failed to load telemetry data: {e}")
                        st.info("This could be due to network issues or the race not having telemetry data available.")
        
        else:
            st.success("✅ Telemetry data is loaded and ready!")
            
            # Get available drivers
            results_df = pd.DataFrame(race_data['results'])
            available_drivers = results_df['Abbreviation'].tolist()
            
            # Driver and lap selection
            col1, col2 = st.columns(2)
            
            with col1:
                selected_drivers = st.multiselect(
                    "Select drivers to compare",
                    available_drivers,
                    default=available_drivers[:2] if len(available_drivers) >= 2 else available_drivers[:1],
                    max_selections=4
                )
            
            with col2:
                if selected_drivers:
                    # Get lap range for the first selected driver
                    driver_laps = st.session_state.telemetry_session.laps.pick_drivers(selected_drivers[0])
                    if not driver_laps.empty:
                        min_lap = int(driver_laps['LapNumber'].min())
                        max_lap = int(driver_laps['LapNumber'].max())
                        
                        selected_lap = st.number_input(
                            "Select lap number",
                            min_value=min_lap,
                            max_value=max_lap,
                            value=min_lap,
                            step=1
                        )
                    else:
                        selected_lap = 1
                        st.warning("No lap data found for selected driver")
                else:
                    selected_lap = 1
            
            # Show telemetry charts
            if selected_drivers:
                try:
                    # Create driver-lap combinations
                    driver_lap_combinations = [(driver, selected_lap) for driver in selected_drivers]
                    
                    # Plot the telemetry
                    plot_telemetry_charts_multiselect(st.session_state.telemetry_session, driver_lap_combinations)
                    
                except Exception as e:
                    st.error(f"Error plotting telemetry: {e}")
                    st.info("Try selecting different drivers or lap numbers.")
            
            # Option to clear telemetry data
            if st.button("Clear Telemetry Data", type="secondary"):
                st.session_state.telemetry_loaded = False
                st.session_state.telemetry_session = None
                st.rerun()

if __name__ == "__main__":
    main()