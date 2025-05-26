# data_fetcher.py
import pandas as pd
from nba_api.stats.static import players
import json
import os
from nba_api.stats.endpoints import playerleaguelog
from datetime import datetime

CURRENT_SEASON = f"{datetime.now().year - 1}-{str(datetime.now().year)[-2:]}" #e.g. 2023-24

CACHE_DIR = "data_ingestion/cache"
ACTIVE_PLAYERS_CACHE_PATH = os.path.join(CACHE_DIR, "active_players.json")

def get_active_players_data():
    """
    Fetches basic data and Player Efficiency Rating (PER) for active NBA players
    for the current season.
    """
    active_players_list = None
    # Try to load from cache first
    if os.path.exists(ACTIVE_PLAYERS_CACHE_PATH):
        try:
            with open(ACTIVE_PLAYERS_CACHE_PATH, 'r') as f:
                active_players_list = json.load(f)
            print("Loading active players list from cache...")
        except (IOError, json.JSONDecodeError) as e:
            print(f"Failed to load active players from cache ({e}), fetching from API...")
            active_players_list = None # Ensure it's reset if loading failed
    else:
        print("Cache not found for active players list, fetching from API...")

    if active_players_list is None: # If cache miss or loading failed
        print("Fetching active players list from API...")
        active_players_list = players.get_active_players()

        if active_players_list: # If API call was successful and returned data
            try:
                if not os.path.exists(CACHE_DIR):
                    os.makedirs(CACHE_DIR) # Should already exist from previous subtask, but good practice
                print("Saving active players list to cache...")
                with open(ACTIVE_PLAYERS_CACHE_PATH, 'w') as f:
                    json.dump(active_players_list, f, indent=4)
            except IOError as e:
                print(f"Failed to save active players list to cache: {e}")
        else: # API call itself returned no data
            print("No active players found from API. Cache will not be updated.")


    if not active_players_list:
        print("No active players found. Check NBA API status or season timing (or cache was empty/corrupt).")
        return pd.DataFrame()

    player_data = []
    print(f"Fetching season stats for active players for season: {CURRENT_SEASON}...")
    count = 0
    total_players = len(active_players_list)

    for player in active_players_list:
        player_id = player['id']
        player_name = player['full_name']
        count += 1
        # Overall fetching message is fine, cache messages will be more specific
        print(f"Processing data for {player_name} ({count}/{total_players})...")

        player_stats_df = None
        player_log_cache_path = os.path.join(CACHE_DIR, f"player_{player_id}_{CURRENT_SEASON}_log.json")

        if os.path.exists(player_log_cache_path):
            try:
                player_stats_df = pd.read_json(player_log_cache_path, orient='split')
                print(f"Loading season stats for {player_name} from cache...")
            except Exception as e: # Catching a broad exception for any parsing/IO issues
                print(f"Failed to load stats for {player_name} from cache ({e}), fetching from API...")
                player_stats_df = None # Ensure it's reset
        else:
            print(f"Cache not found for {player_name} season stats, fetching from API...")

        try:
            if player_stats_df is None: # If cache miss or failed to load
                print(f"Fetching season stats for {player_name} from API...")
                log = playerleaguelog.PlayerLeagueLog(player_id=player_id, season=CURRENT_SEASON)
                # Intentionally get all dataframes to see if there's an issue with index 0 for some players
                all_dfs = log.get_data_frames()
                if all_dfs and len(all_dfs) > 0:
                    player_stats_df = all_dfs[0]
                    # Save to cache if API call was made and data is not empty
                    if not player_stats_df.empty:
                        try:
                            print(f"Saving season stats for {player_name} to cache...")
                            player_stats_df.to_json(player_log_cache_path, orient='split')
                        except IOError as e:
                            print(f"Failed to save stats for {player_name} to cache: {e}")
                    else: # API returned empty df
                        print(f"No season stats found for {player_name} from API for {CURRENT_SEASON}. Cache not updated.")
                else: # API returned no dataframes
                    print(f"No dataframes returned by API for {player_name} for {CURRENT_SEASON}.")
                    player_stats_df = pd.DataFrame() # Ensure it's an empty DataFrame

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
            # This else is now for when player_stats_df (from cache or API) is empty
            else:
                # Avoid duplicating "No season stats found" if API already said so and player_stats_df is empty
                if player_stats_df is not None and not player_stats_df.empty: # Redundant check, but for safety
                     print(f"No season stats found for {player_name} for {CURRENT_SEASON} (after cache/API).")
        except Exception as e:
            # This exception is for unexpected errors during the API call or subsequent processing
            print(f"Error processing stats for {player_name} (ID: {player_id}): {e}")
            # Ensure player_stats_df is an empty DataFrame to prevent errors in player_info creation
            player_stats_df = pd.DataFrame()


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