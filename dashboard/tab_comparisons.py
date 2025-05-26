import dash.html as html
import dash.dcc as dcc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go 
import plotly.express as px # Added import

# Import the app instance from the main app.py file
from app import app
# Import data fetching functions
from data_ingestion.nba_data import get_active_players_data

layout = html.Div([
    html.H3("Player Comparisons", style={'marginTop': '20px', 'marginBottom': '10px'}),
    html.Div([ # Row for dropdowns
        html.Div([ # Primary player display
            html.P("Primary Player (Selected in Tab 1):"),
            dcc.Markdown(id='primary-player-display-tab5', style={'fontWeight': 'bold'}) 
        ], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([
            html.P("Select Player to Compare Against:"),
            dcc.Dropdown(
                id='comparison-player-dropdown-tab5',
                placeholder="Select comparison player...",
                multi=False,
                clearable=True 
            )
        ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
    ], style={'display': 'flex', 'justify-content': 'space-between', 'margin-bottom': '20px'}),
    
    dcc.Loading(
        id="loading-comparison-charts-tab5",
        type="circle",
        children=[
            html.Div(id='comparison-radar-chart-div', children=[html.P("Radar chart will appear here.")]),
            html.Hr(),
            html.Div(id='comparison-bar-chart-div', children=[html.P("Side-by-side bar charts will appear here.")])
        ]
    )
])

@app.callback(
    [Output('comparison-player-dropdown-tab5', 'options'),
     Output('comparison-player-dropdown-tab5', 'value'), 
     Output('primary-player-display-tab5', 'children'),
     Output('comparison-radar-chart-div', 'children'),
     Output('comparison-bar-chart-div', 'children')],
    [Input('player-dropdown-tab1', 'value'), 
     Input('comparison-player-dropdown-tab5', 'value')]
)
def update_comparison_tab_structure_and_placeholders(primary_player_key, comparison_player_key):
    all_players_df = get_active_players_data()
    comparison_options = []
    primary_player_name_display = "*No primary player selected in Tab 1.*" # Default text
    current_comparison_value = comparison_player_key # Preserve current selection initially

    # Default placeholder texts
    radar_output = [html.P("Select a primary player (in Tab 1) and a comparison player.")] # Renamed radar_placeholder
    bar_output = [html.P("Select a primary player (in Tab 1) and a comparison player.")] # Renamed bar_placeholder

    player_name_map = {} # To get display names from keys
    player_data_map = {} # To store player data rows/series

    if all_players_df.empty:
        return [], None, primary_player_name_display, [html.P("Could not load player list for comparison.")], [html.P("Could not load player list for comparison.")]

    # Populate player_name_map, player_data_map and comparison_options
    for index, row in all_players_df.iterrows():
        current_player_id = row['PLAYER_ID']
        current_player_name = row['PLAYER_NAME']
        # Assuming primary_player_key and comparison_player_key use this format: 'FirstName_LastName_ID'
        # This format is consistent with TEMP_PLAYER_OPTIONS in tab_overview.py (e.g. 'lebron_james_2544')
        # We need to ensure get_active_players_data() provides names that can be made into this format.
        # For now, we'll construct it from PLAYER_NAME and PLAYER_ID.
        
        # Construct the key by replacing spaces with underscores and appending ID
        # Example: "LeBron James" (PLAYER_NAME), 2544 (PLAYER_ID) -> "LeBron_James_2544"
        # This assumes player names do not have underscores. If they do, this needs a more robust key.
        # The TEMP_PLAYER_OPTIONS in tab_overview used all lowercase for name parts.
        # Let's try to match that for consistency in key generation.
        name_parts_for_key = current_player_name.lower().split(' ')
        constructed_key = "_".join(name_parts_for_key) + f"_{current_player_id}"
        
        player_name_map[constructed_key] = current_player_name
        player_data_map[constructed_key] = row # Store the player's data series

        if primary_player_key != constructed_key:
            comparison_options.append({'label': current_player_name, 'value': constructed_key})
        
        if primary_player_key == constructed_key:
            primary_player_name_display = f"**{current_player_name}**" # Markdown for bold

    if not primary_player_key:
        # primary_player_name_display is already set to default
        comparison_options = [] # No primary player, so no comparison options
        current_comparison_value = None # Clear comparison selection
        # radar_output and bar_output keep their default "Select a primary player..." message
    elif comparison_player_key and not any(opt['value'] == comparison_player_key for opt in comparison_options):
        # If primary player changed and old comparison player is no longer valid (or is the same as primary)
        current_comparison_value = None
        # Update placeholders as only primary is selected now
        primary_name_for_text = player_name_map.get(primary_player_key, "Primary Player")
        radar_output = [html.P(f"Selected primary player: {primary_name_for_text}. Now select a player to compare against.")]
        bar_output = [html.P(f"Selected primary player: {primary_name_for_text}. Now select a player to compare against.")]
    elif primary_player_key and current_comparison_value:
        primary_player_data = player_data_map.get(primary_player_key)
        comparison_player_data = player_data_map.get(current_comparison_value)

        if primary_player_data is not None and comparison_player_data is not None:
            stats_for_radar = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'EFF_SCORE', 'FG_PCT']
            stats_for_radar_display = list(stats_for_radar) # For labels on the chart
            
            primary_stats_values = []
            comparison_stats_values = []

            for i, stat_name in enumerate(stats_for_radar):
                if '_PCT' in stat_name: # Scale percentage stats
                    primary_stats_values.append(primary_player_data.get(stat_name, 0) * 100)
                    comparison_stats_values.append(comparison_player_data.get(stat_name, 0) * 100)
                    stats_for_radar_display[i] = f"{stat_name} (x100)"
                else:
                    primary_stats_values.append(primary_player_data.get(stat_name, 0))
                    comparison_stats_values.append(comparison_player_data.get(stat_name, 0))
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=primary_stats_values,
                theta=stats_for_radar_display,
                fill='toself',
                name=player_name_map.get(primary_player_key, "Primary Player")
            ))
            fig.add_trace(go.Scatterpolar(
                r=comparison_stats_values,
                theta=stats_for_radar_display,
                fill='toself',
                name=player_name_map.get(current_comparison_value, "Comparison Player")
            ))
            
            # Determine max value for radial axis range dynamically
            max_val_primary = max(primary_stats_values) if primary_stats_values else 0
            max_val_comparison = max(comparison_stats_values) if comparison_stats_values else 0
            radial_axis_range_max = max(max_val_primary, max_val_comparison, 0) + 5 # Add some padding

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, radial_axis_range_max])),
                title=f"Comparison: {player_name_map.get(primary_player_key)} vs {player_name_map.get(current_comparison_value)}",
                legend_title_text='Players'
            )
            radar_output = [dcc.Graph(figure=fig)]

            # Create Bar Chart Data
            bar_chart_data_list = []
            primary_name = player_name_map.get(primary_player_key, "Primary Player")
            comparison_name = player_name_map.get(current_comparison_value, "Comparison Player")

            for i, stat_label in enumerate(stats_for_radar_display):
                bar_chart_data_list.append({'Statistic': stat_label, 'Value': primary_stats_values[i], 'Player': primary_name})
                bar_chart_data_list.append({'Statistic': stat_label, 'Value': comparison_stats_values[i], 'Player': comparison_name})
            
            if bar_chart_data_list:
                bar_df = pd.DataFrame(bar_chart_data_list)
                if not bar_df.empty:
                    fig_bar = px.bar(
                        bar_df,
                        x='Statistic',
                        y='Value',
                        color='Player',
                        barmode='group',
                        title=f"Side-by-Side Comparison: {primary_name} vs {comparison_name}"
                    )
                    bar_output = [dcc.Graph(figure=fig_bar)]
                else:
                    bar_output = [html.P("Not enough data to generate bar chart.")]
            else: # Should not happen if radar chart data was processed
                bar_output = [html.P("Could not prepare data for bar chart.")]

        else: # Data not available for one or both players
            radar_output = [html.P("Data not available for one or both selected players for radar chart.")]
            bar_output = [html.P("Data not available for one or both selected players for bar chart.")] # Updated bar_output message
            
    elif primary_player_key: # Only primary player selected
        primary_name_for_text = player_name_map.get(primary_player_key, "Primary Player")
        radar_output = [html.P(f"Selected primary player: {primary_name_for_text}. Now select a player to compare against.")]
        bar_output = [html.P(f"Selected primary player: {primary_name_for_text}. Now select a player to compare against.")]
    # Else, the default placeholders are used (when primary_player_key is None)
        
    return comparison_options, current_comparison_value, primary_player_name_display, radar_output, bar_output
