from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.responses import HTMLResponse
import sys, os

sys.path.append(os.path.dirname(__file__) + "/ncaabFiles/")
from ncaabGamelines import *  # This imports your existing gameline structure
from ncaabGetData import get_team_stats, get_player_stats, ncaabdb
from ncaabTeam import NcaabTeam

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NCAA Basketball Teams
NCAAB_TEAMS = [
    "Alabama", "Arizona", "Arkansas", "Auburn", "Baylor", "Butler", "BYU",
    "Cincinnati", "Clemson", "Connecticut", "Creighton", "Duke", "Florida",
    "Florida State", "Gonzaga", "Houston", "Illinois", "Indiana", "Iowa",
    "Iowa State", "Kansas", "Kansas State", "Kentucky", "Louisville", "Marquette",
    "Maryland", "Memphis", "Miami (FL)", "Michigan", "Michigan State", "Minnesota",
    "Mississippi State", "Missouri", "North Carolina", "NC State", "Notre Dame",
    "Ohio State", "Oklahoma", "Oklahoma State", "Oregon", "Penn State", "Pittsburgh",
    "Purdue", "San Diego State", "Seton Hall", "St. John's", "Syracuse", "TCU",
    "Tennessee", "Texas", "Texas A&M", "Texas Tech", "UCLA", "USC", "Villanova",
    "Virginia", "Virginia Tech", "Wake Forest", "Washington", "West Virginia",
    "Wisconsin", "Xavier"
]

# Years for dropdown
YEARS = [str(year) for year in range(2020, 2025)]

# Your existing gameline endpoints (unchanged)
@app.get("/ncaab/gamelines")
def get_lines():
    """Main gamelines endpoint for NCAA Basketball"""
    try:
        manager = GamelineManager()
        db_gamelines = manager.read_gamelines()
        
        if db_gamelines:
            return {"Gamelines": db_gamelines}
        else:
            return {"Gamelines": ncaab_game_lines}
        
    except Exception as e:
        print(f"Error in /ncaab/gamelines: {e}")
        return {"Gamelines": {"manual": {}}}

@app.get("/ncaab/gamelines/manual", response_class=HTMLResponse)
def manual_input_form():
    """Serve HTML form for manual NCAA Basketball gameline input"""
    html_content = f"""
    <html>
    <head>
        <title>NCAA Basketball Manual Gameline Input</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .formGrid {{ display: flex; flex-direction: column; gap: 20px; max-width: 800px; }}
            .dateTimeRow {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .teamRow {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 20px; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input, select {{ padding: 8px; width: 100%; box-sizing: border-box; }}
            button {{ padding: 12px 24px; background: #007bff; color: white; border: none; cursor: pointer; font-size: 16px; }}
            button:hover {{ background: #0056b3; }}
            .card {{ border: 1px solid #ddd; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h2>NCAA Basketball Manual Gameline Input</h2>
        <form action="/ncaab/gamelines/manual" method="post">
            <div class="card">
                <div class="form-group">
                    <label for="source">Source:</label>
                    <select id="source" name="source" required>
                        <option value="manual">Manual</option>
                        <option value="draftkings">DraftKings</option>
                        <option value="fanduel">FanDuel</option>
                        <option value="espn_bets">ESPN Bets</option>
                    </select>
                </div>
            </div>

            <div class="card">
                <div class="dateTimeRow">
                    <div class="form-group">
                        <label for="game_day">Game Date:</label>
                        <input type="date" id="game_day" name="game_day" required>
                    </div>
                    <div class="form-group">
                        <label for="start_time">Start Time:</label>
                        <input type="time" id="start_time" name="start_time">
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>Away Team</h3>
                <div class="teamRow">
                    <div class="form-group">
                        <label for="away_team">Away Team:</label>
                        <select id="away_team" name="away_team" required>
                            <option value="">Select Away Team</option>
                            {"".join([f'<option value="{team}">{team}</option>' for team in NCAAB_TEAMS])}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="away_ml">Away ML:</label>
                        <input type="number" id="away_ml" name="away_ml" placeholder="e.g., +150">
                    </div>
                    <div class="form-group">
                        <label for="away_spread">Away Spread:</label>
                        <input type="number" step="0.5" id="away_spread" name="away_spread" placeholder="e.g., +7.5">
                    </div>
                    <div class="form-group">
                        <label for="away_spread_odds">Spread Odds:</label>
                        <input type="number" id="away_spread_odds" name="away_spread_odds" placeholder="e.g., -110">
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>Home Team</h3>
                <div class="teamRow">
                    <div class="form-group">
                        <label for="home_team">Home Team:</label>
                        <select id="home_team" name="home_team" required>
                            <option value="">Select Home Team</option>
                            {"".join([f'<option value="{team}">{team}</option>' for team in NCAAB_TEAMS])}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="home_ml">Home ML:</label>
                        <input type="number" id="home_ml" name="home_ml" placeholder="e.g., -170">
                    </div>
                    <div class="form-group">
                        <label for="home_spread">Home Spread:</label>
                        <input type="number" step="0.5" id="home_spread" name="home_spread" placeholder="e.g., -7.5">
                    </div>
                    <div class="form-group">
                        <label for="home_spread_odds">Spread Odds:</label>
                        <input type="number" id="home_spread_odds" name="home_spread_odds" placeholder="e.g., -110">
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="form-group">
                    <label for="over_under">Over/Under:</label>
                    <input type="number" step="0.5" id="over_under" name="over_under" placeholder="e.g., 148.5">
                </div>
                <div class="form-group">
                    <label for="over_odds">Over Odds:</label>
                    <input type="number" id="over_odds" name="over_odds" placeholder="e.g., -110">
                </div>
                <div class="form-group">
                    <label for="under_odds">Under Odds:</label>
                    <input type="number" id="under_odds" name="under_odds" placeholder="e.g., -110">
                </div>
            </div>

            <button type="submit">Submit NCAA Basketball Gameline</button>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/ncaab/gamelines/manual")
async def submit_manual_gameline(
    source: str = Form(...),
    home_team: str = Form(...),
    away_team: str = Form(...),
    game_day: str = Form(...),
    start_time: str = Form(None),
    home_ml: int = Form(None),
    away_ml: int = Form(None),
    home_spread: float = Form(None),
    away_spread: float = Form(None),
    home_spread_odds: int = Form(None),
    away_spread_odds: int = Form(None),
    over_under: float = Form(None),
    over_odds: int = Form(None),
    under_odds: int = Form(None)
):
    """Handle manual NCAA Basketball gameline submission"""
    try:
        game_data = {
            'home': home_team,
            'away': away_team,
            'game_day': game_day,
            'start_time': start_time,
            'home_ml': home_ml,
            'away_ml': away_ml,
            'home_spread': home_spread,
            'away_spread': away_spread,
            'home_spread_odds': home_spread_odds,
            'away_spread_odds': away_spread_odds,
            'over_under': over_under,
            'over_odds': over_odds,
            'under_odds': under_odds
        }

        manager = GamelineManager()
        manager.update_gameline(source, game_data)
        
        return {
            "status": "success",
            "message": f"NCAA Basketball Gameline for {away_team} @ {home_team} submitted successfully",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting NCAA Basketball gameline: {str(e)}")

# NEW: Team stats endpoints
@app.get("/ncaab/team-select", response_class=HTMLResponse)
def team_select_form():
    """Serve HTML form for team stats with dropdowns"""
    html_content = f"""
    <html>
    <head>
        <title>NCAA Basketball Team Stats</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            select, button {{ padding: 10px; font-size: 16px; }}
            button {{ background: #007bff; color: white; border: none; cursor: pointer; }}
            button:hover {{ background: #0056b3; }}
            .stats-card {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .game-row {{ border-bottom: 1px solid #eee; padding: 8px 0; }}
        </style>
    </head>
    <body>
        <h2>NCAA Basketball Team Statistics</h2>
        <form action="/ncaab/team-stats" method="get" id="teamForm">
            <div class="form-group">
                <label for="team">Team:</label>
                <select id="team" name="team" required>
                    <option value="">Select Team</option>
                    {"".join([f'<option value="{team}">{team}</option>' for team in NCAAB_TEAMS])}
                </select>
            </div>
            <div class="form-group">
                <label for="year">Year:</label>
                <select id="year" name="year" required>
                    <option value="">Select Year</option>
                    {"".join([f'<option value="{year}">{year}</option>' for year in YEARS])}
                </select>
            </div>
            <button type="submit">Get Team Stats</button>
        </form>
        <div id="results"></div>
        
        <script>
            document.getElementById('teamForm').onsubmit = async function(e) {{
                e.preventDefault();
                const team = document.getElementById('team').value;
                const year = document.getElementById('year').value;
                
                if (team && year) {{
                    try {{
                        const response = await fetch(`/ncaab/team-stats?team=${{encodeURIComponent(team)}}&year=${{year}}`);
                        const data = await response.json();
                        
                        let html = '<h3>Team Statistics:</h3>';
                        
                        if (data.summary) {{
                            html += `<div class="stats-card">
                                <h4>Season Summary</h4>
                                <p><strong>Record:</strong> ${{data.summary.record || 'N/A'}}</p>
                                <p><strong>Points Per Game:</strong> ${{data.summary.points_per_game || 'N/A'}}</p>
                                <p><strong>Points Against Per Game:</strong> ${{data.summary.points_against_per_game || 'N/A'}}</p>
                                <p><strong>FG Percentage:</strong> ${{data.summary.fg_percentage || 'N/A'}}%</p>
                                <p><strong>3-Pointers Per Game:</strong> ${{data.summary.threes_per_game || 'N/A'}}</p>
                            </div>`;
                        }}
                        
                        if (data.games && data.games.length > 0) {{
                            html += '<h4>Game Log</h4>';
                            data.games.forEach(game => {{
                                html += `<div class="game-row">
                                    <strong>${{game.Date || 'N/A'}}</strong> vs ${{game.Opponent || 'N/A'}}: 
                                    ${{game.Tm || '0'}} - ${{game.Opp || '0'}} (${{game.Result || 'N/A'}})
                                </div>`;
                            }});
                        }}
                        
                        document.getElementById('results').innerHTML = html;
                    }} catch (error) {{
                        document.getElementById('results').innerHTML = 
                            '<p style="color: red;">Error fetching data: ' + error + '</p>';
                    }}
                }}
            }};
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/ncaab/team-stats")
def get_team_stats_via_form(team: str, year: str):
    """Get team stats via form parameters"""
    try:
        print(f"Fetching stats for {team} in {year}")
        results = get_team_stats(team, year)
        
        if not results or "error" in results:
            # Try to scrape data first
            team_url = team.lower().replace(' ', '-').replace('(', '').replace(')', '')
            if ncaabdb(team_url, year):
                results = get_team_stats(team, year)
            else:
                raise HTTPException(status_code=404, detail=f"Could not retrieve stats for {team} {year}")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ncaab/{team}/{year}")
def get_team_stats_endpoint(team: str, year: str):
    """Team stats endpoint - maintained for compatibility"""
    return get_team_stats_via_form(team, year)

@app.get("/ncaab/player-stats")
def get_player_stats_endpoint(player: str, season: str = None):
    """Get player stats"""
    try:
        results = get_player_stats(player, season)
        if not results:
            raise HTTPException(status_code=404, detail="Player stats not found")
        return {"Player_Stats": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ncaab/team/recent/{team}/{year}/{games}")
def get_recent_games(team
