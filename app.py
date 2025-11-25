from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.responses import HTMLResponse
import sys, os
import json
import logging
import datetime as dt
from fastapi.responses import FileResponse
import tempfile
import os
from fastapi import UploadFile, File

# Add logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(__file__) + "/ncaabFiles/")
from ncaabGamelines import *
from ncaabGetData import get_team_stats, get_player_stats
from ncaabTeam import NcaabTeam
from ncaabEvents import ncaab_events_manager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# COMPREHENSIVE NCAAB TEAMS LIST
NCAAB_TEAMS = [
    "Alabama", "Arizona", "Arkansas", "Auburn", "Baylor", "UCLA", "Connecticut",
    "Duke", "Florida", "Gonzaga", "Houston", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisville", "Marquette", "Maryland", "Memphis",
    "Michigan", "Michigan State", "North Carolina", "NC State", "Ohio State",
    "Oregon", "Purdue", "San Diego State", "Tennessee", "Texas", "Texas A&M",
    "Texas Tech", "Villanova", "Virginia", "West Virginia", "Wisconsin",
    "Xavier", "Creighton", "Syracuse", "Butler", "Georgetown", "St. John's",
    "Providence", "Seton Hall", "DePaul", "Notre Dame", "Wake Forest",
    "Georgia Tech", "Clemson", "Florida State", "Miami", "Virginia Tech",
    "Boston College", "Pittsburgh", "Oklahoma", "Oklahoma State", "Iowa State",
    "Kansas State", "TCU", "West Virginia", "Texas Tech", "Baylor",
    "Colorado", "Utah", "Arizona State", "USC", "Stanford", "California",
    "Washington", "Washington State", "Oregon State", "UCLA", "USC",
    "BYU", "Saint Mary's", "San Francisco", "Santa Clara", "Pepperdine",
    "Loyola Marymount", "Gonzaga", "Saint Louis", "Dayton", "VCU",
    "Richmond", "Davidson", "George Mason", "UMass", "Rhode Island",
    "Saint Joseph's", "La Salle", "Duquesne", "George Washington",
    "Saint Bonaventure", "Fordham", "Nevada", "Utah State", "Boise State",
    "Colorado State", "Wyoming", "Fresno State", "San Jose State",
    "Air Force", "UNLV", "New Mexico", "San Diego State", "Nevada",
    "Buffalo", "Akron", "Kent State", "Ohio", "Miami (OH)", "Bowling Green",
    "Toledo", "Ball State", "Western Michigan", "Eastern Michigan",
    "Central Michigan", "Northern Illinois", "Belmont", "Murray State",
    "Austin Peay", "Tennessee State", "Tennessee Tech", "Eastern Kentucky",
    "Morehead State", "SIU Edwardsville", "UT Martin", "Southeast Missouri",
    "Jacksonville State", "Tennessee State", "Lipscomb", "Liberty",
    "North Florida", "Florida Gulf Coast", "Jacksonville", "Stetson",
    "Kennesaw State", "North Alabama", "UNC Asheville", "Winthrop",
    "Radford", "Campbell", "Gardner-Webb", "Presbyterian", "High Point",
    "Charleston Southern", "Longwood", "UNC Greensboro", "Furman",
    "East Tennessee State", "Mercer", "Chattanooga", "Wofford",
    "Samford", "VMI", "The Citadel", "Western Carolina"
]

# Remove duplicates and sort
NCAAB_TEAMS = sorted(list(set(NCAAB_TEAMS)))

# Years for dropdown
YEARS = [str(year) for year in range(2020, 2026)]  # Extended to 2025

@app.get("/ncaab/gamelines")
def get_lines():
    """Main gamelines endpoint"""
    try:
        manager = GamelineManager()
        db_gamelines = manager.read_gamelines()
        
        if db_gamelines:
            return {"Gamelines": {"manual": db_gamelines}}
        else:
            return {"Gamelines": {"manual": []}}
        
    except Exception as e:
        print(f"Error in /ncaab/gamelines: {e}")
        return {"Gamelines": {"manual": []}}

# ADD THESE NEW ENDPOINTS AFTER YOUR EXISTING ROUTES:

@app.get("/ncaab/debug/db")
def debug_database():
    """Debug endpoint to check database status"""
    try:
        manager = GamelineManager()
        gamelines = manager.read_gamelines()
        
        # Check database file info
        db_info = {
            "db_file": manager.db_file,
            "db_exists": os.path.exists(manager.db_file),
            "total_gamelines": len(gamelines),
            "sources": {}
        }
        
        # Count by source
        for gameline in gamelines:
            source = gameline['source']
            if source not in db_info['sources']:
                db_info['sources'][source] = 0
            db_info['sources'][source] += 1
            
        return db_info
    except Exception as e:
        return {"error": str(e)}


@app.get("/ncaab/gamelines/all")
def get_all_gamelines_detailed():
    """Get all gamelines with detailed info"""
    try:
        manager = GamelineManager()
        gamelines = manager.read_gamelines()
        
        return {
            "total_gamelines": len(gamelines),
            "gamelines": gamelines,
            "sources": list(set(g['source'] for g in gamelines))
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/ncaab/gamelines/manual", response_class=HTMLResponse)
def manual_input_form():
    """Serve HTML form for manual NCAAB gameline input with upcoming events"""
    try:
        # Get upcoming TBD events
        upcoming_events = ncaab_events_manager.get_upcoming_tbd_events(days=7)
        
        # Generate HTML for upcoming events
        upcoming_events_html = ""
        if upcoming_events:
            for event in upcoming_events:
                upcoming_events_html += f"""
                <div class="upcoming-event-card">
                    <div class="event-header">
                        <h4>{event['away_team']} @ {event['home_team']}</h4>
                        <span class="event-date">{event['game_day']} {event.get('start_time', '')}</span>
                    </div>
                    <form action="/ncaab/gamelines/manual/quick" method="post" class="quick-gameline-form">
                        <input type="hidden" name="source" value="manual">
                        <input type="hidden" name="game_day" value="{event['game_day']}">
                        <input type="hidden" name="start_time" value="{event.get('start_time', '')}">
                        <input type="hidden" name="home_team" value="{event['home_team']}">
                        <input type="hidden" name="away_team" value="{event['away_team']}">
                        
                        <div class="quick-odds-row">
                            <div class="odds-group">
                                <label>Home ML:</label>
                                <input type="number" name="home_ml" placeholder="e.g., -150" value="">
                            </div>
                            <div class="odds-group">
                                <label>Away ML:</label>
                                <input type="number" name="away_ml" placeholder="e.g., +130" value="">
                            </div>
                        </div>
                        
                        <div class="quick-odds-row">
                            <div class="odds-group">
                                <label>Home Spread:</label>
                                <input type="number" step="0.5" name="home_spread" placeholder="e.g., -3.5" value="">
                            </div>
                            <div class="odds-group">
                                <label>Home Spread Odds:</label>
                                <input type="number" name="home_spread_odds" placeholder="e.g., -110" value="">
                            </div>
                        </div>
                        
                        <div class="quick-odds-row">
                            <div class="odds-group">
                                <label>Away Spread:</label>
                                <input type="number" step="0.5" name="away_spread" placeholder="e.g., +3.5" value="">
                            </div>
                            <div class="odds-group">
                                <label>Away Spread Odds:</label>
                                <input type="number" name="away_spread_odds" placeholder="e.g., -110" value="">
                            </div>
                        </div>
                        
                        <div class="quick-odds-row">
                            <div class="odds-group">
                                <label>Over/Under:</label>
                                <input type="number" step="0.5" name="over_under" placeholder="e.g., 145.5" value="">
                            </div>
                            <div class="odds-group">
                                <label>Over Odds:</label>
                                <input type="number" name="over_odds" placeholder="e.g., -110" value="">
                            </div>
                            <div class="odds-group">
                                <label>Under Odds:</label>
                                <input type="number" name="under_odds" placeholder="e.g., -110" value="">
                            </div>
                        </div>
                        
                        <button type="submit" class="quick-submit-btn">Add Gameline</button>
                    </form>
                </div>
                """
        else:
            upcoming_events_html = "<p>No upcoming games found. All scheduled games may already have gamelines.</p>"
        
        html_content = f"""
        <html>
        <head>
            <title>NCAAB Manual Gameline Input</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .formGrid {{ display: flex; flex-direction: column; gap: 20px; max-width: 1000px; }}
                .dateTimeRow {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
                .teamRow {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 20px; }}
                .form-group {{ margin-bottom: 15px; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                input, select {{ padding: 8px; width: 100%; box-sizing: border-box; }}
                button {{ padding: 12px 24px; background: #007bff; color: white; border: none; cursor: pointer; font-size: 16px; }}
                button:hover {{ background: #0056b3; }}
                .card {{ border: 1px solid #ddd; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                
                /* Upcoming Events Styles */
                .upcoming-events-section {{ margin-top: 40px; }}
                .upcoming-event-card {{
                    border: 2px solid #e0e0e0;
                    padding: 15px;
                    margin-bottom: 15px;
                    border-radius: 8px;
                    background: #f9f9f9;
                }}
                .event-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 10px;
                }}
                .event-header h4 {{
                    margin: 0;
                    color: #333;
                }}
                .event-date {{
                    color: #666;
                    font-size: 0.9em;
                }}
                .quick-gameline-form {{
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                }}
                .quick-odds-row {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                }}
                .odds-group {{
                    display: flex;
                    flex-direction: column;
                }}
                .odds-group label {{
                    font-size: 0.8em;
                    color: #666;
                    margin-bottom: 2px;
                }}
                .quick-submit-btn {{
                    padding: 8px 16px;
                    background: #28a745;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-top: 10px;
                }}
                .quick-submit-btn:hover {{
                    background: #218838;
                }}
                .section-title {{
                    color: #333;
                    border-bottom: 2px solid #007bff;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <h2>NCAAB Manual Gameline Input</h2>
            
            <!-- Update Events Button -->
            <div style="margin-bottom: 20px;">
                <button onclick="updateEvents()" style="background: #6c757d;">Update Events from Schedule</button>
                <span id="update-status" style="margin-left: 10px;"></span>
            </div>
            
            <!-- Standard Manual Input Form -->
            <div class="card">
                <h3>Custom Gameline Input</h3>
                <form action="/ncaab/gamelines/manual" method="post">
                    <div class="form-group">
                        <label for="source">Source:</label>
                        <select id="source" name="source" required>
                            <option value="manual">Manual</option>
                            <option value="draftkings">DraftKings</option>
                            <option value="fanduel">FanDuel</option>
                            <option value="espn_bets">ESPN Bets</option>
                        </select>
                    </div>

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

                    <div class="card">
                        <h4>Away Team</h4>
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
                        <h4>Home Team</h4>
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
                            <input type="number" step="0.5" id="over_under" name="over_under" placeholder="e.g., 145.5">
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

                    <button type="submit">Submit Custom Gameline</button>
                </form>
            </div>

            <!-- Upcoming Events Section -->
            <div class="upcoming-events-section">
                <h3 class="section-title">Upcoming Games (No Gamelines Yet)</h3>
                <p>Quickly add gamelines to scheduled games:</p>
                {upcoming_events_html}
            </div>

            <script>
                function updateEvents() {{
                    const statusElement = document.getElementById('update-status');
                    statusElement.innerHTML = 'Updating events...';
                    
                    fetch('/ncaab/events/update?days=7&use_gamelines=false')
                        .then(response => response.json())
                        .then(data => {{
                            if (data.status === 'success') {{
                                statusElement.innerHTML = `✅ Updated ${{data.events_updated}} events`;
                                // Reload the page to show new events
                                setTimeout(() => location.reload(), 1000);
                            }} else {{
                                statusElement.innerHTML = '❌ Failed to update events';
                            }}
                        }})
                        .catch(error => {{
                            statusElement.innerHTML = '❌ Error updating events';
                            console.error('Error:', error);
                        }});
                }}
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error generating manual form: {e}")
        return HTMLResponse(content=generate_basic_form())

def generate_basic_form():
    """Generate basic form without events if manager fails"""
    return f"""
    <html>
    <head>
        <title>NCAAB Manual Gameline Input</title>
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
        <h2>NCAAB Manual Gameline Input</h2>
        <form action="/ncaab/gamelines/manual" method="post">
            <div class="form-group">
                <label for="source">Source:</label>
                <select id="source" name="source" required>
                    <option value="manual">Manual</option>
                    <option value="draftkings">DraftKings</option>
                    <option value="fanduel">FanDuel</option>
                    <option value="espn_bets">ESPN Bets</option>
                </select>
            </div>

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

            <div class="card">
                <h4>Away Team</h4>
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
                <h4>Home Team</h4>
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
                    <input type="number" step="0.5" id="over_under" name="over_under" placeholder="e.g., 145.5">
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

            <button type="submit">Submit Custom Gameline</button>
        </form>
    </body>
    </html>
    """

@app.post("/ncaab/gamelines/manual/dumps")
async def bulk_gamelines_dump(request: Request):
    """Bulk dump gamelines from Python list - handles both JSON and Python literal syntax"""
    try:
        # Get the raw request body
        body = await request.body()
        body_text = body.decode('utf-8')
        logger.info(f"Received bulk dump request: {body_text[:200]}...")
        
        gamelines = []
        
        # Try to parse as JSON first
        try:
            data = json.loads(body_text)
            if isinstance(data, list):
                gamelines = data
            elif isinstance(data, dict) and 'gamelines' in data:
                gamelines = data['gamelines']
            else:
                gamelines = [data]  # Single gameline object
        except json.JSONDecodeError:
            # If JSON fails, try to parse as Python literal
            logger.info("JSON parsing failed, trying Python literal parsing")
            try:
                # Clean the text for Python literal parsing
                cleaned_text = body_text.strip()
                
                # Remove variable assignment if present
                if cleaned_text.startswith('gamelines'):
                    cleaned_text = cleaned_text.split('=', 1)[1].strip()
                
                # Handle Python literal syntax
                cleaned_text = cleaned_text.replace("'", '"')
                cleaned_text = cleaned_text.replace('None', 'null')
                cleaned_text = cleaned_text.replace('True', 'true')
                cleaned_text = cleaned_text.replace('False', 'false')
                
                # Parse as JSON
                parsed_data = json.loads(cleaned_text)
                
                if isinstance(parsed_data, list):
                    gamelines = parsed_data
                elif isinstance(parsed_data, dict) and 'gamelines' in parsed_data:
                    gamelines = parsed_data['gamelines']
                else:
                    gamelines = [parsed_data]
                    
            except Exception as parse_error:
                logger.error(f"Python literal parsing failed: {parse_error}")
                raise HTTPException(status_code=400, detail=f"Could not parse gamelines data: {str(parse_error)}")
        
        if not gamelines or not isinstance(gamelines, list):
            logger.error(f"Invalid gamelines format: {type(gamelines)}")
            raise HTTPException(status_code=400, detail="No valid gamelines list provided")
        
        logger.info(f"Parsed {len(gamelines)} gamelines for processing")
        
        manager = GamelineManager()
        success_count = 0
        errors = []
        
        for i, gameline in enumerate(gamelines):
            try:
                # Validate required fields
                if not gameline.get('home_team') or not gameline.get('away_team'):
                    errors.append(f"Gameline {i}: Missing home_team or away_team")
                    continue
                
                game_data = {
                    'home': gameline.get('home_team'),
                    'away': gameline.get('away_team'),
                    'game_day': gameline.get('game_day', str(today)),
                    'start_time': gameline.get('start_time'),
                    'home_ml': gameline.get('home_ml'),
                    'away_ml': gameline.get('away_ml'),
                    'home_spread': gameline.get('home_spread'),
                    'away_spread': gameline.get('away_spread'),
                    'home_spread_odds': gameline.get('home_spread_odds'),
                    'away_spread_odds': gameline.get('away_spread_odds'),
                    'over_under': gameline.get('over_under'),
                    'over_odds': gameline.get('over_odds'),
                    'under_odds': gameline.get('under_odds')
                }
                
                source = gameline.get('source', 'manual_dump')
                manager.update_gameline(source, game_data)
                success_count += 1
                logger.info(f"Successfully processed gameline {i}: {game_data['home']} vs {game_data['away']}")
                
            except Exception as e:
                error_msg = f"Gameline {i}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue
        
        result = {
            "status": "success",
            "message": f"Successfully added {success_count} gamelines to database",
            "gamelines_added": success_count,
            "total_processed": len(gamelines),
            "errors": errors
        }
        
        if errors:
            result["status"] = "partial_success"
            result["message"] = f"Added {success_count} gamelines with {len(errors)} errors"
        
        logger.info(f"Bulk dump completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing bulk gamelines dump: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing bulk gamelines dump: {str(e)}")

@app.post("/ncaab/gamelines/manual/quick")
async def submit_quick_gameline(
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
    """Handle quick gameline submission from upcoming events"""
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
            "message": f"Quick gameline added for {away_team} @ {home_team}",
            "redirect": "/ncaab/gamelines/manual"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting quick gameline: {str(e)}")

# Add events management endpoints
@app.get("/ncaab/events/update")
def update_ncaab_events(days: int = 7, use_gamelines: bool = False):
    """Update NCAAB events with schedule data"""
    try:
        updated_count = ncaab_events_manager.update_events(days, use_gamelines)
        return {
            "status": "success", 
            "sport": "ncaab",
            "events_updated": updated_count,
            "use_gamelines": use_gamelines
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ncaab/events/upcoming")
def get_upcoming_events(days: int = 7):
    """Get upcoming TBD events"""
    try:
        events = ncaab_events_manager.get_upcoming_tbd_events(days)
        return {"sport": "ncaab", "upcoming_events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    """Handle manual NCAAB gameline submission"""
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
            "message": f"NCAAB Gameline for {away_team} @ {home_team} submitted successfully",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting NCAAB gameline: {str(e)}")

@app.get("/ncaab/team-select", response_class=HTMLResponse)
def team_select_form():
    """Serve HTML form for team stats with dropdowns"""
    html_content = f"""
    <html>
    <head>
        <title>NCAAB Team Stats</title>
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
        <h2>NCAAB Team Statistics</h2>
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
                                <p><strong>Field Goal %:</strong> ${{data.summary.field_goal_percentage || 'N/A'}}</p>
                                <p><strong>3-Point %:</strong> ${{data.summary.three_point_percentage || 'N/A'}}</p>
                            </div>`;
                        }}
                        
                        if (data.games && data.games.length > 0) {{
                            html += '<h4>Game Log</h4>';
                            data.games.forEach(game => {{
                                html += `<div class="game-row">
                                    <strong>${{game.Date || 'N/A'}}</strong> vs ${{game.Opp || 'N/A'}}: 
                                    ${{game.Tm || '0'}} - ${{game.Opp2 || '0'}}
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
        
        return {'Team_Stats':results}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ncaab/{team}/{year}")
def get_team_stats_endpoint(team: str, year: str):
    results = get_team_stats_via_form(team, year)
    return {'Team_Stats':results}

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
def get_recent_games(team: str, year: str, games: int):
    """Get recent games data using NcaabTeam class"""
    try:
        ncaab_team = NcaabTeam()
        
        if games == 2:
            success = ncaab_team.last2(team, year)
        elif games == 4:
            success = ncaab_team.last4(team, year)
        elif games == 8:
            success = ncaab_team.last8(team, year)
        else:
            raise HTTPException(status_code=400, detail="Games must be 2, 4, or 8")
        
        if not success:
            raise HTTPException(status_code=404, detail="Could not retrieve recent games")
        
        # Return the recent games data
        recent_data = {
            'scores': ncaab_team.tm if hasattr(ncaab_team, 'tm') else [],
            'opponents': ncaab_team.opp if hasattr(ncaab_team, 'opp') else [],
            'dates': ncaab_team.date if hasattr(ncaab_team, 'date') else []
        }
        
        return recent_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ncaab/scrape/{team}/{year}")
def scrape_team_data(team: str, year: str):
    """Endpoint to manually trigger data scraping"""
    try:
        team_url = team.lower().replace(' ', '-').replace('(', '').replace(')', '')
        success = ncaabdb(team_url, year)
        
        if success:
            return {"status": "success", "message": f"Data scraped for {team} {year}"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to scrape data for {team} {year}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add manual events routes
@app.get("/ncaab/events/manual", response_class=HTMLResponse)
def manual_events_form():
    """Serve HTML form for manual NCAAB events input"""
    html_content = f"""
    <html>
    <head>
        <title>Manual NCAAB Events Input</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .form-container {{ max-width: 800px; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input, select {{ padding: 8px; width: 100%; box-sizing: border-box; }}
            button {{ padding: 12px 24px; background: #007bff; color: white; border: none; cursor: pointer; font-size: 16px; margin-right: 10px; }}
            button:hover {{ background: #0056b3; }}
            .game-row {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; }}
            .add-game-btn {{ background: #28a745; }}
            .add-game-btn:hover {{ background: #218838; }}
            .remove-game-btn {{ background: #dc3545; }}
            .remove-game-btn:hover {{ background: #c82333; }}
        </style>
    </head>
    <body>
        <h2>Manual NCAAB Events Input</h2>
        
        <div class="form-container">
            <form id="eventsForm">
                <div id="gamesContainer">
                    <div class="game-row">
                        <div class="form-group">
                            <label>Game Date:</label>
                            <input type="date" name="game_day" required>
                        </div>
                        <div class="form-group">
                            <label>Start Time:</label>
                            <input type="time" name="start_time">
                        </div>
                        <div class="form-group">
                            <label>Away Team:</label>
                            <select name="away_team" required>
                                <option value="">Select Away Team</option>
                                {"".join([f'<option value="{team}">{team}</option>' for team in NCAAB_TEAMS])}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Home Team:</label>
                            <select name="home_team" required>
                                <option value="">Select Home Team</option>
                                {"".join([f'<option value="{team}">{team}</option>' for team in NCAAB_TEAMS])}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Source:</label>
                            <select name="source">
                                <option value="manual">Manual</option>
                                <option value="schedule">Schedule</option>
                                <option value="espn">ESPN</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <button type="button" class="add-game-btn" onclick="addGameRow()">Add Another Game</button>
                <button type="submit">Submit Events</button>
            </form>
            
            <div id="result" style="margin-top: 20px;"></div>
        </div>

        <script>
            let gameCount = 1;
            
            function addGameRow() {{
                gameCount++;
                const gamesContainer = document.getElementById('gamesContainer');
                const newGameRow = document.createElement('div');
                newGameRow.className = 'game-row';
                newGameRow.innerHTML = `
                    <div class="form-group">
                        <label>Game Date:</label>
                        <input type="date" name="game_day" required>
                    </div>
                    <div class="form-group">
                        <label>Start Time:</label>
                        <input type="time" name="start_time">
                    </div>
                    <div class="form-group">
                        <label>Away Team:</label>
                        <select name="away_team" required>
                            <option value="">Select Away Team</option>
                            {"".join([f'<option value="{team}">{team}</option>' for team in NCAAB_TEAMS])}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Home Team:</label>
                        <select name="home_team" required>
                            <option value="">Select Home Team</option>
                            {"".join([f'<option value="{team}">{team}</option>' for team in NCAAB_TEAMS])}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Source:</label>
                        <select name="source">
                            <option value="manual">Manual</option>
                            <option value="schedule">Schedule</option>
                            <option value="espn">ESPN</option>
                        </select>
                    </div>
                    <button type="button" class="remove-game-btn" onclick="this.parentElement.remove()">Remove Game</button>
                `;
                gamesContainer.appendChild(newGameRow);
            }}
            
            document.getElementById('eventsForm').onsubmit = async function(e) {{
                e.preventDefault();
                
                // Collect all games
                const games = [];
                const gameRows = document.querySelectorAll('.game-row');
                
                gameRows.forEach(row => {{
                    const inputs = row.querySelectorAll('input, select');
                    const gameData = {{}};
                    inputs.forEach(input => {{
                        if (input.name) {{
                            gameData[input.name] = input.value;
                        }}
                    }});
                    games.push(gameData);
                }});
                
                try {{
                    const response = await fetch('/ncaab/events/manual/dumps', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ games: games }})
                    }});
                    
                    const result = await response.json();
                    document.getElementById('result').innerHTML = 
                        `<p style="color: green;">✅ ${{result.message}}</p>`;
                        
                }} catch (error) {{
                    document.getElementById('result').innerHTML = 
                        `<p style="color: red;">❌ Error: ${{error}}</p>`;
                }}
            }};
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/ncaab/events/manual/dumps")
async def bulk_events_dump(data: dict):
    """Bulk dump events from Python list"""
    try:
        games = data.get('games', [])
        if not games:
            raise HTTPException(status_code=400, detail="No games provided")
        
        # Convert to events format and update database
        events = []
        for game in games:
            event = {
                'game_day': game.get('game_day'),
                'start_time': game.get('start_time', 'TBD'),
                'home_team': game.get('home_team'),
                'away_team': game.get('away_team'),
                'home_ml': '---',
                'away_ml': '---',
                'home_spread': '---',
                'away_spread': '---',
                'home_spread_odds': '---',
                'away_spread_odds': '---',
                'over_under': '---',
                'over_odds': '---',
                'under_odds': '---',
                'status': 'TBD',
                'source': game.get('source', 'manual_dump')
            }
            events.append(event)
        
        # Update database
        updated_count = ncaab_events_manager._update_database(events)
        
        return {
            "status": "success",
            "message": f"Successfully added {updated_count} events to database",
            "events_added": updated_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing bulk events dump: {str(e)}")

@app.get("/ncaab/gamelines/manual/dumps", response_class=HTMLResponse)
def gamelines_dump_form():
    """Serve HTML form for bulk gamelines dump"""
    html_content = f"""
    <html>
    <head>
        <title>Bulk NCAAB Gamelines Dump</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .form-container {{ max-width: 1000px; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            textarea {{ width: 100%; height: 300px; padding: 10px; font-family: monospace; }}
            button {{ padding: 12px 24px; background: #007bff; color: white; border: none; cursor: pointer; font-size: 16px; }}
            button:hover {{ background: #0056b3; }}
            .example {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .code {{ font-family: monospace; background: #e9ecef; padding: 10px; }}
        </style>
    </head>
    <body>
        <h2>Bulk NCAAB Gamelines Dump</h2>
        
        <div class="form-container">
            <div class="example">
                <h3>Example Python List Format:</h3>
                <div class="code">
gamelines = [<br>
&nbsp;&nbsp;{{<br>
&nbsp;&nbsp;&nbsp;&nbsp;"source": "draftkings",<br>
&nbsp;&nbsp;&nbsp;&nbsp;"game_day": "2025-02-15",<br>
&nbsp;&nbsp;&nbsp;&nbsp;"start_time": "19:00",<br>
&nbsp;&nbsp;&nbsp;&nbsp;"home_team": "Duke",<br>
&nbsp;&nbsp;&nbsp;&nbsp;"away_team": "North Carolina",<br>
&nbsp;&nbsp;&nbsp;&nbsp;"home_ml": -180,<br>
&nbsp;&nbsp;&nbsp;&nbsp;"away_ml": 160,<br>
&nbsp;&nbsp;&nbsp;&nbsp;"home_spread": -4.5,<br>
&nbsp;&nbsp;&nbsp;&nbsp;"away_spread": 4.5,<br>
&nbsp;&nbsp;&nbsp;&nbsp;"home_spread_odds": -110,<br>
&nbsp;&nbsp;&nbsp;&nbsp;"away_spread_odds": -110,<br>
&nbsp;&nbsp;&nbsp;&nbsp;"over_under": 148.5,<br>
&nbsp;&nbsp;&nbsp;&nbsp;"over_odds": -110,<br>
&nbsp;&nbsp;&nbsp;&nbsp;"under_odds": -110<br>
&nbsp;&nbsp;}}<br>
]
                </div>
            </div>
            
            <form id="gamelinesDumpForm">
                <div class="form-group">
                    <label for="gamelinesData">Paste your Python list of gamelines:</label>
                    <textarea id="gamelinesData" name="gamelines_data" placeholder="Paste your Python list here..."></textarea>
                </div>
                
                <button type="submit">Submit Bulk Gamelines</button>
            </form>
            
            <div id="result" style="margin-top: 20px;"></div>
        </div>

        <script>
            document.getElementById('gamelinesDumpForm').onsubmit = async function(e) {{
                e.preventDefault();
                const gamelinesData = document.getElementById('gamelinesData').value;
                
                if (!gamelinesData.trim()) {{
                    document.getElementById('result').innerHTML = 
                        '<p style="color: red;">❌ Please provide gamelines data</p>';
                    return;
                }}
                
                try {{
                    // Send the raw text as-is, let the backend handle the parsing
                    const response = await fetch('/ncaab/gamelines/manual/dumps', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'text/plain',
                        }},
                        body: gamelinesData
                    }});
                    
                    const result = await response.json();
                    document.getElementById('result').innerHTML = 
                        `<p style="color: green;">✅ ${{result.message}}</p>`;
                        
                }} catch (error) {{
                    document.getElementById('result').innerHTML = 
                        `<p style="color: red;">❌ Error: ${{error}}</p>`;
                }}
            }};
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/ncaab/player-stats", response_class=HTMLResponse)
def player_select_form():
    """Serve HTML form for player stats"""
    html_content = """
    <html>
    <head>
        <title>NCAAB Player Stats</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
        </style>
    </head>
    <body>
        <h2>NCAAB Player Statistics</h2>
        <p>Player stats functionality is available via API.</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/ncaab/gamelines/export")
def export_ncaab_gamelines():
    """Export all NCAAB gamelines to a JSON file"""
    try:
        manager = GamelineManager()
        
        # Export gamelines using the manager method
        export_filepath = manager.export_gamelines()
        
        if not export_filepath:
            raise HTTPException(status_code=404, detail="No gamelines to export")
        
        # Return the file for download
        filename = os.path.basename(export_filepath)
        return FileResponse(
            path=export_filepath,
            media_type='application/json',
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting NCAAB gamelines: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting gamelines: {str(e)}")

@app.post("/ncaab/gamelines/import")
async def import_ncaab_gamelines(file: UploadFile = File(...)):
    """Import NCAAB gamelines from a JSON file"""
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only JSON files are supported")
        
        # Create a temporary file to save the upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            manager = GamelineManager()
            success = manager.import_gamelines(temp_file_path)
            
            if success:
                return {
                    "status": "success",
                    "message": "Gamelines imported successfully",
                    "filename": file.filename
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to import gamelines - invalid file format")
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing NCAAB gamelines: {e}")
        raise HTTPException(status_code=500, detail=f"Error importing gamelines: {str(e)}")

@app.get("/ncaab/gamelines/export/form", response_class=HTMLResponse)
def export_ncaab_gamelines_form():
    """Serve HTML form for exporting and importing NCAAB gamelines"""
    html_content = """
    <html>
    <head>
        <title>NCAAB Gamelines Export/Import</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .form-container { max-width: 800px; }
            .section { 
                border: 1px solid #ddd; 
                padding: 20px; 
                margin-bottom: 30px; 
                border-radius: 5px;
            }
            h2 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
            button { 
                padding: 12px 24px; 
                background: #007bff; 
                color: white; 
                border: none; 
                cursor: pointer; 
                font-size: 16px;
                margin-right: 10px;
                margin-bottom: 10px;
            }
            button:hover { background: #0056b3; }
            .export-btn { background: #28a745; }
            .export-btn:hover { background: #218838; }
            .import-btn { background: #ffc107; color: black; }
            .import-btn:hover { background: #e0a800; }
            .info-box { 
                background: #e7f3ff; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 15px 0;
            }
            .file-info { 
                background: #f8f9fa; 
                padding: 10px; 
                border-radius: 3px; 
                font-family: monospace;
                margin: 10px 0;
            }
            #result { margin-top: 20px; padding: 15px; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        </style>
    </head>
    <body>
        <h1>NCAAB Gamelines Export & Import</h1>
        
        <div class="form-container">
            <!-- Export Section -->
            <div class="section">
                <h2>📤 Export Gamelines</h2>
                <div class="info-box">
                    <p><strong>Export Format:</strong> JSON file with timestamp (ncaab_gamelines_export_YYYYMMDD_HHMM.json)</p>
                    <p><strong>Includes:</strong> All current gamelines with metadata (sport, timestamp, total games)</p>
                </div>
                <button class="export-btn" onclick="exportGamelines()">Export Gamelines</button>
                <button onclick="viewExportFormat()">View Export Format</button>
            </div>

            <!-- Import Section -->
            <div class="section">
                <h2>📥 Import Gamelines</h2>
                <div class="info-box">
                    <p><strong>Supported Format:</strong> JSON export files created by this system</p>
                    <p><strong>Note:</strong> Imported gamelines will be added to the database (duplicates will be updated)</p>
                </div>
                <form id="importForm" enctype="multipart/form-data">
                    <input type="file" id="importFile" name="file" accept=".json" required style="margin-bottom: 15px;">
                    <button type="submit" class="import-btn">Import Gamelines</button>
                </form>
            </div>

            <!-- Result Display -->
            <div id="result"></div>

            <!-- Export Format Preview -->
            <div id="exportFormat" style="display: none; margin-top: 20px;">
                <h3>Export File Format Example:</h3>
                <div class="file-info">
                    {<br>
                    &nbsp;&nbsp;"sport": "ncaab",<br>
                    &nbsp;&nbsp;"export_timestamp": "2024-01-15T14:30:00",<br>
                    &nbsp;&nbsp;"total_games": 25,<br>
                    &nbsp;&nbsp;"gamelines": [<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;{<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"source": "draftkings",<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"game_day": "2024-01-15",<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"start_time": "19:30",<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"home_team": "Duke",<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"away_team": "North Carolina",<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"home_ml": -150,<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"away_ml": 130,<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"home_spread": -3.5,<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"away_spread": 3.5,<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"home_spread_odds": -110,<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"away_spread_odds": -110,<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"over_under": 145.5,<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"over_odds": -110,<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"under_odds": -110<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;}<br>
                    &nbsp;&nbsp;]<br>
                    }
                </div>
            </div>
        </div>

        <script>
            function exportGamelines() {
                // Trigger file download
                window.open('/ncaab/gamelines/export', '_blank');
                
                // Show success message
                showResult('Export started! Your file will download shortly.', 'success');
            }

            function viewExportFormat() {
                const formatDiv = document.getElementById('exportFormat');
                formatDiv.style.display = formatDiv.style.display === 'none' ? 'block' : 'none';
            }

            document.getElementById('importForm').onsubmit = async function(e) {
                e.preventDefault();
                
                const fileInput = document.getElementById('importFile');
                const file = fileInput.files[0];
                
                if (!file) {
                    showResult('Please select a file to import.', 'error');
                    return;
                }

                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch('/ncaab/gamelines/import', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();
                    
                    if (response.ok) {
                        showResult(`✅ ${result.message}`, 'success');
                    } else {
                        showResult(`❌ Error: ${result.detail}`, 'error');
                    }
                    
                    // Clear file input
                    fileInput.value = '';
                    
                } catch (error) {
                    showResult(`❌ Error: ${error}`, 'error');
                }
            };

            function showResult(message, type) {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = message;
                resultDiv.className = type;
                resultDiv.style.display = 'block';
                
                // Scroll to result
                resultDiv.scrollIntoView({ behavior: 'smooth' });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/ncaab/gamelines/export/list")
def list_ncaab_export_files():
    """List all available NCAAB export files"""
    try:
        export_dir = 'exports'
        if not os.path.exists(export_dir):
            return {"exports": [], "message": "No export directory found"}
        
        export_files = []
        for filename in os.listdir(export_dir):
            if filename.startswith('ncaab_gamelines_export_') and filename.endswith('.json'):
                filepath = os.path.join(export_dir, filename)
                file_stats = os.stat(filepath)
                export_files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size_bytes': file_stats.st_size,
                    'created_time': dt.datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    'download_url': f"/ncaab/gamelines/export/file/{filename}"
                })
        
        # Sort by creation time (newest first)
        export_files.sort(key=lambda x: x['created_time'], reverse=True)
        
        return {
            "exports": export_files,
            "total_files": len(export_files)
        }
        
    except Exception as e:
        logger.error(f"Error listing NCAAB export files: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing export files: {str(e)}")

@app.get("/ncaab/gamelines/export/file/{filename}")
def download_ncaab_export_file(filename: str):
    """Download a specific NCAAB export file by filename"""
    try:
        # Security: Validate filename to prevent directory traversal
        if not filename.startswith('ncaab_gamelines_export_') or not filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        filepath = os.path.join('exports', filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Export file not found")
        
        return FileResponse(
            path=filepath,
            media_type='application/json',
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading NCAAB export file: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")                                                                                

@app.get("/ncaab/db-check")
def db_check():
    """Check database status"""
    try:
        from ncaabGamelines import GamelineManager
        manager = GamelineManager()
        gamelines = manager.read_gamelines()
        
        # Check if ncaabDb directory exists and has files
        db_files = []
        if os.path.exists('ncaabDb'):
            db_files = os.listdir('ncaabDb')
        
        return {
            "db_gamelines": gamelines, 
            "count": len(gamelines),
            "ncaabDb_files": db_files,
            "ncaabDb_count": len(db_files)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
