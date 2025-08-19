"""
tire strategy visualization for F1 race analysis.

Creates intuitive visualizations that tell the strategic story of the race,
focusing on insights rather than raw data.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def plot_tire_strategy_timeline(race_session, selected_drivers=None):
    """
    Plot user-friendly tire strategy timeline that tells the strategic story.
    
    Focuses on strategic insights and clear visual storytelling rather than data dumping.
    """
    if not hasattr(race_session, 'laps') or race_session.laps.empty:
        st.warning("No strategy data available for this race.")
        return
    
    try:
        # Get and validate data
        laps_df = race_session.laps.copy()
        
        if 'Compound' not in laps_df.columns:
            st.warning("No tire compound data available for this race.")
            return
        
        laps_df = laps_df.dropna(subset=['Compound', 'Driver', 'LapNumber'])
        
        if laps_df.empty:
            st.warning("No valid strategy data found.")
            return
        
        # Filter to selected drivers
        if selected_drivers:
            laps_df = laps_df[laps_df['Driver'].isin(selected_drivers)]
            if laps_df.empty:
                st.warning("No data found for selected drivers.")
                return
        
        laps_df = laps_df.sort_values(['Driver', 'LapNumber'])
        
        st.subheader("🛞 Race Strategy Analysis")
        
        # Get race context
        total_laps = int(laps_df['LapNumber'].max())  # Convert to int
        compounds_used = sorted(laps_df['Compound'].unique())
        
        # Standard F1 colors
        compound_colors = {
            'SOFT': '#FF3333', 'MEDIUM': '#FFFF33', 'HARD': '#FFFFFF',
            'INTERMEDIATE': '#33FF33', 'WET': '#3333FF'
        }
        
        # Get driver finishing order
        try:
            results_df = race_session.results.copy()
            pos_col = 'Position' if 'Position' in results_df.columns else 'ClassifiedPosition'
            if pos_col in results_df.columns:
                driver_order = results_df.sort_values(pos_col)['Abbreviation'].tolist()
                driver_order = [d for d in driver_order if d in laps_df['Driver'].values]
            else:
                driver_order = sorted(laps_df['Driver'].unique())
        except:
            driver_order = sorted(laps_df['Driver'].unique())
        
        fig = go.Figure()
        
        # Track strategy insights
        strategy_insights = []
        pit_windows = []
        
        # Process each driver's strategy
        for i, driver in enumerate(driver_order):
            driver_laps = laps_df[laps_df['Driver'] == driver].copy()
            driver_laps = driver_laps.sort_values('LapNumber')
            
            # Identify stints
            driver_laps['compound_change'] = (driver_laps['Compound'] != driver_laps['Compound'].shift(1))
            driver_laps['stint_number'] = driver_laps['compound_change'].cumsum()
            
            pit_laps = []
            stints = []
            
            for stint_num, stint_data in driver_laps.groupby('stint_number'):
                compound = stint_data['Compound'].iloc[0]
                start_lap = stint_data['LapNumber'].min()
                end_lap = stint_data['LapNumber'].max()
                stint_length = len(stint_data)
                
                color = compound_colors.get(compound, '#888888')
                
                stint_laps = list(range(int(start_lap), int(end_lap) + 1))
                stint_y = [i] * len(stint_laps)
                
                # Main stint bar with full hover coverage
                fig.add_trace(go.Scatter(
                    x=stint_laps,
                    y=stint_y,
                    mode='lines',
                    line=dict(color=color, width=15),
                    showlegend=False,
                    hovertemplate=(
                        f"<b>{driver}</b><br>" +
                        f"{compound} tires<br>" +
                        f"Laps {start_lap}-{end_lap}<br>" +
                        f"Stint: {stint_length} laps<br>" +
                        "<extra></extra>"
                    ),
                    connectgaps=True
                ))
                
                # Add pit stop marker for stint changes (except first stint)
                if stint_num > 1:
                    pit_lap = int(start_lap)  # Convert to int
                    pit_laps.append(pit_lap)
                    
                    fig.add_trace(go.Scatter(
                        x=[pit_lap],
                        y=[i],
                        mode='markers',
                        marker=dict(
                            symbol='line-ns',
                            size=20,
                            color='orange',
                            line=dict(width=4, color='black')
                        ),
                        showlegend=False,
                        hovertemplate=(
                            f"<b>{driver}</b><br>" +
                            f"Pit stop: Lap {pit_lap}<br>" +
                            "<extra></extra>"
                        )
                    ))
                
                # Add clear compound labels
                if stint_length >= 3: 
                    fig.add_annotation(
                        x=(start_lap + end_lap) / 2,
                        y=i,
                        text=compound.replace('SOFT', 'S').replace('MEDIUM', 'M').replace('HARD', 'H'),
                        showarrow=False,
                        font=dict(color='black', size=11, family='Arial Black'),
                        bgcolor='rgba(255,255,255,0.9)',
                        borderwidth=2,
                        bordercolor='black'
                    )
                
                stints.append({
                    'compound': compound,
                    'start': int(start_lap),  
                    'end': int(end_lap),      
                    'length': stint_length
                })
            
            # Track pit windows
            for pit_lap in pit_laps:
                pit_windows.append(pit_lap)
            
            # Store strategy analysis
            strategy_insights.append({
                'driver': driver,
                'pit_stops': len(pit_laps),
                'stints': stints,
                'compounds_used': len(set(s['compound'] for s in stints))
            })
        
        # Configure chart
        fig.update_layout(
            title=f"Tire Strategy Timeline - {race_session.event['EventName']} {race_session.event.year}",
            xaxis_title="Lap Number",
            yaxis_title="",
            height=max(400, len(driver_order) * 35),
            xaxis=dict(
                range=[-1, total_laps + 2],
                gridcolor='rgba(128,128,128,0.2)',
                dtick=10,
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                tickmode='array',
                tickvals=list(range(len(driver_order))),
                ticktext=driver_order,
                tickfont=dict(size=13),
                gridcolor='rgba(128,128,128,0.1)'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=60, r=20, t=80, b=50),
            font=dict(size=12)
        )
        
        # Add compound legend directly on chart
        legend_y = len(driver_order) + 0.5
        legend_x_start = 2
        
        for i, compound in enumerate(compounds_used):
            color = compound_colors.get(compound, '#888888')
            x_pos = legend_x_start + (i * 8)
            
            # Legend marker
            fig.add_trace(go.Scatter(
                x=[x_pos, x_pos + 3],
                y=[legend_y, legend_y],
                mode='lines',
                line=dict(color=color, width=15),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Legend text
            fig.add_annotation(
                x=x_pos + 1.5,
                y=legend_y + 0.3,
                text=compound,
                showarrow=False,
                font=dict(color='white', size=10, family='Arial Black'),
                bgcolor='rgba(0,0,0,0.7)',
                bordercolor='white',
                borderwidth=1
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Strategic insights section 
        st.subheader("📊 Strategic Insights")
        
        # Analyze pit window patterns
        if pit_windows:
            pit_window_analysis = pd.Series(pit_windows).value_counts().sort_index()
            main_pit_window = pit_window_analysis.idxmax() if len(pit_window_analysis) > 0 else None
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Key strategic insights
                total_drivers = len(strategy_insights)
                one_stop_drivers = len([s for s in strategy_insights if s['pit_stops'] == 1])
                two_stop_drivers = len([s for s in strategy_insights if s['pit_stops'] == 2])
                
                st.write("**Race Strategy Pattern:**")
                if one_stop_drivers > two_stop_drivers:
                    st.write(f"• **One-stop dominant**: {one_stop_drivers}/{total_drivers} drivers used 1 pit stop")
                    st.write(f"• Conservative approach favored tire management")
                else:
                    st.write(f"• **Two-stop preferred**: {two_stop_drivers}/{total_drivers} drivers used 2 pit stops")
                    st.write(f"• Aggressive strategy focused on tire performance")
                
                if main_pit_window:
                    window_drivers = int(pit_window_analysis[main_pit_window])  # Convert to int
                    st.write(f"• **Main pit window**: Lap {int(main_pit_window)} ({window_drivers} drivers)")
                
                # Find strategic standouts
                most_aggressive = max(strategy_insights, key=lambda x: x['pit_stops'])
                most_conservative = min(strategy_insights, key=lambda x: x['pit_stops'])
                
                if most_aggressive['pit_stops'] != most_conservative['pit_stops']:
                    st.write(f"• **Most aggressive**: {most_aggressive['driver']} ({most_aggressive['pit_stops']} stops)")
                    st.write(f"• **Most conservative**: {most_conservative['driver']} ({most_conservative['pit_stops']} stops)")
            
            with col2:
                # Compound usage analysis
                st.write("**Tire Compound Usage:**")
                for compound in compounds_used:
                    drivers_using = len([s for s in strategy_insights 
                                       if any(stint['compound'] == compound for stint in s['stints'])])
                    st.write(f"• **{compound}**: {drivers_using}/{total_drivers} drivers")
        
        # detailed breakdown 
        with st.expander("🔍 Strategy Details", expanded=False):
            # Create simplified strategy summary
            strategy_summary = []
            for insight in strategy_insights:
                driver = insight['driver']
                stints = insight['stints']
                
                # readable strategy string
                strategy_parts = []
                for stint in stints:
                    compound_short = stint['compound'][0]  # S, M, H
                    strategy_parts.append(f"{compound_short}({stint['length']})")
                
                strategy_summary.append({
                    'Driver': driver,
                    'Strategy': " → ".join(strategy_parts),
                    'Pit Stops': insight['pit_stops'],
                    'Compounds': insight['compounds_used']
                })
            
            if strategy_summary:
                summary_df = pd.DataFrame(strategy_summary)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                st.caption("""
                **How to read**: S(12) = Soft tires for 12 laps, M(25) = Medium tires for 25 laps  
                **Orange markers** = Pit stops  
                **Strategy tip**: Fewer stops = tire management, more stops = pace priority
                """)
    
    except Exception as e:
        st.error(f"Error creating strategy analysis: {e}")
        st.info("This might be due to missing strategy data for this race.")

# Backward compatibility
def plot_strategy_chart(race_session, selected_drivers=None):
    """DEPRECATED: Use plot_tire_strategy_timeline() instead."""
    return plot_tire_strategy_timeline(race_session, selected_drivers)