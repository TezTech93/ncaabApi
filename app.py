from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware 
import sys, os
sys.path.append(os.path.dirname((__file__)) + "/ncaabFiles/")
import asyncio
from ncaabGamelines import *
from ncaabGetData import *

gameline_url = 'https://sportsbook.draftkings.com/leagues/basketball/ncaab'

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ncaab/gamelines")
async def get_lines():
    print('starting')
    print('printed')
    try:
        await asyncio.sleep(1)
        lines = current_gamelines(gameline_url)
        if not lines:
            raise HTTPException(status_code=404, detail="No gamelines found")
        return {"Gamelines":lines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))                      

@app.get("/ncaab/{team}/{year}")
def get_stats(team,year):
    try:
        results = get_team_stats(team, year)
        print(results)
        if not results:
            raise HTTPException(status_code=404, detail="No stats found for the given team and year")
        return {"Team_Stats": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ncaab/{player}/")
def get_player_stats(range):
    return 1

@app.get("/ncaab/{coach}/")
def get_coach_stats(range):
    return 1