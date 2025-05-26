# app.py
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc

from data_ingestion.nba_data import get_active_players_data
from analysis.undervalued_metrics import flag_undervalued_players

# --- Data Loading and Preparation ---
print("Starting data loading process for Dash app...")
# For MVP development, load data once on startup.
# For a production app, you might update this periodically or use a database.
try:
    players_df_raw = get_active_players_data()
    if not players_df_raw.empty:
        players_df = flag_undervalued_players(players_df_raw.copy())
        # Sort players for dropdown
        players_df = players_df.sort_values(by='PLAYER_NAME')
        print(f"Data loaded. {len(players_df)} players available.")
    else:
        print("No player data loaded. Dashboard will be empty or show an error.")
        players_df = pd.DataFrame() # Ensure players_df exists
except Exception as e:
    print(f"Error during data loading: {e}")
    players_df = pd.DataFrame() # Ensure players_df exists in case of error

# --- Dash App Initialization ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG]) # Using a dark theme
server = app.server # Expose server for deployment

# --- App Layout ---
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("NBA Player Talent Identification MVP", className="text-center text-primary mb-4"), width=12)),

    dbc.Row([
        dbc.Col([
            html.Label("Select Player:"),
            dcc.Dropdown(
                id='player-dropdown',
                options=[{'label': name, 'value': name} for name in players_df['PLAYER_NAME'].unique()] if not players_df.empty else [],
                value=players_df['PLAYER_NAME'].iloc[0] if not players_df.empty else None,
                clearable=False
            ),
        ], width=6, className="mb-3")
    ]),

    dbc.Row([
        dbc.Col([
            html.H4("Player Information", className="mt-4"),
            html.Div(id='player-info-display')
        ], md=6),
        dbc.Col([
            html.H4("Basic Stats Chart", className="mt-4"),
            dcc.Graph(id='player-stats-chart')
        ], md=6)
    ]),

    dbc.Row([
        dbc.Col([
            html.H4("Player Stats Table", className="mt-4"),
            html.Div(id='player-stats-table-container')
        ], width=12)
    ])
], fluid=True)

# --- Callbacks ---
@app.callback(
    [Output('player-info-display', 'children'),
     Output('player-stats-chart', 'figure'),
     Output('player-stats-table-container', 'children')],
    [Input('player-dropdown', 'value')]
)
def update_player_dashboard(selected_player_name):
    if selected_player_name is None or players_df.empty:
        return "No player selected or no data available.", {}, []

    player_data = players_df[players_df['PLAYER_NAME'] == selected_player_name].iloc[0]

    # Player Info Display
    info_display = html.Ul([
        html.Li(f"Name: {player_data['PLAYER_NAME']}"),
        html.Li(f"Team: {player_data['TEAM_ABBREVIATION']}"),
        html.Li(f"Games Played (GP): {player_data['GP']}"),
        html.Li(f"Minutes (MIN): {player_data['MIN']}"), # Using actual MIN field
        html.Li(f"Simplified EFF_SCORE: {player_data['EFF_SCORE']:.2f}"),
        html.Li(f"MVP Undervalued Flag: {'Yes' if player_data['IS_UNDERVALUED_MVP'] else 'No'}",
                style={'color': 'lightgreen' if player_data['IS_UNDERVALUED_MVP'] else 'lightcoral'})
    ])

    # Player Stats Chart (Simple Bar Chart)
    stats_to_chart = ['PTS', 'REB', 'AST', 'STL', 'BLK']
    # Values need to be numeric for the chart
    chart_data_values = [pd.to_numeric(player_data.get(stat, 0), errors='coerce') for stat in stats_to_chart]
    
    fig = px.bar(
        x=stats_to_chart,
        y=chart_data_values,
        labels={'x': 'Statistic', 'y': 'Value'},
        title=f"Key Stats for {selected_player_name}"
    )
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')


    # Player Stats Table
    player_table_df = player_data.to_frame().reset_index()
    player_table_df.columns = ['Statistic', 'Value']
    
    table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in player_table_df.columns],
        data=player_table_df.to_dict('records'),
        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white', 'fontWeight': 'bold'},
        style_cell={
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'white',
            'textAlign': 'left',
            'padding': '5px'
        },
        style_table={'overflowX': 'auto'}
    )
    table_container = html.Div(table)


    return info_display, fig, table_container

# --- Run the App ---
if __name__ == '__main__':
    if players_df.empty:
        print("WARNING: No player data was loaded. The dashboard might not function correctly.")
        print("Please check 'data_fetcher.py' and your internet connection or NBA API status.")
    app.run_server(debug=True)