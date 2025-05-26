import dash.html as html
import dash.dcc as dcc
from dash.dependencies import Input, Output, State # State imported as suggested
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc # Added

# Import the app instance from the main app.py file
from app import app
# Import data fetching functions
from data_ingestion.nba_data import get_player_shot_chart_data, CURRENT_SEASON # Added

layout = html.Div([
    html.H3("Shooting Analysis", style={'marginTop': '20px', 'marginBottom': '10px'}),
    
    # Filters
    html.Div([
        dcc.Dropdown(
            id='shot-chart-timeframe-filter-tab3',
            options=[
                {'label': 'Full Season', 'value': 'full'},
                {'label': 'Last 10 Games', 'value': 'last10'} # Timeframe not yet integrated in data fetching
            ],
            value='full',
            placeholder="Select Timeframe",
            clearable=False,
            style={'width': '200px', 'display': 'inline-block', 'marginRight': '10px'}
        ),
        dcc.RadioItems(
            id='shot-chart-type-filter-tab3',
            options=[
                {'label': 'Makes & Misses (Scatter)', 'value': 'scatter'},
                {'label': 'Heatmap', 'value': 'heatmap'}
            ],
            value='scatter',
            labelStyle={'display': 'inline-block', 'marginRight': '10px', 'marginLeft': '10px'}
        ),
    ], style={'marginBottom': '20px'}),

    # Heatmap specific options (visibility controlled by callback)
    html.Div(id='heatmap-options-wrapper-tab3', children=[ # Wrapper div for style manipulation
        dcc.RadioItems(
            id='shot-chart-heatmap-metric-filter-tab3',
            options=[
                {'label': 'Field Goal % (FG%)', 'value': 'fg_pct'},
                {'label': 'True Shooting % (TS%)', 'value': 'ts_pct'},
                {'label': 'Points Per Shot (PPS)', 'value': 'pps'}
            ],
            value='fg_pct',
            labelStyle={'display': 'inline-block', 'marginRight': '10px', 'marginLeft': '10px'}
        )
    ], style={'marginBottom': '20px'}), # Initial style set here, callback will update it

    # Shot Chart Graph
    dcc.Graph(id='shot-chart-graph-tab3'),
    
    html.Hr(style={'marginTop': '20px', 'marginBottom': '20px'}),
    
    # Shooting Splits
    html.H4("Shooting Splits", style={'marginTop': '20px'}),
    html.Div(id='shooting-splits-tab3', children=["Shooting splits will appear here."]),
    
    html.Hr(style={'marginTop': '20px', 'marginBottom': '20px'}),
    
    # Shot Breakdown
    html.H4("Shot Breakdown by Type/Distance", style={'marginTop': '20px'}),
    html.Div(id='shot-breakdown-tab3', children=["Shot breakdown will appear here."])
])

# Callback for Tab 3: Update placeholders and graph based on filters
@app.callback(
    [Output('shot-chart-graph-tab3', 'figure'),
     Output('shooting-splits-tab3', 'children'),
     Output('shot-breakdown-tab3', 'children'),
     Output('heatmap-options-wrapper-tab3', 'style')], # Target the wrapper div for style
    [Input('player-dropdown-tab1', 'value'), # From Tab 1
     Input('shot-chart-timeframe-filter-tab3', 'value'),
     Input('shot-chart-type-filter-tab3', 'value'),
     Input('shot-chart-heatmap-metric-filter-tab3', 'value')]
)
def update_shooting_tab_placeholders(selected_player, timeframe, chart_type, heatmap_metric): # Renamed selected_player_value
    
    if not selected_player:
        # Default empty state for all outputs
        return {}, "Select a player.", "Select a player.", {'display': 'none'}
    try:
        player_id_int = int(selected_player.split('_')[-1])
        # More robust name extraction
        name_parts = selected_player.split('_')[:-1] # Exclude ID
        display_player_name = ' '.join([part.title() for part in name_parts]) if name_parts else selected_player.title()

    except (ValueError, AttributeError, IndexError):
        return {}, "Invalid player selection.", "Invalid player selection.", {'display': 'none'}

    heatmap_options_style = {'display': 'block', 'marginBottom': '20px'} if chart_type == 'heatmap' else {'display': 'none'}
    
    # Initialize outputs
    graph_figure = {'layout': {'title': 'Select chart type'}}
    splits_elements = [html.P(f"Shooting splits data not available for {display_player_name}.")]
    # Initialize breakdown_elements after display_player_name is defined
    breakdown_elements = [html.P(f"Shot breakdown data not available for {display_player_name}.")]


    # Fetch data (common for both scatter and heatmap)
    season_to_fetch = CURRENT_SEASON 
    season_type_to_fetch = "Regular Season" # Timeframe filter not yet integrated
    print(f"Fetching shot data for {display_player_name} ({player_id_int}), season {season_to_fetch} for Tab 3 display...")
    shot_df = get_player_shot_chart_data(player_id_int, season_to_fetch, season_type_to_fetch)

    if shot_df is None or shot_df.empty:
        error_message = f'No shot data available for {display_player_name} ({season_to_fetch})'
        print(f"No shot_df returned for player {player_id_int} for Tab 3.")
        graph_figure = {'layout': {'title': error_message}}
        # splits_elements keeps its default "not available" message
        # breakdown_elements keeps its default "not available" message if shot_df is None or empty
        # No change to heatmap_options_style based on breakdown logic
    else: # This else corresponds to: if shot_df is not None and not shot_df.empty:
        # Calculate splits (logic from previous step, now uses common shot_df)
        fg_pct_str = "N/A"
        made_shots_count = 0
        total_shots_count = len(shot_df)
        if 'SHOT_MADE_FLAG' in shot_df.columns and total_shots_count > 0:
            made_shots_count = shot_df['SHOT_MADE_FLAG'].sum()
            fg_pct = made_shots_count / total_shots_count
            fg_pct_str = f"{fg_pct:.1%}"
        
        fg3_pct_str = "N/A"
        made_three_pt_shots_count = 0
        total_three_pt_shots_count = 0
        if 'SHOT_TYPE' in shot_df.columns and 'SHOT_MADE_FLAG' in shot_df.columns:
            three_pt_attempts_df = shot_df[shot_df['SHOT_TYPE'].str.contains('3PT', na=False)]
            total_three_pt_shots_count = len(three_pt_attempts_df)
            if total_three_pt_shots_count > 0:
                made_three_pt_shots_count = three_pt_attempts_df['SHOT_MADE_FLAG'].sum()
                fg3_pct = made_three_pt_shots_count / total_three_pt_shots_count
                fg3_pct_str = f"{fg3_pct:.1%}"
        elif 'SHOT_MADE_FLAG' in shot_df.columns:
             fg3_pct_str = "N/A (SHOT_TYPE column missing)"
             print("Warning: SHOT_TYPE column not found in shot_df, cannot calculate 3P FG%.")

        splits_elements = [
            html.H5(f"Shooting Splits for {display_player_name}"),
            html.P(f"Season: {season_to_fetch} ({season_type_to_fetch})"),
            html.P(f"Overall FG%: {fg_pct_str} ({made_shots_count}/{total_shots_count})"),
            html.P(f"3-Point FG%: {fg3_pct_str} ({made_three_pt_shots_count}/{total_three_pt_shots_count})")
        ]

        # Generate graph based on chart_type
        if chart_type == 'scatter':
            if 'SHOT_MADE_FLAG' in shot_df.columns and 'EVENT_TYPE' not in shot_df.columns:
                shot_df['EVENT_TYPE'] = shot_df['SHOT_MADE_FLAG'].apply(lambda x: 'Made Shot' if x == 1 else 'Missed Shot')

            if 'LOC_X' in shot_df.columns and 'LOC_Y' in shot_df.columns and 'EVENT_TYPE' in shot_df.columns:
                graph_figure = px.scatter(
                    shot_df, x='LOC_X', y='LOC_Y', color='EVENT_TYPE', symbol='EVENT_TYPE',
                    title=f"Shot Chart: {display_player_name} ({season_to_fetch}) - Makes & Misses",
                    color_discrete_map={'Made Shot': 'green', 'Missed Shot': 'red'}
                )
                graph_figure.update_xaxes(range=[-250, 250])
                graph_figure.update_yaxes(range=[-50, 420])
                graph_figure.update_layout(yaxis_title="Distance from Hoop (tenths of a foot)", xaxis_title="Court Width (tenths of a foot)")
            else:
                graph_figure = {'layout': {'title': f'Shot data columns missing for scatter plot for {display_player_name}'}}
                print(f"Missing required columns (LOC_X, LOC_Y, EVENT_TYPE/SHOT_MADE_FLAG) in shot_df for player {player_id_int}")

        elif chart_type == 'heatmap':
            if 'LOC_X' in shot_df.columns and 'LOC_Y' in shot_df.columns:
                title = f"Shot Density Heatmap: {display_player_name} ({season_to_fetch})"
                # Note about metric-specific heatmaps coming soon
                density_note = "(Showing Density - Metric Specific Heatmaps Coming Soon!)"
                if heatmap_metric == 'fg_pct':
                    title = f"Shot Density for {display_player_name} (FG% per bin: Coming Soon)"
                elif heatmap_metric == 'ts_pct':
                    title = f"Shot Density for {display_player_name} (TS% per bin: Coming Soon)"
                elif heatmap_metric == 'pps':
                    title = f"Shot Density for {display_player_name} (PPS per bin: Coming Soon)"
                else: # Default title if metric not specifically handled for title, but still show density
                    title = f"Shot Density Heatmap: {display_player_name} ({season_to_fetch}) - Metric: {heatmap_metric} {density_note}"


                graph_figure = px.density_heatmap(
                    shot_df, x='LOC_X', y='LOC_Y',
                    nbinsx=30, nbinsy=30,
                    title=title
                )
                graph_figure.update_xaxes(range=[-250, 250])
                graph_figure.update_yaxes(range=[-50, 420])
                graph_figure.update_layout(yaxis_title="Distance from Hoop (tenths of a foot)", xaxis_title="Court Width (tenths of a foot)")
            else:
                graph_figure = {'layout': {'title': f'Shot data columns missing for heatmap for {display_player_name}'}}
                print(f"Missing LOC_X or LOC_Y for heatmap for player {player_id_int}")
    
        # Logic for breakdown_elements (replaces old breakdown_text logic)
        if 'SHOT_ZONE_BASIC' not in shot_df.columns or 'SHOT_MADE_FLAG' not in shot_df.columns:
            print("Warning: SHOT_ZONE_BASIC or SHOT_MADE_FLAG missing from shot_df. Cannot generate breakdown.")
            breakdown_elements = [html.P(f"Shot breakdown data requires SHOT_ZONE_BASIC and SHOT_MADE_FLAG columns.")]
        else:
            grouped_shots = shot_df.groupby('SHOT_ZONE_BASIC').agg(
                FGA=('SHOT_MADE_FLAG', 'count'),
                FGM=('SHOT_MADE_FLAG', 'sum')
            ).reset_index()

            if not grouped_shots.empty:
                grouped_shots['FG_PCT'] = grouped_shots['FGM'] / grouped_shots['FGA']
                
                table_header = [html.Thead(html.Tr([html.Th("Shot Zone"), html.Th("FGM"), html.Th("FGA"), html.Th("FG%")]))]
                table_rows = []
                for index, row in grouped_shots.iterrows():
                    table_rows.append(html.Tr([
                        html.Td(row['SHOT_ZONE_BASIC']),
                        html.Td(row['FGM']),
                        html.Td(row['FGA']),
                        html.Td(f"{row['FG_PCT']:.1%}" if pd.notna(row['FG_PCT']) else "N/A")
                    ]))
                
                breakdown_table = dbc.Table(table_header + [html.Tbody(table_rows)], bordered=True, striped=True, hover=True, responsive=True, size='sm')
                # Assign the new list of components to breakdown_elements
                breakdown_elements = [
                    html.H5(f"Shot Breakdown by Zone for {display_player_name}"),
                    html.P(f"Season: {season_to_fetch} ({season_type_to_fetch})"),
                    breakdown_table
                ]
            else:
                breakdown_elements = [html.P(f"No shot zone data to aggregate for {display_player_name}.")]
        
    return graph_figure, splits_elements, breakdown_elements, heatmap_options_style
