# analysis.py
import pandas as pd

def flag_undervalued_players(players_df):
    """
    Flags players based on a simple 'undervalued' logic.
    For MVP: Player has an EFF_SCORE above the median.
    (This is a placeholder for more sophisticated analysis).
    """
    if 'EFF_SCORE' not in players_df.columns or players_df.empty:
        players_df['IS_UNDERVALUED_MVP'] = False
        return players_df

    median_eff_score = players_df['EFF_SCORE'].median()
    print(f"Median EFF_SCORE for flagging: {median_eff_score}")
    
    players_df['IS_UNDERVALUED_MVP'] = players_df['EFF_SCORE'] > median_eff_score
    return players_df

if __name__ == '__main__':
    # Test the function with dummy data
    dummy_data = {
        'PLAYER_NAME': ['Player A', 'Player B', 'Player C', 'Player D'],
        'EFF_SCORE': [10, 25, 15, 30]
    }
    dummy_df = pd.DataFrame(dummy_data)
    analyzed_df = flag_undervalued_players(dummy_df.copy())
    print("\nSample of analyzed player data:")
    print(analyzed_df)