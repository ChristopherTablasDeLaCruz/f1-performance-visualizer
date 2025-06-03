import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def plot_strategy_chart(race_session, selected_drivers=None):
    """
    Plot each driver's tire stint strategy across the race.

    Parameters:
        race_session: A FastF1 race session object.
        selected_drivers (list, optional): If provided, only these drivers will be shown.

    Output:
        chart with stints color-coded by compound, with lap ranges and tooltips.
    """

    # Extract stint data
    stints = race_session.laps[["Driver", "Stint", "Compound", "LapNumber"]]
    stints = (
        stints.groupby(["Driver", "Stint", "Compound"])["LapNumber"]
        .agg(["min", "max", "count"])
        .reset_index()
    )

    # Determine driver order
    drivers = race_session.results["Abbreviation"].tolist()
    if selected_drivers:
        drivers = [d for d in drivers if d in selected_drivers]

    # Compound color map
    compound_colors = {
        'SOFT': '#ff3333',
        'MEDIUM': '#ffff66',
        'HARD': '#e6e6e6',
        'INTERMEDIATE': '#39B54A',
        'WET': '#1995D0',
        'UNKNOWN': '#cccccc'
    }

    # Build data
    data = []
    for driver in drivers:
        driver_stints = stints[stints["Driver"] == driver]
        for _, stint in driver_stints.iterrows():
            data.append(dict(
                Driver=driver,
                Compound=stint["Compound"].title(),
                Start=stint["min"],
                End=stint["max"],
                Duration=stint["count"],
                Color=compound_colors.get(stint["Compound"].upper(), "#888888")
            ))

    df = pd.DataFrame(data)
    df["Driver"] = pd.Categorical(df["Driver"], categories=drivers[::-1], ordered=True)

    fig = go.Figure()

    for _, row in df.iterrows():
        fig.add_trace(go.Bar(
            x=[row["Duration"]],
            y=[row["Driver"]],
            base=row["Start"],
            orientation='h',
            marker=dict(color=row["Color"], line=dict(color="black", width=1)),
            name=row["Compound"],
            hovertemplate=f"{row['Driver']}<br>{row['Compound']}<br>Lap {row['Start']} → {row['End']}<extra></extra>",
            showlegend=False
        ))

    # Custom legend
    seen = set()
    for compound, color in compound_colors.items():
        if compound.title() in df["Compound"].unique() and compound not in seen:
            fig.add_trace(go.Bar(
                x=[None], y=[None],
                marker=dict(color=color),
                name=compound.title(),
                showlegend=True
            ))
            seen.add(compound)

    fig.update_layout(
        title=f"{race_session.event['EventName']} {race_session.event.year} - Tyre Strategy",
        xaxis_title="Lap",
        yaxis_title="Driver",
        height=500 + 20 * len(drivers),
        barmode="stack",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=60, b=40, l=80, r=20)
    )

    st.plotly_chart(fig, use_container_width=True)
