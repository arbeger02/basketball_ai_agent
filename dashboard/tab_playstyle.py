import dash.html as html
import dash.dcc as dcc
from dash.dependencies import Input, Output
import pandas as pd

# Import the app instance from the main app.py file
from app import app
# Import data fetching functions
from data_ingestion.nba_data import get_active_players_data, CURRENT_SEASON

layout = html.Div([
    html.H3("Playstyle & Role Metrics", style={'marginTop': '20px', 'marginBottom': '10px'}),
    dcc.Loading(
        id="loading-playstyle-tab4",
        type="circle", 
        children=[
            html.Div(id='playstyle-metrics-display-tab4', children=[
                html.P("Select a player to see their playstyle metrics.")
            ])
        ]
    )
])

@app.callback(
    Output('playstyle-metrics-display-tab4', 'children'),
    [Input('player-dropdown-tab1', 'value')]
)
def update_playstyle_metrics_tab4(selected_player_value):
    if not selected_player_value:
        return [html.P("Select a player to see their playstyle metrics.")]

    try:
        player_id_int = int(selected_player_value.split('_')[-1])
        # A slightly more robust name extraction
        name_parts = selected_player_value.split('_')[:-1] # Exclude ID
        display_player_name = ' '.join([part.title() for part in name_parts]) if name_parts else selected_player_value.title()
    except (ValueError, AttributeError, IndexError):
        return [html.P("Invalid player selection.")]

    all_players_df = get_active_players_data()
    if all_players_df.empty:
        return [html.P(f"Could not retrieve player data.")]
    
    player_series = all_players_df[all_players_df['PLAYER_ID'] == player_id_int]
    if player_series.empty:
        return [html.P(f"Data not found for {display_player_name} (ID: {player_id_int}) in the current season dataset.")]
    
    player_data = player_series.iloc[0]

    elements = [html.H4(f"Playstyle Metrics for {display_player_name}")]
    elements.append(html.P(f"Season: {CURRENT_SEASON} (Note: Data is for current active players summary)"))

    gp = player_data.get('GP', 0)
    elements.append(html.H5("Basic Totals & Averages:", style={'marginTop': '15px'}))
    
    # Stats to display as is, and per-game if applicable
    basic_stats_with_per_game = ['PTS', 'REB', 'AST', 'STL', 'BLK']
    other_basic_stats = ['GP', 'MIN', 'EFF_SCORE'] # No per-game for these in this context

    for stat in other_basic_stats:
        val = player_data.get(stat, 'N/A')
        elements.append(html.P(f"{stat}: {val}"))

    for stat in basic_stats_with_per_game:
        val = player_data.get(stat, 'N/A')
        elements.append(html.P(f"{stat}: {val}"))
        if gp > 0:
            per_game_val = player_data.get(stat, 0) / gp
            elements.append(html.P(f"{stat} per game: {per_game_val:.2f}"))
    
    elements.append(html.H5("Shooting Percentages:", style={'marginTop': '15px'}))
    for stat in ['FG_PCT', 'FG3_PCT', 'FT_PCT']:
        val = player_data.get(stat, 0) # Default to 0 if N/A, so formatting works
        elements.append(html.P(f"{stat.replace('_', ' ')}: {val:.1%}"))

    # Calculated Offensive Metrics
    fga = player_data.get('FGA', 0)
    fta = player_data.get('FTA', 0)
    tov = player_data.get('TOV', 0) # Assuming 'TOV' from nba_data.py

    elements.append(html.H5("Calculated Offensive Metrics:", style={'marginTop': '15px'}))
    if pd.notna(fga) and pd.notna(fta) and pd.notna(tov) and (fga > 0 or fta > 0 or tov > 0): # Check if there's data to calculate
        pop = fga + 0.44 * fta + tov
        elements.append(html.P(f"Player Offensive Plays (POP = FGA + 0.44*FTA + TOV): {pop:.2f}"))
        if pop > 0:
            tov_pct = 100 * tov / pop
            elements.append(html.P(f"Turnover % (TOV / POP): {tov_pct:.1f}%"))
        else:
            elements.append(html.P("Turnover % (TOV / POP): N/A (POP is zero)"))
    else:
        elements.append(html.P("FGA, FTA, TOV data not available or zero for these calculations."))


    elements.append(html.H5("Advanced Metrics (Conceptual - Requires More Data/Calculations):", style={'marginTop': '15px'}))
    advanced_metrics_notes = {
        "Usage Rate (USG%)": "Detailed USG% requires FGA, FTA, Turnovers, and team stats. (Coming soon if data permits)",
        "Assist Rate (AST%)": "Detailed AST% requires player MP, team MP, and team FGM. (Coming soon if data permits)",
        "Rebound Rate (REB%)": "Detailed REB% requires player MP, team MP, and team TRB. (Coming soon if data permits)",
        # TOV% is now calculated above, so its note can be removed or changed
        # "Turnover Rate (TOV%)": "Calculated as TOV / (FGA + 0.44*FTA + TOV)" # Example if keeping it
    }
    # Display remaining conceptual advanced metrics notes
    for metric, note in advanced_metrics_notes.items():
        elements.append(html.P(f"{metric}: {note}"))
    
    return elements
