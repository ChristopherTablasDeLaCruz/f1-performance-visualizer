"""
Lap time analysis for individual drivers.

Shows how a driver's pace changed throughout the race
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def plot_driver_pace_progression(race_session, selected_driver):
    """
    Show how a driver's lap times changed during the race.
    
    Creates a chart with tire colors and pit stops marked, plus a summary
    of what happened during the race.
    """
    if not hasattr(race_session, 'laps') or race_session.laps.empty:
        st.warning("No lap data available for this driver.")
        return
    
    if not selected_driver:
        st.warning("Please select a driver to analyze.")
        return
    
    try:
        # Get driver's lap data
        all_laps = race_session.laps.copy()
        driver_laps = all_laps[all_laps['Driver'] == selected_driver].copy()
        
        if driver_laps.empty:
            st.warning(f"No lap data found for {selected_driver}.")
            return
        
        # Clean up the data
        driver_laps = driver_laps.dropna(subset=['LapTime', 'LapNumber'])
        
        if driver_laps.empty:
            st.warning(f"No valid lap times found for {selected_driver}.")
            return
        
        # Convert lap times to seconds
        driver_laps['LapTimeSeconds'] = driver_laps['LapTime'].dt.total_seconds()
        driver_laps = driver_laps.sort_values('LapNumber')
        
        # Use stint-based pit stop detection 
        # Each stint = time between pit stops, so stint changes = pit stops
        if 'Stint' in driver_laps.columns and driver_laps['Stint'].notna().any():
            dl = driver_laps.copy()
            
            # Find where stint number changes (indicates pit stop)
            dl['stint_changed'] = (dl['Stint'] != dl['Stint'].shift(1)) & (dl['Stint'].notna())
            
            # First lap never counts as a pit stop
            dl.loc[dl.index[0], 'stint_changed'] = False
            
            # Split laps into pit stops vs racing
            pit_laps = dl[dl['stint_changed']].copy()
            racing_laps = dl[~dl['stint_changed']].copy()
            
        else:
            # Fallback if no stint data available
            fastest_lap = driver_laps['LapTimeSeconds'].min()
            outlier_threshold = fastest_lap * 1.20
            racing_laps = driver_laps[driver_laps['LapTimeSeconds'] <= outlier_threshold]
            pit_laps = driver_laps[driver_laps['LapTimeSeconds'] > outlier_threshold]
        
        # Get race context
        race_name = race_session.event['EventName']
        race_year = race_session.event.year
        total_laps = int(driver_laps['LapNumber'].max())
        
        st.subheader(f"🏎️ {selected_driver}'s Race Performance")
        st.caption(f"How {selected_driver} performed throughout the {race_name}")
        
        # Calculate key metrics
        if not racing_laps.empty:
            fastest_time = racing_laps['LapTimeSeconds'].min()
            fastest_lap_num = racing_laps.loc[racing_laps['LapTimeSeconds'].idxmin(), 'LapNumber']
        
        # Create the lap time chart
        fig = go.Figure()
        
        # F1 tire colors
        compound_colors = {
            'SOFT': '#FF3333',      # Red
            'MEDIUM': '#FFFF33',    # Yellow
            'HARD': '#FFFFFF',      # White
            'INTERMEDIATE': '#33FF33', # Green
            'WET': '#3333FF'        # Blue
        }
        
        # Plot each tire stint separately so lines don't connect across pit stops
        if not racing_laps.empty and 'Compound' in racing_laps.columns:
            racing_laps_sorted = racing_laps.sort_values('LapNumber')
            racing_laps_sorted['compound_change'] = (racing_laps_sorted['Compound'] != racing_laps_sorted['Compound'].shift(1))
            racing_laps_sorted['stint_id'] = racing_laps_sorted['compound_change'].cumsum()
            
            # Track which compounds we've already added to legend
            compounds_in_legend = set()
            
            # Draw each stint as its own line
            for stint_id, stint_data in racing_laps_sorted.groupby('stint_id'):
                compound = stint_data['Compound'].iloc[0]
                color = compound_colors.get(compound, '#888888')
                
                # Only show in legend if we haven't seen this compound yet
                show_in_legend = compound not in compounds_in_legend
                if show_in_legend:
                    compounds_in_legend.add(compound)
                
                fig.add_trace(go.Scatter(
                    x=stint_data['LapNumber'],
                    y=stint_data['LapTimeSeconds'],
                    mode='markers+lines',
                    name=f"{compound} Tires",
                    line=dict(color=color, width=3),
                    marker=dict(color=color, size=5),
                    showlegend=show_in_legend,
                    legendgroup=compound,
                    hovertemplate=(
                        f"<b>{selected_driver}</b><br>" +
                        f"Lap: %{{x}}<br>" +
                        f"Time: %{{customdata}}<br>" +
                        f"Tires: {compound}<br>" +
                        "<extra></extra>"
                    ),
                    customdata=[f"{int(t//60)}:{t%60:06.3f}" for t in stint_data['LapTimeSeconds']]
                ))
        else:
            # If no tire data, just plot all laps as one line
            fig.add_trace(go.Scatter(
                x=racing_laps['LapNumber'],
                y=racing_laps['LapTimeSeconds'],
                mode='markers+lines',
                name="Race Pace",
                line=dict(color='#3366CC', width=3),
                marker=dict(color='#3366CC', size=5),
                hovertemplate=(
                    f"<b>{selected_driver}</b><br>" +
                    f"Lap: %{{x}}<br>" +
                    f"Time: %{{customdata}}<br>" +
                    "<extra></extra>"
                ),
                customdata=[f"{int(t//60)}:{t%60:06.3f}" for t in racing_laps['LapTimeSeconds']]
            ))
        
        # Mark pit stops with orange diamonds
        if not pit_laps.empty and not racing_laps.empty:
            # Put pit markers slightly above the slowest racing lap for visibility
            max_racing_time = racing_laps['LapTimeSeconds'].max()
            pit_marker_y = max_racing_time + 0.5
            
            fig.add_trace(go.Scatter(
                x=pit_laps['LapNumber'],
                y=[pit_marker_y] * len(pit_laps),
                mode='markers',
                name="Pit Stops",
                marker=dict(
                    color='orange',
                    size=12,
                    symbol='diamond',
                    line=dict(width=2, color='black')
                ),
                hovertemplate=(
                    f"<b>{selected_driver}</b><br>" +
                    f"Lap: %{{x}}<br>" +
                    f"Pit Stop<br>" +
                    "<extra></extra>"
                )
            ))
        
        # Mark fastest lap with gold star
        if not racing_laps.empty:
            fastest_lap_data = racing_laps.loc[racing_laps['LapTimeSeconds'].idxmin()]
            fig.add_trace(go.Scatter(
                x=[fastest_lap_data['LapNumber']],
                y=[fastest_lap_data['LapTimeSeconds']],
                mode='markers',
                name="Fastest Lap",
                marker=dict(
                    color='gold',
                    size=15,
                    symbol='star',
                    line=dict(width=2, color='black')
                ),
                hovertemplate=(
                    f"<b>{selected_driver}</b><br>" +
                    f"Fastest Lap: {int(fastest_lap_data['LapNumber'])}<br>" +
                    f"Time: {int(fastest_time//60)}:{fastest_time%60:06.3f}<br>" +
                    "<extra></extra>"
                )
            ))
        
        # Set up the chart
        fig.update_layout(
            title=f"{selected_driver}'s Lap Times Throughout the Race",
            xaxis_title="Lap Number",
            yaxis_title="Lap Time",
            height=450,
            xaxis=dict(
                range=[0, total_laps + 1],
                dtick=10,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            yaxis=dict(
                gridcolor='rgba(128,128,128,0.2)'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # metrics row
        if not racing_laps.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            # Calculate the key numbers
            fastest_formatted = f"{int(fastest_time // 60)}:{fastest_time % 60:06.3f}"
            avg_lap_time = racing_laps['LapTimeSeconds'].mean()
            avg_formatted = f"{int(avg_lap_time // 60)}:{avg_lap_time % 60:06.3f}"
            num_pit_stops = len(pit_laps)
            
            with col1:
                st.metric("Best Lap", fastest_formatted, f"Lap {int(fastest_lap_num)}")
            
            with col2:
                st.metric("Average Lap", avg_formatted)
            
            with col3:
                st.metric("Total Laps", total_laps)
            
            with col4:
                st.metric("Pit Stops", num_pit_stops)
        
        # Race story in one paragraph
        st.subheader("Race Summary")
        
        if not racing_laps.empty and len(racing_laps) >= 10:
            # Figure out what happened during the race
            early_laps = racing_laps.head(len(racing_laps)//3)
            late_laps = racing_laps.tail(len(racing_laps)//3)
            early_avg = early_laps['LapTimeSeconds'].mean()
            late_avg = late_laps['LapTimeSeconds'].mean()
            time_difference = late_avg - early_avg
            
            summary_parts = []
            
            # How did their pace change?
            if time_difference > 2.0:
                summary_parts.append(f"Lost {time_difference:.1f} seconds per lap from start to finish, likely due to tire degradation or mechanical issues")
            elif time_difference > 0.5:
                summary_parts.append(f"Lap times increased by {time_difference:.1f}s per lap due to normal tire wear")
            elif time_difference < -1.0:
                summary_parts.append(f"Improved by {abs(time_difference):.1f} seconds per lap throughout the race")
            else:
                summary_parts.append("Maintained consistent lap times throughout the race")
            
            # What was their pit strategy?
            if not pit_laps.empty:
                pit_lap_numbers = sorted(pit_laps['LapNumber'].tolist())
                num_stops = len(pit_lap_numbers)
                
                if num_stops == 1:
                    summary_parts.append(f"Used a one-stop strategy with pit stop on lap {int(pit_lap_numbers[0])}")
                elif num_stops == 2:
                    summary_parts.append(f"Used a two-stop strategy with pit stops on laps {int(pit_lap_numbers[0])} and {int(pit_lap_numbers[1])}")
                else:
                    pit_laps_str = ", ".join([str(int(lap)) for lap in pit_lap_numbers])
                    summary_parts.append(f"Made {num_stops} pit stops on laps {pit_laps_str}")
            
            # What tires did they use for their best lap?
            if 'Compound' in racing_laps.columns:
                fastest_tire = racing_laps.loc[racing_laps['LapTimeSeconds'].idxmin(), 'Compound']
                if pd.notna(fastest_tire):
                    tire_type = fastest_tire.lower()
                    summary_parts.append(f"Set fastest lap on {tire_type} tires")
            
            # Put it all together
            summary_text = ". ".join(summary_parts) + "."
            st.write(summary_text)
        
        # detailed data table
        with st.expander("📊 Detailed Lap Data", expanded=False):
            if not driver_laps.empty:
                display_data = []
                
                for _, lap in driver_laps.iterrows():
                    lap_time = lap['LapTimeSeconds']
                    formatted_time = f"{int(lap_time // 60)}:{lap_time % 60:06.3f}"
                    
                    # Figure out what type of lap this was
                    if lap['LapNumber'] in pit_laps['LapNumber'].values:
                        lap_type = "Pit Stop"
                    elif lap['LapNumber'] == fastest_lap_num:
                        lap_type = "Fastest"
                    else:
                        lap_type = "Racing"
                    
                    row = {
                        'Lap': int(lap['LapNumber']),
                        'Time': formatted_time,
                        'Type': lap_type
                    }
                    
                    # Add tire info if we have it
                    if 'Compound' in lap and pd.notna(lap['Compound']):
                        row['Tires'] = lap['Compound']
                    
                    display_data.append(row)
                
                display_df = pd.DataFrame(display_data)
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                st.caption("""
                **Gold star** = Fastest lap of the race  
                **Orange diamonds** = Pit stops  
                **Tire colors** = Different compounds used (Red=Soft, Yellow=Medium, White=Hard)
                """)
    
    except Exception as e:
        st.error(f"Error analyzing {selected_driver}'s lap times: {e}")
        st.info("This might be due to missing lap time data for this driver.")

def plot_driver_laptimes(race_session, selected_driver):
    """Keep the old function name working for backwards compatibility."""
    return plot_driver_pace_progression(race_session, selected_driver)