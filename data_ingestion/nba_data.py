# data_fetcher.py
import pandas as pd
from nba_api.stats.static import players
from nba_api.stats.endpoints import playerleaguelog
from datetime import datetime

CURRENT_SEASON = f"{datetime.now().year - 1}-{str(datetime.now().year)[-2:]}" #e.g. 2023-24

def get_active_players_data():
    """
    Fetches basic data and Player Efficiency Rating (PER) for active NBA players
    for the current season.
    """
    print("Fetching active players list...")
    active_players_list = players.get_active_players()
    if not active_players_list:
        print("No active players found. Check NBA API status or season timing.")
        return pd.DataFrame()

    player_data = []
    print(f"Fetching season stats for active players for season: {CURRENT_SEASON}...")
    count = 0
    total_players = len(active_players_list)

    for player in active_players_list:
        player_id = player['id']
        player_name = player['full_name']
        count += 1
        print(f"Fetching data for {player_name} ({count}/{total_players})...")
        try:
            log = playerleaguelog.PlayerLeagueLog(player_id=player_id, season=CURRENT_SEASON)
            player_stats_df = log.get_data_frames()[0]

            if not player_stats_df.empty:
                # We are interested in overall season stats, usually the first row if sorted by date or if only one entry exists
                season_summary = player_stats_df.iloc[0]

                # Calculate PER: (PTS + REB + AST + STL + BLK - Missed FG - Missed FT - TO) / GP
                # This is a simplified PER-like calculation for MVP. Real PER is more complex.
                # For simplicity, we'll use the MIN field from the API if available, often used in PER calculations.
                # The nba_api often doesn't directly provide PER in simple endpoints.
                # We'll fetch available stats and manually note PER is a target for improvement.

                player_info = {
                    'PLAYER_ID': player_id,
                    'PLAYER_NAME': player_name,
                    'TEAM_ABBREVIATION': season_summary.get('TEAM_ABBREVIATION', 'N/A'),
                    'GP': season_summary.get('GP', 0),
                    'MIN': season_summary.get('MIN', 0), # Minutes played
                    'PTS': season_summary.get('PTS', 0),
                    'REB': season_summary.get('REB', 0),
                    'AST': season_summary.get('AST', 0),
                    'STL': season_summary.get('STL', 0),
                    'BLK': season_summary.get('BLK', 0),
                    'FG_PCT': season_summary.get('FG_PCT', 0),
                    'FG3_PCT': season_summary.get('FG3_PCT', 0),
                    'FT_PCT': season_summary.get('FT_PCT', 0),
                    # Placeholder for a more accurate PER.
                    # A true PER calculation requires more detailed stats (Turnovers, Fouls, etc.)
                    # and league averages, which is complex for an MVP from this specific endpoint.
                    # We'll create a simplified efficiency metric for now.
                    'EFF_SCORE': (
                        season_summary.get('PTS', 0) +
                        season_summary.get('REB', 0) +
                        season_summary.get('AST', 0) +
                        season_summary.get('STL', 0) +
                        season_summary.get('BLK', 0)
                    ) / season_summary.get('GP', 1) if season_summary.get('GP', 0) > 0 else 0
                }
                player_data.append(player_info)
            else:
                print(f"No season stats found for {player_name} for {CURRENT_SEASON}.")
        except Exception as e:
            print(f"Could not fetch stats for {player_name} (ID: {player_id}): {e}")

    if not player_data:
        print("No player data could be compiled.")
        return pd.DataFrame()
        
    return pd.DataFrame(player_data)

if __name__ == '__main__':
    # Test the function
    players_df = get_active_players_data()
    if not players_df.empty:
        print("\nSample of fetched player data:")
        print(players_df.head())
        print(f"\nFetched data for {len(players_df)} players.")
    else:
        print("No data fetched.")