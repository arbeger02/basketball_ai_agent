import dash.html as html
import dash.dcc as dcc
import dash_table
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px # Added import
from data_ingestion.nba_data import get_active_players_data # Added import

# Import the app instance from the main app.py file
# This is possible because app.py defines 'app' before importing this module
from app import app

layout = html.Div([
    html.H3("Traditional & Advanced Stats", style={'marginTop': '20px', 'marginBottom': '10px'}),
    dash_table.DataTable(
        id='player-stats-table-tab2',
        # Columns will be set by the callback now, but initial definition is good for structure
        columns=[{'name': 'Statistic', 'id': 'Statistic'}, {'name': 'Value', 'id': 'Value'}],
        data=[], # Initialize with empty data
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'border': '1px solid black'
        },
        style_data={
            'border': '1px solid grey'
        },
        page_size=10, 
    ),
    html.Hr(style={'marginTop': '20px', 'marginBottom': '20px'}),
    html.H4("Comparison to Positional Averages", style={'marginTop': '20px'}),
    dcc.Graph(id='pos-avg-bar-charts-graph-tab2'), 
    html.Hr(style={'marginTop': '20px', 'marginBottom': '20px'}),
    html.H4("Stat Progression Over Seasons", style={'marginTop': '20px'}),
    dcc.Graph(id='stat-progression-line-charts-graph-tab2') # Changed from html.Div to dcc.Graph
])

# Callback for Tab 2: Update Player Stats Table and Positional Avg Chart
@app.callback(
    [Output('player-stats-table-tab2', 'data'),
     Output('player-stats-table-tab2', 'columns'),
     Output('pos-avg-bar-charts-graph-tab2', 'figure')],
    [Input('player-dropdown-tab1', 'value')] # Input from Tab 1's dropdown
)
def update_stats_table_tab2(selected_player_value):
    if not selected_player_value:
        return [], [], {} # Return empty for table data, columns, and figure

    all_players_df = get_active_players_data()
    player_series = None
    table_data = []
    table_columns = [{'name': 'Statistic', 'id': 'Statistic'}, {'name': 'Value', 'id': 'Value'}]
    bar_fig = {'layout': {'title': 'Select a player'}} # Default empty figure

    if all_players_df.empty:
        # Handle case where get_active_players_data returns empty
        return [], [], {'layout': {'title': 'No player data available from source.'}}

    try:
        player_id_int = int(selected_player_value.split('_')[-1])
        filtered_df = all_players_df[all_players_df['PLAYER_ID'] == player_id_int]
        if not filtered_df.empty:
            player_series = filtered_df.iloc[0]
    except (ValueError, IndexError): # Handle potential errors from split or int conversion
        return [], [], {'layout': {'title': 'Invalid player selection format.'}}


    if player_series is not None:
        # Populate Player Stats Table
        table_data = [{'Statistic': k, 'Value': v} for k, v in player_series.items()]
        # table_columns are already defined with default values, or could be dynamic:
        # table_columns = [{'name': col, 'id': col} for col in player_series.index] -> this would make a wide table.
        # For a two-column table (Statistic, Value), the above conversion is better.

        # Prepare Data for Bar Chart
        mock_positional_averages = {
            'Guard': {'PTS': 18.0, 'REB': 4.0, 'AST': 5.0, 'EFF_SCORE': 20.0},
            'Forward': {'PTS': 20.0, 'REB': 7.0, 'AST': 3.5, 'EFF_SCORE': 22.0},
            'Center': {'PTS': 15.0, 'REB': 10.0, 'AST': 2.0, 'EFF_SCORE': 21.0}
        }

        # Mock Player Position (simplified)
        player_name_for_mock = player_series.get('PLAYER_NAME', '')
        if player_name_for_mock.startswith('L') or player_name_for_mock.startswith('K') or player_name_for_mock.startswith('J'): # LeBron, Kevin, James etc.
            mock_player_position = 'Forward'
        elif player_name_for_mock.startswith('S') or player_name_for_mock.startswith('D') or player_name_for_mock.startswith('C'): # Steph, Damian, Chris Paul etc.
            mock_player_position = 'Guard'
        else:
            mock_player_position = 'Center'
        
        avg_stats = mock_positional_averages.get(mock_player_position, {})

        key_stats_to_compare = ['PTS', 'REB', 'AST', 'EFF_SCORE']
        player_chart_stats = [player_series.get(stat, 0) for stat in key_stats_to_compare]
        avg_chart_stats = [avg_stats.get(stat, 0) for stat in key_stats_to_compare]

        chart_df_data = []
        for i, stat_name in enumerate(key_stats_to_compare):
            chart_df_data.append({'Statistic': stat_name, 'Value': player_chart_stats[i], 'Type': player_series.get('PLAYER_NAME', 'Selected Player')})
            chart_df_data.append({'Statistic': stat_name, 'Value': avg_chart_stats[i], 'Type': f"Avg {mock_player_position}"})
        
        chart_df = pd.DataFrame(chart_df_data)

        if not chart_df.empty:
            bar_fig = px.bar(
                chart_df,
                x='Statistic',
                y='Value',
                color='Type',
                barmode='group',
                title=f"{player_series.get('PLAYER_NAME', 'Selected Player')} vs. Avg {mock_player_position}"
            )
        else:
            bar_fig = {'layout': {'title': 'Comparison data not available for player or position.'}}
    else:
        # Player not found after filtering
        return [], [], {'layout': {'title': f"Player data not found for ID: {player_id_int if 'player_id_int' in locals() else selected_player_value}"}}

    return table_data, table_columns, bar_fig

# Callback for Tab 2: Update Stat Progression Line Charts
@app.callback(
    Output('stat-progression-line-charts-graph-tab2', 'figure'),
    [Input('player-dropdown-tab1', 'value')] # Input from Tab 1's dropdown
)
def update_stat_progression_charts(selected_player_value):
    if not selected_player_value:
        return {} # Return empty figure if no player is selected

    player_id_int = None
    try:
        # Assuming selected_player_value format is like 'playername_id', e.g., 'lebron_james_2544'
        player_id_int = int(selected_player_value.split('_')[-1])
    except (ValueError, IndexError):
        return {'layout': {'title': 'Invalid player selection format for progression chart.'}}

    mock_career_stats = {
        2544: [ # LeBron James
            {'SEASON': '2020-21', 'PLAYER_NAME': 'LeBron James', 'PTS': 25.0, 'AST': 7.8, 'REB': 7.7, 'EFF_SCORE': 28.0},
            {'SEASON': '2021-22', 'PLAYER_NAME': 'LeBron James', 'PTS': 30.3, 'AST': 6.2, 'REB': 8.2, 'EFF_SCORE': 33.5},
            {'SEASON': '2022-23', 'PLAYER_NAME': 'LeBron James', 'PTS': 28.9, 'AST': 6.8, 'REB': 8.3, 'EFF_SCORE': 31.0}
        ],
        201939: [ # Stephen Curry
            {'SEASON': '2020-21', 'PLAYER_NAME': 'Stephen Curry', 'PTS': 32.0, 'AST': 5.8, 'REB': 5.5, 'EFF_SCORE': 35.0},
            {'SEASON': '2021-22', 'PLAYER_NAME': 'Stephen Curry', 'PTS': 25.5, 'AST': 6.3, 'REB': 5.2, 'EFF_SCORE': 29.0},
            {'SEASON': '2022-23', 'PLAYER_NAME': 'Stephen Curry', 'PTS': 29.4, 'AST': 6.3, 'REB': 6.1, 'EFF_SCORE': 33.0}
        ],
        # Example for a player from TEMP_PLAYER_OPTIONS in tab_overview
        # Assuming 'player_a_placeholder' value was 'player_a_placeholder_1'
        1: [ 
            {'SEASON': '2021-22', 'PLAYER_NAME': 'Player A (Placeholder)', 'PTS': 10.0, 'AST': 2.0, 'REB': 3.0, 'EFF_SCORE': 12.0},
            {'SEASON': '2022-23', 'PLAYER_NAME': 'Player A (Placeholder)', 'PTS': 12.0, 'AST': 2.5, 'REB': 3.5, 'EFF_SCORE': 15.0}
        ]
    }

    player_historical_data = mock_career_stats.get(player_id_int)

    if player_historical_data is None:
        return {'layout': {'title': f'Stat progression data not available for player ID {player_id_int}'}}

    progression_df = pd.DataFrame(player_historical_data)
    
    # Ensure SEASON is treated as a categorical and sorted correctly for the line chart
    # This is important if seasons are not lexicographically sorted by default (e.g. '2022-23' before '2021-22')
    # However, for typical season strings 'YYYY-YY', default string sort usually works.
    # If explicit sorting is needed: progression_df['SEASON'] = pd.Categorical(progression_df['SEASON'], sorted(progression_df['SEASON'].unique()))
    # progression_df = progression_df.sort_values('SEASON')


    stats_to_plot = ['PTS', 'AST', 'REB', 'EFF_SCORE']
    # Filter out any stats not present in the DataFrame to avoid melt errors
    stats_to_plot_present = [stat for stat in stats_to_plot if stat in progression_df.columns]
    
    if not stats_to_plot_present:
        return {'layout': {'title': 'No relevant stats found for progression chart.'}}

    melted_df = progression_df.melt(
        id_vars=['SEASON', 'PLAYER_NAME'], 
        value_vars=stats_to_plot_present, 
        var_name='Statistic', 
        value_name='Value'
    )

    line_fig = {} # Default to empty figure
    if not melted_df.empty:
        player_name = melted_df['PLAYER_NAME'].iloc[0] # Get player name for title
        line_fig = px.line(
            melted_df,
            x='SEASON',
            y='Value',
            color='Statistic', # Creates different lines for PTS, AST, REB, EFF_SCORE
            title=f"Stat Progression for {player_name}",
            markers=True # Show markers on the lines
        )
        # Ensure seasons are ordered correctly on the x-axis if they are strings
        line_fig.update_xaxes(type='category') 
    else:
        line_fig = {'layout': {'title': 'No progression data to display for the selected player.'}}
        
    return line_fig
