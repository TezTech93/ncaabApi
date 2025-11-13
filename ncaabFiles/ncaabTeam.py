import datetime as dt
import sqlite3
import pandas as pd
import os

dirname = os.path.dirname(__file__)

now = dt.datetime.now()
todays_date = dt.date(now.year, now.month, now.day)

class NcaabTeam:
    w = 0
    l = 0
    
    def __init__(self, Name='', **kwargs):
        self.name = Name
        # Initialize all stats attributes
        stats_attrs = [
            'Date', 'Opponent', 'Result', 'Tm', 'Opp', 'FGM', 'FGA', 'FG_Pct',
            'ThreePM', 'ThreePA', 'ThreeP_Pct', 'FTM', 'FTA', 'FT_Pct', 'ORB',
            'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'Opp_FGM', 'Opp_FGA',
            'Opp_FG_Pct', 'Opp_ThreePM', 'Opp_ThreePA', 'Opp_ThreeP_Pct'
        ]
        
        for attr in stats_attrs:
            setattr(self, attr.lower(), '')
            
        # Set attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key.lower()):
                setattr(self, key.lower(), value)

    def get_stats(self, team, year):
        """Get all stats for a team"""
        self.w = 0
        self.l = 0
        filename = os.path.join(dirname, f'ncaabDb/{team}-{year}-stats.db')
        
        if not os.path.exists(filename):
            print(f"Database file not found: {filename}")
            return None
            
        conn = sqlite3.connect(filename)
        cur = conn.cursor()
        
        try:
            cur.execute('SELECT * FROM Stats')
            rows = cur.fetchall()
            conn.close()
            
            if not rows:
                return None
                
            return rows
            
        except Exception as e:
            print(f"Error reading stats: {e}")
            conn.close()
            return None

    def last2(self, team, year):
        """Get last 2 games stats"""
        return self._get_recent_games(team, year, 2)
    
    def last4(self, team, year):
        """Get last 4 games stats"""
        return self._get_recent_games(team, year, 4)
    
    def last8(self, team, year):
        """Get last 8 games stats"""
        return self._get_recent_games(team, year, 8)

    def _get_recent_games(self, team, year, num_games):
        """Helper method to get recent games"""
        self.w = 0
        self.l = 0
        
        filename = os.path.join(dirname, f'ncaabDb/{team}-{year}-stats.db')
        
        if not os.path.exists(filename):
            print(f"Database file not found: {filename}")
            return False
            
        conn = sqlite3.connect(filename)
        
        try:
            # Read data into pandas DataFrame
            query = "SELECT * FROM Stats"
            team_stats = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(team_stats) < num_games:
                print(f"Not enough games found. Have {len(team_stats)}, need {num_games}")
                return False
            
            # Define column names based on database structure
            columns = [
                'Date', 'Opponent', 'Result', 'Tm', 'Opp', 'FGM', 'FGA', 'FG_Pct',
                'ThreePM', 'ThreePA', 'ThreeP_Pct', 'FTM', 'FTA', 'FT_Pct', 'ORB',
                'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'Opp_FGM', 'Opp_FGA',
                'Opp_FG_Pct', 'Opp_ThreePM', 'Opp_ThreePA', 'Opp_ThreeP_Pct'
            ]
            
            team_stats.columns = columns
            
            # Get recent games
            recent_games = team_stats.tail(num_games)
            
            # Set attributes for recent games
            for col in columns:
                setattr(self, col.lower(), recent_games[col].tolist())
            
            return True
            
        except Exception as e:
            print(f"Error getting recent games: {e}")
            conn.close()
            return False

    def calculate_win_loss(self, team, year):
        """Calculate win-loss record from database"""
        filename = os.path.join(dirname, f'ncaabDb/{team}-{year}-stats.db')
        
        if not os.path.exists(filename):
            return 0, 0
            
        conn = sqlite3.connect(filename)
        
        try:
            team_stats = pd.read_sql_query("SELECT * FROM Stats", conn)
            conn.close()
            
            wins = 0
            losses = 0
            
            for _, game in team_stats.iterrows():
                result = str(game.get('Result', ''))
                if 'W' in result:
                    wins += 1
                elif 'L' in result:
                    losses += 1
            
            self.w = wins
            self.l = losses
            return wins, losses
            
        except Exception as e:
            print(f"Error calculating win-loss: {e}")
            return 0, 0

# Create instance
ncaab_team = NcaabTeam()
