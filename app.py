import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

# 1. Define app and server
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

# 2. Now import tab modules that might need to import 'app'
from dashboard import tab_overview
from dashboard import tab_stats
from dashboard import tab_shooting
from dashboard import tab_playstyle
from dashboard import tab_comparisons

# App Layout
app.layout = html.Div([
    html.H1("NBA Player Analysis Dashboard", style={'textAlign': 'center', 'marginBottom': '20px'}),
    dcc.Tabs(id='main-tabs', value='tab-overview', children=[
        dcc.Tab(label='Overview & Summary', value='tab-overview'),
        dcc.Tab(label='Traditional & Advanced Stats', value='tab-stats'),
        dcc.Tab(label='Shooting Analysis', value='tab-shooting'),
        dcc.Tab(label='Playstyle/Role Metrics', value='tab-playstyle'),
        dcc.Tab(label='Comparisons', value='tab-comparisons'),
    ]),
    html.Div(id='tab-content', style={'marginTop': '20px'})
])

# Callback to render tab content
@app.callback(
    Output('tab-content', 'children'),
    Input('main-tabs', 'value')
)
def render_tab_content(tab_value):
    if tab_value == 'tab-overview':
        if hasattr(tab_overview, 'layout'):
            return tab_overview.layout
        else:
            return html.P(f"Content for Overview & Summary (tab-overview) coming soon!")
    elif tab_value == 'tab-stats':
        if hasattr(tab_stats, 'layout'):
            return tab_stats.layout
        else:
            return html.P(f"Content for Traditional & Advanced Stats (tab-stats) coming soon!")
    elif tab_value == 'tab-shooting':
        if hasattr(tab_shooting, 'layout'):
            return tab_shooting.layout
        else:
            return html.P(f"Content for Shooting Analysis (tab-shooting) coming soon!")
    elif tab_value == 'tab-playstyle':
        if hasattr(tab_playstyle, 'layout'):
            return tab_playstyle.layout
        else:
            return html.P(f"Content for Playstyle/Role Metrics (tab-playstyle) coming soon!")
    elif tab_value == 'tab-comparisons':
        if hasattr(tab_comparisons, 'layout'):
            return tab_comparisons.layout
        else:
            return html.P(f"Content for Comparisons (tab-comparisons) coming soon!")
    return html.P("Select a tab to view its content.") # Default fallback

if __name__ == '__main__':
    app.run_server(debug=True)
