import streamlit as st
import plotly.graph_objects as go


@st.cache_data(show_spinner="Fetching telemetry data...")
def get_telemetry_for_driver_lap(_session, driver_code, lap_number):
    """
    Retrieve telemetry data for a specific driver and lap number.

    Parameters:
        _session: FastF1 session object.
        driver_code (str): Abbreviation of the driver's name (e.g. 'VER').
        lap_number (int): The lap to fetch telemetry for.

    Returns:
        pd.DataFrame or None: DataFrame containing telemetry data with distance, speed, throttle, etc.
    """

    #get the specific lap for a specific driver 
    lap = _session.laps.pick_driver(driver_code).loc[_session.laps["LapNumber"] == lap_number]
    if lap.empty:
        return None
    
    lap = lap.iloc[0]

    tel = lap.get_telemetry().add_distance()
    tel["LapTime"] = lap.LapTime
    tel["Driver"] = driver_code
    tel["Lap"] = lap_number
    
    return tel

def plot_telemetry_charts_multiselect(session, selected):
    """
    Plot multiple telemetry variables for selected driver and lap pairs.

    Parameters:
        session: FastF1 session object with telemetry.
        selected: List of (driver_code, lap_number) tuples to compare.

    Renders:
        One Plotly chart per telemetry variable (e.g., Speed, Throttle).
    """
    if not selected:
        st.info("Please select at least one driver-lap combination to display telemetry.")
        return

    # Telemetry metrics we will be plotting
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

        #loop through the different driver / lap combinations
        for driver_code, lap_number in selected:
            tel = get_telemetry_for_driver_lap(session, driver_code, lap_number)
            if tel is None:
                continue

            y_values = tel[col] if isinstance(col, str) else col(tel)
            fig.add_trace(go.Scatter(
                x=tel["Distance"],
                y=y_values,
                mode="lines",
                name=f"{driver_code} - Lap {lap_number}"
            ))

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
