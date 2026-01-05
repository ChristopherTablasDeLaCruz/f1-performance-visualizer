"""
Visualizes telemetry data comparisons between drivers.
"""

import streamlit as st
import plotly.graph_objects as go

def get_telemetry_for_driver_lap(session, driver_code, lap_number):
    """
    Retrieves telemetry data (speed, throttle, etc.) for a specific driver and lap.
    Returns None if the lap is invalid or data is missing.
    """
    try:
        driver_laps = session.laps.pick_driver(driver_code)
        if driver_laps.empty: 
            return None
        
        lap_data = driver_laps[driver_laps['LapNumber'] == lap_number]
        if lap_data.empty: 
            return None
        
        lap = lap_data.iloc[0]
        
        # .add_distance() is required for the x-axis on telemetry charts
        return lap.get_telemetry().add_distance()
        
    except Exception:
        return None

def plot_telemetry_charts_multiselect(session, selected):
    """
    Renders stacked Plotly charts for Speed, Throttle, Brake, RPM, and Gear.
    
    Args:
        session: The FastF1 session object.
        selected: List of tuples [(driver_code, lap_number), ...]
    """
    if not selected: 
        return

    channels = {
        "Speed": ("Speed", "km/h"),
        "Throttle": ("Throttle", "%"),
        "Brake": ("Brake", "%"),
        "RPM": ("RPM", "rpm"),
        "Gear": ("nGear", "#")
    }

    for name, (col, unit) in channels.items():
        fig = go.Figure()
        has_data = False

        for driver, lap_num in selected:
            tel = get_telemetry_for_driver_lap(session, driver, lap_num)
            
            if tel is not None and not tel.empty:
                has_data = True
                fig.add_trace(go.Scatter(
                    x=tel['Distance'], 
                    y=tel[col], 
                    name=f"{driver} L{lap_num}",
                    mode='lines'
                ))
        
        if has_data:
            fig.update_layout(
                title=f"{name}", 
                yaxis_title=unit,
                height=300,
                margin=dict(l=50, r=20, t=40, b=20),
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No {name} data found for selected drivers.")