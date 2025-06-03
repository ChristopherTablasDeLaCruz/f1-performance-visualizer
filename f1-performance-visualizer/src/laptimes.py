import streamlit as st
import plotly.express as px
import fastf1
import fastf1.plotting


def plot_driver_laptimes(session, driver_code="ALO"):
    """
    Display a scatter plot of lap times for selected driver using color-coded tyre compounds.

    Parameters:
        session: FastF1 session object (race or qualifying).
        driver_code (str): Abbreviation of the driver (e.g., "VER", "LEC").

    Renders:
        scatter plot with lap number vs lap time.
    """
    st.subheader(f"⏱️ Lap Times for {driver_code}")

    # Load quick laps
    laps = session.laps.pick_drivers(driver_code).pick_quicklaps().reset_index()

    if laps.empty:
        st.warning(f"No quick laps found for driver {driver_code}")
        return

    # Clean compound values
    laps["Compound"] = laps["Compound"].astype(str)
    laps["Compound"] = laps["Compound"].replace(["nan", "None", "<NA>", "NaN"], "Unknown")
    laps["Compound"] = laps["Compound"].fillna("Unknown")

    # Get color palette from FastF1
    palette = fastf1.plotting.get_compound_mapping(session=session)
    if "Unknown" not in palette:
        palette["Unknown"] = "#888888"

    # default gray for unexpected compounds
    unique_compounds = set(laps["Compound"].unique())
    for compound in unique_compounds:
        if compound not in palette:
            palette[compound] = "#cccccc"

    # Convert LapTime to total seconds
    laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()

    fig = px.scatter(
        laps,
        x="LapNumber",
        y="LapTimeSeconds",
        color="Compound",
        color_discrete_map=palette,
        hover_data={"LapNumber": True, "LapTimeSeconds": ':.2f', "Compound": True},
        title=f"{driver_code} Lap Times - {session.event['EventName']} {session.event.year}",
        labels={"LapNumber": "Lap", "LapTimeSeconds": "Lap Time (s)"}
    )

    fig.update_layout(
        yaxis=dict(autorange="reversed"), 
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=60, b=40, l=60, r=20),
    )

    st.plotly_chart(fig, use_container_width=True)

    if "Unknown" in laps["Compound"].values:
        st.caption("ℹ️ Some laps are labeled as 'Unknown' compound because tyre data was unavailable for those laps.")
