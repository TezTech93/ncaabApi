import datetime as dt
import requests
from bs4 import BeautifulSoup
import os
import json
import logging
import time
from random import uniform
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

current_year = dt.datetime.now().year

# Basketball-specific headers
basketball_headers = [
    "Date", "Location", "Opp", "W/L", "Tm", "Opp", "FG", "FGA", "FG%", "3P", "3PA", "3P%", 
    "FT", "FTA", "FT%", "ORB", "TRB", "AST", "STL", "BLK", "TOV", "PF"
]

def get_soup(url):
    """Helper function to fetch and parse HTML"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        # Add respectful delay
        time.sleep(uniform(1, 3))
        content = requests.get(url, headers=headers, timeout=10)
        content.raise_for_status()
        soup = BeautifulSoup(content.content, 'html.parser')
        return soup
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return None

def get_team_stats(team: str, year: int) -> Dict:
    """
    Get NCAAB team stats using Sports Reference (following your working structure)
    """
    try:
        team = team.lower()
        url = f'https://www.sports-reference.com/cbb/schools/{team}/{year}-gamelogs.html'
        
        soup = get_soup(url)
        if not soup:
            return {"error": f"Could not fetch data for {team} {year}"}
        
        body = soup.find('tbody')
        if not body:
            return {"error": f"No data found for {team} {year}"}

        rows = body.find_all('tr')  
        all_data = []
        
        for row in rows:
            cells = row.find_all('td')
            if not cells:
                continue

            # Create data dictionary using your header structure
            data = {
                header: cells[idx].text if len(cells) > idx else None
                for idx, header in enumerate(basketball_headers)
            }
            
            all_data.append(data)

        # Calculate summary stats
        summary = _calculate_basketball_summary(all_data)
        summary['games'] = all_data
        summary['team'] = team
        summary['year'] = year
        
        return summary
        
    except Exception as e:
        logger.error(f"Error in get_team_stats: {e}")
        return {"error": str(e)}

def _calculate_basketball_summary(games: List[Dict]) -> Dict:
    """Calculate basketball summary statistics"""
    try:
        if not games:
            return {}
            
        total_games = len(games)
        wins = 0
        losses = 0
        
        # Basketball stats accumulators
        total_points = 0
        total_points_against = 0
        total_fg_made = 0
        total_fg_attempted = 0
        total_3p_made = 0
        total_3p_attempted = 0
        total_ft_made = 0
        total_ft_attempted = 0
        total_rebounds = 0
        total_assists = 0
        total_turnovers = 0
        
        for game in games:
            try:
                # Win/Loss
                wl = game.get('W/L', '')
                if wl == 'W':
                    wins += 1
                elif wl == 'L':
                    losses += 1
                
                # Points
                points = _safe_int(game.get('Tm'))
                points_against = _safe_int(game.get('Opp'))
                
                total_points += points
                total_points_against += points_against
                
                # Field goals
                fg_made = _safe_int(game.get('FG'))
                fg_attempted = _safe_int(game.get('FGA'))
                total_fg_made += fg_made
                total_fg_attempted += fg_attempted
                
                # 3-pointers
                three_made = _safe_int(game.get('3P'))
                three_attempted = _safe_int(game.get('3PA'))
                total_3p_made += three_made
                total_3p_attempted += three_attempted
                
                # Free throws
                ft_made = _safe_int(game.get('FT'))
                ft_attempted = _safe_int(game.get('FTA'))
                total_ft_made += ft_made
                total_ft_attempted += ft_attempted
                
                # Other stats
                rebounds = _safe_int(game.get('TRB'))
                assists = _safe_int(game.get('AST'))
                turnovers = _safe_int(game.get('TOV'))
                
                total_rebounds += rebounds
                total_assists += assists
                total_turnovers += turnovers
                
            except (ValueError, KeyError) as e:
                logger.debug(f"Error processing basketball game stats: {e}")
                continue
        
        # Calculate percentages and averages
        fg_percentage = (total_fg_made / total_fg_attempted * 100) if total_fg_attempted > 0 else 0
        three_percentage = (total_3p_made / total_3p_attempted * 100) if total_3p_attempted > 0 else 0
        ft_percentage = (total_ft_made / total_ft_attempted * 100) if total_ft_attempted > 0 else 0
        
        return {
            'record': f"{wins}-{losses}",
            'wins': wins,
            'losses': losses,
            'points_per_game': round(total_points / total_games, 1) if total_games > 0 else 0,
            'points_against_per_game': round(total_points_against / total_games, 1) if total_games > 0 else 0,
            'field_goal_percentage': round(fg_percentage, 1),
            'three_point_percentage': round(three_percentage, 1),
            'free_throw_percentage': round(ft_percentage, 1),
            'rebounds_per_game': round(total_rebounds / total_games, 1) if total_games > 0 else 0,
            'assists_per_game': round(total_assists / total_games, 1) if total_games > 0 else 0,
            'turnovers_per_game': round(total_turnovers / total_games, 1) if total_games > 0 else 0,
            'total_games': total_games
        }
        
    except Exception as e:
        logger.error(f"Error calculating basketball summary stats: {e}")
        return {}

def _safe_int(value):
    """Safely convert to int, return 0 if invalid"""
    try:
        if value and str(value).strip().replace('.', '').isdigit():
            return int(float(value))
        return 0
    except (ValueError, TypeError):
        return 0

def ncaabdb(team: str, year: int = current_year) -> bool:
    """
    Scrape NCAAB team stats - maintains compatibility with your existing structure
    """
    try:
        team_url = team.lower().replace(' ', '-').replace('(', '').replace(')', '')
        url = f'https://www.sports-reference.com/cbb/schools/{team_url}/{year}-gamelogs.html'
        
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        body = soup.find('tbody')
        
        if not body:
            logger.warning(f"No data found for {team} {year}")
            return False
            
        # If we found data, consider it successful
        logger.info(f"Successfully found data for {team} {year}")
        return True
        
    except Exception as e:
        logger.error(f"Error in ncaabdb: {e}")
        return False

def get_player_stats(player: str, season: Optional[int] = None) -> Dict:
    """
    Get NCAAB player statistics - placeholder implementation
    """
    try:
        # This would be replaced with actual NCAAB API calls
        return {
            "player": player,
            "season": season or current_year,
            "position": "G",
            "games_played": 30,
            "points_per_game": 18.5,
            "rebounds_per_game": 5.2,
            "assists_per_game": 4.1,
            "field_goal_percentage": "45.8%",
            "three_point_percentage": "38.2%",
            "free_throw_percentage": "85.1%"
        }
    except Exception as e:
        logger.error(f"Error getting NCAAB player stats: {e}")
        return {}

# Test function
def test_scraping():
    """Test the basketball scraping functionality"""
    test_team = "michigan-state"
    test_year = 2024

    print(f"Testing NCAAB stats for {test_team} {test_year}...")
    stats = get_team_stats(test_team, test_year)

    if stats and 'error' not in stats:
        print(f"Successfully loaded data for {test_team}")
        print(f"Record: {stats.get('record', 'N/A')}")
        print(f"PPG: {stats.get('points_per_game', 'N/A')}")
        if stats.get('games'):
            print(f"Sample game: {stats['games'][0]}")
    else:
        print(f"No data found for {test_team} {test_year}")
        print(f"Error: {stats.get('error', 'Unknown error')}")

    print('ncaab stats loaded')

test_scraping()
