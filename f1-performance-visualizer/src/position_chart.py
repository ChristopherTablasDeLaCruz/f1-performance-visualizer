import streamlit as st
import pandas as pd
import plotly.express as px

def plot_position_changes(session):
    """
    Plot driver position changes over the course of the race.

    Parameters:
        session: FastF1 race session object (must have loaded laps).
    """

    if session.laps.empty or not {'Driver', 'LapNumber', 'Position'}.issubset(session.laps.columns):
        st.warning("Lap data unavailable for this session.")
        return

    # Get driver, lap number, position and remove rows with missing data
    laps = session.laps[['Driver', 'LapNumber', 'Position']].dropna()

    laps['Position'] = pd.to_numeric(laps['Position'])

    # Create line plot that shows position per lap for each driver.
    fig = px.line(
        laps,
        x='LapNumber',
        y='Position',
        color='Driver',
        hover_data={'Position': True, 'LapNumber': True},
        line_group='Driver',
        render_mode='svg'
    )

    fig.update_yaxes(autorange="reversed", title="Position")
    fig.update_xaxes(title="Lap")
    fig.update_layout(
        height=600,
        hovermode='closest',
        legend_title="Driver",
        template='plotly_dark'
    )

    st.plotly_chart(fig, use_container_width=True)
