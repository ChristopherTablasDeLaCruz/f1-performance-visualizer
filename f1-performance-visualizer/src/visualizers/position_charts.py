"""
Position tracking throughout the race.

Shows how each driver moved up and down the field lap by lap.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

def plot_position_changes(session):
    """
    Show driver positions throughout the race.
    
    Creates a line chart where each driver's position is tracked
    lap by lap. 
    """
    
    if session.laps.empty or not {'Driver', 'LapNumber', 'Position'}.issubset(session.laps.columns):
        st.warning("Position data not available for this race.")
        return

    # Clean up the position data
    laps = session.laps[['Driver', 'LapNumber', 'Position']].dropna()
    laps['Position'] = pd.to_numeric(laps['Position'], errors='coerce')
    laps = laps.dropna(subset=['Position'])
    
    if laps.empty:
        st.warning("No valid position data found.")
        return

    st.caption("Track how each driver's position changed lap by lap")

    # Create the position chart
    fig = px.line(
        laps,
        x='LapNumber',
        y='Position',
        color='Driver',
        hover_data={'Position': True, 'LapNumber': True},
        line_group='Driver'
    )

    # Make it look clean
    fig.update_yaxes(
        autorange="reversed", 
        title="Position",
        gridcolor='rgba(128,128,128,0.2)'
    )
    fig.update_xaxes(
        title="Lap Number",
        gridcolor='rgba(128,128,128,0.2)'
    )
    fig.update_layout(
        height=500,
        hovermode='closest',
        legend_title="Driver",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # explanation
    st.write("Each line shows a driver's position throughout the race. Sharp drops usually indicate pit stops, while gradual changes show on-track position battles.")