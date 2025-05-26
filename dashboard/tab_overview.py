import dash.html as html
import dash.dcc as dcc
from dash.dependencies import Input, Output
import pandas as pd # Added import
from data_ingestion.nba_data import get_active_players_data # Added import

# Import the app instance from the main app.py file
# This is possible because app.py defines 'app' before importing this module
from app import app

# Placeholder player options for the dropdown
# This will be made dynamic in a future task.
TEMP_PLAYER_OPTIONS = [
    {'label': 'Player A (Placeholder)', 'value': 'player_a_placeholder'},
    {'label': 'Player B (Placeholder)', 'value': 'player_b_placeholder'},
    {'label': 'LeBron James (Example)', 'value': 'lebron_james_2544'},
    {'label': 'Stephen Curry (Example)', 'value': 'stephen_curry_201939'},
]

layout = html.Div([
    html.H3("Overview & Why Undervalued Summary", style={'marginTop': '20px', 'marginBottom': '10px'}),
    dcc.Dropdown(
        id='player-dropdown-tab1',
        options=TEMP_PLAYER_OPTIONS,
        value=TEMP_PLAYER_OPTIONS[0]['value'], # Default to the first player in the list
        clearable=False,
        style={'marginBottom': '20px'}
    ),
    html.Hr(),
    html.H4("Key 'Undervalued' Indicators:", style={'marginTop': '20px'}),
    dcc.Loading( # Added Loading component
        id="loading-indicators-tab1",
        type="circle",
        children=[
            html.Div(
                id='undervalued-indicators-tab1',
                children="Undervalued indicators will appear here." # Initial placeholder text
            )
        ]
    ),
    html.Hr(),
    html.H4("Brief Textual Summary:", style={'marginTop': '20px'}),
    html.Div(
        id='textual-summary-tab1',
        children="Textual summary will appear here." # Initial placeholder text
    )
])

# Callbacks for Tab 1: Overview
@app.callback(
    [Output('undervalued-indicators-tab1', 'children'),
     Output('textual-summary-tab1', 'children')],
    [Input('player-dropdown-tab1', 'value')]
)
def update_overview_content(selected_player_value):
    if not selected_player_value:
        return [html.P("Please select a player to see details.")], "Please select a player to see details."

    try:
        player_id_int = int(selected_player_value.split('_')[-1])
        name_parts = selected_player_value.split('_')[:-1]
        display_player_name = ' '.join([part.title() for part in name_parts]) if name_parts else selected_player_value.title()
    except (ValueError, AttributeError, IndexError):
        return [html.P("Invalid player selection format.")], "Invalid player selection format."

    all_players_df = get_active_players_data()

    if all_players_df.empty:
        return [html.P("Could not retrieve player data for analysis.")], "Could not retrieve player data."

    player_series_list = all_players_df[all_players_df['PLAYER_ID'] == player_id_int]
    if player_series_list.empty:
        return [html.P(f"Data not found for {display_player_name} (ID: {player_id_int}).")], f"Data not found for {display_player_name}."
    
    player_data = player_series_list.iloc[0]

    # Calculate PPG for all players and the selected player
    all_players_df['PPG'] = 0.0 # Initialize PPG column
    # Calculate PPG only for players with GP > 0
    mask_gp_gt_0 = all_players_df['GP'] > 0
    all_players_df.loc[mask_gp_gt_0, 'PPG'] = all_players_df.loc[mask_gp_gt_0, 'PTS'] / all_players_df.loc[mask_gp_gt_0, 'GP']
    
    selected_player_gp = player_data.get('GP', 0)
    selected_player_pts = player_data.get('PTS', 0)
    selected_player_ppg = selected_player_pts / selected_player_gp if selected_player_gp > 0 else 0

    # Calculate Percentile Ranks
    # Ensure EFF_SCORE and PPG columns are numeric, coercing errors for safety
    all_players_df['EFF_SCORE'] = pd.to_numeric(all_players_df['EFF_SCORE'], errors='coerce').fillna(0)
    all_players_df['PPG'] = pd.to_numeric(all_players_df['PPG'], errors='coerce').fillna(0)

    all_players_df['EFF_SCORE_Percentile'] = all_players_df['EFF_SCORE'].rank(pct=True, method='average') * 100
    all_players_df['PPG_Percentile'] = all_players_df['PPG'].rank(pct=True, method='average') * 100
    
    # Re-filter for the selected player to get their percentile values
    player_percentiles_series = all_players_df[all_players_df['PLAYER_ID'] == player_id_int].iloc[0]
    
    eff_percentile = player_percentiles_series.get('EFF_SCORE_Percentile', 0)
    ppg_percentile = player_percentiles_series.get('PPG_Percentile', 0)
    selected_player_eff_score = player_data.get('EFF_SCORE', 0)

    indicator_elements = [
        html.H5(f"Key Metric Percentiles for {display_player_name}:"),
        html.P(f"Player's EFF_SCORE ({selected_player_eff_score:.2f}) is in the {eff_percentile:.0f}th percentile among all players."),
        html.P(f"Player's Points Per Game ({selected_player_ppg:.2f}) is in the {ppg_percentile:.0f}th percentile among all players.")
    ]
    
    # Example of a simple "undervalued" check (can be expanded)
    # For this example, let's use EFF_SCORE percentile and minutes per game.
    # This requires FGA, FTA, TOV to be added to get_active_players_data. For now, let's use MIN / GP.
    if selected_player_gp > 0:
        minutes_per_game = player_data.get('MIN', 0) / selected_player_gp
        if eff_percentile > 75 and minutes_per_game < 28: # Example thresholds
             indicator_elements.append(html.P(f"Note: High EFF_SCORE percentile ({eff_percentile:.0f}th) on relatively moderate minutes per game ({minutes_per_game:.1f} MPG). Potential for higher impact with more minutes?", style={'color': 'green'}))
    
    summary_text = f"Detailed textual summary for {display_player_name} will be generated by an agent in a future step."

    return indicator_elements, summary_text
