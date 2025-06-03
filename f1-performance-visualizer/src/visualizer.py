import streamlit as st
import plotly.express as px

def plot_results(df):
    """
    Display two summary charts:
    1. Driver average race vs qualifying lap delta times.
    2. Driver position changes from grid to finish.

    """

    # Plot Position Change (Grid vs Finish)
    pos_sorted = df.sort_values("PositionDelta", ascending=False)
    colors = pos_sorted["PositionDelta"].apply(
        lambda x: "seagreen" if x > 0 else "lightcoral" if x < 0 else "lightgray"
    )

    hover_text = pos_sorted.apply(
        lambda row: f"{row['Driver']}: P{int(row['GridPosition'])} → P{int(row['FinishPosition'])} ({row['PositionDelta']:+.0f} pos)", axis=1
    )

    fig2 = px.bar(
        pos_sorted,
        x="PositionDelta",
        y="Driver",
        orientation="h",
        text=hover_text,
        color=colors,
        color_discrete_map="identity",
        labels={"PositionDelta": "Position Gained (+) or Lost (–)", "Driver": ""},
        title="Grid Start vs Final Position"
    )

    fig2.update_traces(
        textposition="none",
        hovertemplate="%{text}<extra></extra>"
    )

    fig2.update_layout(
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=60, b=40, l=80, r=20),
        xaxis=dict(zeroline=True, zerolinewidth=1, zerolinecolor='gray')
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Plot Delta Time
    df_sorted = df.sort_values("DeltaTime", ascending=False)
    avg_delta = df_sorted["DeltaTime"].mean()

    fig1 = px.bar(
        df_sorted,
        x="DeltaTime",
        y="Driver",
        orientation="h",
        text=df_sorted["DeltaTime"].apply(lambda x: f"{x:.2f}s"),
        labels={"DeltaTime": "Delta (Race Avg - Quali)", "Driver": ""},
        title="Driver Race vs Qualifying Performance",
        color_discrete_sequence=["steelblue"]
    )

    fig1.add_vline(x=avg_delta, line_dash="dash", line_color="red", annotation_text=f"Avg: {avg_delta:.2f}s")

    fig1.update_traces(
        textposition="outside",
        hovertemplate="Driver: %{y}<br>Delta: %{x:.2f}s<extra></extra>"
    )

    fig1.update_layout(
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=60, b=40, l=80, r=20),
    )

    st.plotly_chart(fig1, use_container_width=True)
