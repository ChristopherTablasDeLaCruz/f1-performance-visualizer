"""
Telemetry comparison charts for F1 analysis.

Shows detailed car data like speed, throttle, and brakes for specific laps.
Good for comparing how different drivers tackled the same track.
"""

import streamlit as st
import plotly.graph_objects as go


@st.cache_data(show_spinner="Fetching telemetry data...")
def get_telemetry_for_driver_lap(_session, driver_code, lap_number):
    """
    Get detailed car data for one driver's lap.
    
    Pulls telemetry like speed, throttle, brakes for a specific lap.
    Returns None if that lap doesn't exist.
    """

    # Find the specific lap for this driver 
    lap = _session.laps.pick_driver(driver_code).loc[_session.laps["LapNumber"] == lap_number]
    if lap.empty:
        return None
    
    lap = lap.iloc[0]

    # Get all the detailed telemetry data
    tel = lap.get_telemetry().add_distance()
    tel["LapTime"] = lap.LapTime
    tel["Driver"] = driver_code
    tel["Lap"] = lap_number
    
    return tel

def plot_telemetry_charts_multiselect(session, selected):
    """
    Compare telemetry between different driver-lap combinations.
    
    Shows speed, throttle, brakes etc. side by side so you can see
    how different drivers handled the same track sections.
    """
    if not selected:
        st.info("Please select at least one driver-lap combination to display telemetry.")
        return

    # Different telemetry channels we can show
    telemetry_vars = {
        "Speed (km/h)": "Speed",
        "Throttle (%)": "Throttle",
        "Brake (%)": "Brake",
        "RPM (x1000)": lambda tel: tel["RPM"] / 1000,
        "Gear": "nGear",
        "DRS": "DRS"
    }

    for label, col in telemetry_vars.items():
        fig = go.Figure()

        # Add each driver/lap combination to the chart
        for driver_code, lap_number in selected:
            tel = get_telemetry_for_driver_lap(session, driver_code, lap_number)
            if tel is None:
                continue

            # Get the data for this telemetry channel
            y_values = tel[col] if isinstance(col, str) else col(tel)
            fig.add_trace(go.Scatter(
                x=tel["Distance"],
                y=y_values,
                mode="lines",
                name=f"{driver_code} - Lap {lap_number}"
            ))

        # Style the chart
        fig.update_layout(
            title=f"{label} Comparison",
            xaxis_title="Distance (m)",
            yaxis_title=label,
            height=300,
            margin=dict(t=50, b=40, l=50, r=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, use_container_width=True)