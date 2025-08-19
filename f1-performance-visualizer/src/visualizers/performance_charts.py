"""
Performance comparison charts and visualizations.

Contains plotting functions for comparing driver performance between
qualifying and race sessions, showing delta times and position changes.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def plot_performance_comparison(performance_df):
    """
    Plot performance comparison with correct interpretation.
    
    Shows who maintained their qualifying pace best vs who struggled most in race conditions.
    Positive delta (slower in race) is normal - we're looking for who had the smallest degradation.
    """
    if performance_df.empty:
        st.warning("No performance data available for comparison.")
        return
    
    # Validate required columns exist in dataframe
    required_cols = ['DeltaTime', 'Driver', 'PositionDelta', 'QualTime', 'RaceAvgTime', 'GridPosition', 'FinishPosition']
    missing_cols = [col for col in required_cols if col not in performance_df.columns]
    if missing_cols:
        st.error(f"Missing required columns: {missing_cols}")
        return
    
    df = performance_df.copy()
    # Remove rows with missing critical data (DeltaTime is our primary metric)
    df = df.dropna(subset=['DeltaTime', 'Driver'])
    
    if df.empty:
        st.warning("No valid performance data after removing incomplete records.")
        return
    
    # Categorize performance based on pace degradation thresholds
    # These thresholds are based on typical F1 performance patterns
    df['Performance_Category'] = df['DeltaTime'].apply(lambda x: 
        'Excellent' if x < 3 else          # Very close to quali pace
        'Good' if x < 5 else               # Reasonable degradation
        'Average' if x < 7 else            # Typical F1 degradation
        'Poor'                             # Significant struggle
    )
    
    # Sort by performance (best pace maintenance first)
    df = df.sort_values('DeltaTime')
    
    st.subheader("🏁 Race Pace vs Qualifying Performance")
    st.caption("💡 **Key Insight**: Almost everyone is slower in races than qualifying. We're measuring who maintained their pace best.")
    
    # Create main performance chart
    fig = go.Figure()
    
    # Color scheme: green = good, red = poor performance
    colors = {
        'Excellent': '#00AA00',     # Dark green
        'Good': '#66CC66',          # Light green
        'Average': '#FFAA00',       # Orange
        'Poor': '#DD0000'           # Red
    }
    
    # Add bars for each performance category
    for category in ['Excellent', 'Good', 'Average', 'Poor']:
        category_data = df[df['Performance_Category'] == category]
        if not category_data.empty:
            fig.add_trace(go.Bar(
                name=f"{category} Pace Maintenance",
                x=category_data['Driver'],
                y=category_data['DeltaTime'],
                marker_color=colors[category],
                text=category_data['DeltaTime'].apply(lambda x: f"+{x:.1f}s"),
                textposition='outside',
                textfont=dict(color='white', size=12),  
                hovertemplate=(
                    "<b>%{x}</b><br>" +
                    "Race pace compared to qualifying: %{text}<br>" +
                    "Category: %{fullData.name}<br>" +
                    "<extra></extra>"
                )
            ))
    
    fig.update_layout(
        title="Who Maintained Their Qualifying Pace Best?<br><sub>Lower bars = better pace maintenance</sub>",
        xaxis_title="Driver",
        yaxis_title="Seconds Slower Than Qualifying",
        height=500,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_tickangle=-45  # Rotate driver names for readability
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Two-column layout for position changes and highlights
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("📊 Position Changes")
        
        # Sort by position change (biggest gainers first)
        df_pos = df.sort_values('PositionDelta', ascending=False)
        
        fig_pos = go.Figure()
        
        # Color code position changes
        position_colors = []
        for delta in df_pos['PositionDelta']:
            if delta >= 3:
                position_colors.append('#00AA00')      # Big gain
            elif delta > 0:
                position_colors.append('#66CC66')      # Small gain
            elif delta == 0:
                position_colors.append('#CCCCCC')      # No change
            elif delta >= -3:
                position_colors.append('#FFAA00')      # Small loss
            else:
                position_colors.append('#DD0000')      # Big loss
        
        fig_pos.add_trace(go.Bar(
            x=df_pos['Driver'],
            y=df_pos['PositionDelta'],
            marker_color=position_colors,
            text=df_pos['PositionDelta'].apply(lambda x: f"{x:+.0f}" if x != 0 else "0"),
            textposition='outside',
            textfont=dict(color='white', size=12),
            hovertemplate=(
                "<b>%{x}</b><br>" +
                "Started: P%{customdata[0]}<br>" +
                "Finished: P%{customdata[1]}<br>" +
                "Change: %{text}<br>" +
                "<extra></extra>"
            ),
            customdata=df_pos[['GridPosition', 'FinishPosition']].values,
            showlegend=False
        ))
        
        fig_pos.add_hline(y=0, line_dash="dash", line_color="black", line_width=2)
        
        fig_pos.update_layout(
            title="Grid vs Finish Position Changes",
            xaxis_title="Driver",
            yaxis_title="Positions Gained/Lost",
            height=700,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig_pos, use_container_width=True)
    
    with col2:
        st.subheader("🏆 Performance Highlights")
        
        # Get key performance stats (data is already sorted by DeltaTime)
        best_pace = df.iloc[0]  # Best pace maintenance
        worst_pace = df.iloc[-1]  # Worst pace maintenance
        biggest_gainer = df.loc[df['PositionDelta'].idxmax()]
        biggest_loser = df.loc[df['PositionDelta'].idxmin()]
        
        # Display key insights 
        st.success(f"**🎯 Best Pace Maintenance**\n{best_pace['Driver']}\nRace pace only {best_pace['DeltaTime']:.1f}s slower than qualifying")
        
        if biggest_gainer['PositionDelta'] > 0:
            st.success(f"**📈 Most Positions Gained**\n{biggest_gainer['Driver']}\n+{int(biggest_gainer['PositionDelta'])} positions")
        
        st.error(f"**⚠️ Biggest Pace Drop-Off**\n{worst_pace['Driver']}\nRace pace {worst_pace['DeltaTime']:.1f}s slower than qualifying")
        
        if biggest_loser['PositionDelta'] < 0:
            st.error(f"**📉 Most Positions Lost**\n{biggest_loser['Driver']}\n{int(biggest_loser['PositionDelta'])} positions")
    
    # Detailed data table in expandable section
    with st.expander("📋 Detailed Performance Data", expanded=False):
        display_df = df.copy()
        
        # Format time values, handling NaN/invalid data
        def format_time(seconds):
            if pd.isna(seconds) or seconds <= 0:
                return "N/A"
            return f"{int(seconds//60)}:{seconds%60:06.3f}"
        
        # Convert timedelta to seconds and format as MM:SS.sss
        display_df['Best Quali Time'] = display_df['QualTime'].dt.total_seconds().apply(format_time)
        display_df['Avg Race Time'] = display_df['RaceAvgTime'].dt.total_seconds().apply(format_time)
        display_df['Pace Difference'] = display_df['DeltaTime'].apply(
            lambda x: f"+{x:.2f}s" if pd.notna(x) else "N/A"
        )
        
        # Format position changes with error handling
        display_df['Grid → Finish'] = display_df.apply(
            lambda row: (f"P{int(row['GridPosition'])} → P{int(row['FinishPosition'])}" 
                        if pd.notna(row['GridPosition']) and pd.notna(row['FinishPosition']) 
                        else "N/A"), axis=1
        )
        display_df['Position Change'] = display_df['PositionDelta'].apply(
            lambda x: (f"+{int(x)}" if x > 0 else f"{int(x)}" if x < 0 else "0") 
                     if pd.notna(x) else "N/A"
        )
        
        # Add ranking column (1 = best pace maintenance)
        display_df['Pace Rank'] = range(1, len(display_df) + 1)
        
        # Prepare final table
        table_df = display_df[[
            'Pace Rank', 'Driver', 'Best Quali Time', 'Avg Race Time', 
            'Pace Difference', 'Performance_Category', 'Grid → Finish', 'Position Change'
        ]].rename(columns={
            'Performance_Category': 'Pace Maintenance',
            'Pace Rank': 'Rank'
        })
        
        # Display formatted table
        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", format="%d"),
                "Pace Difference": st.column_config.TextColumn("Pace Difference"),
                "Position Change": st.column_config.TextColumn("Pos Change"),
            }
        )
    
    with st.expander("📚 Understanding the Data", expanded=False):
        st.write("""
        **Why is everyone slower in races than qualifying?**
        
        🏎️ **Qualifying conditions:**
        - Fresh tires with maximum grip
        - Low fuel load (lighter car)
        - Clear track with no traffic
        - Single flying lap (no tire degradation)
        
        🏁 **Race conditions:**
        - Tires degrade over many laps
        - Heavy fuel load at start
        - Traffic and dirty air from other cars
        - Different tire compounds and strategies
        
        **What we're measuring:** Who adapted best to race conditions and maintained their pace closest to their qualifying performance.
        """)
        
        avg_degradation = df['DeltaTime'].mean()
        best_performer = df.iloc[0]
        worst_performer = df.iloc[-1]
        
        st.write(f"**Race Summary:**")
        st.write(f"• Average pace degradation: +{avg_degradation:.1f} seconds")
        st.write(f"• Best pace maintenance: {best_performer['Driver']} (+{best_performer['DeltaTime']:.1f}s)")
        st.write(f"• Worst pace maintenance: {worst_performer['Driver']} (+{worst_performer['DeltaTime']:.1f}s)")

def plot_results(performance_df):
    """DEPRECATED: Use plot_performance_comparison() instead.""" 
    return plot_performance_comparison(performance_df)