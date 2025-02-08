import datetime as dt
import requests
from bs4 import BeautifulSoup

now = dt.datetime.now()
today = f'{now.month},{now.day},{now.year}'

off_headers = [
    "G", "Date", 'Location',"Opp", "W/L", "Tm", "Opp", "FG", "FGA", "FG%", "3P", "3PA", "3P%", 
    "FT", "FTA", "FT%", "ORB", "TRB", "AST", "STL", "BLK", "TOV", "PF", 
    "FG", "FGA", "FG%", "3P", "3PA", "3P%", "FT", "FTA", "FT%", "ORB", "TRB", "AST", "STL", "BLK", "TOV", "PF"
]

def get_team_stats(team,year):
    url = f'https://www.sports-reference.com/cbb/schools/{team}/{year}-gamelogs.html'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    body = soup.find('tbody')
    rows = body.find_all('tr')  

    all_data = []
    for row in rows:
        cells = row.find_all('td')
        if not cells:
            continue

        data = {
        header: cells[idx].text if len(cells) > idx else None
        for idx, header in enumerate(off_headers)
    }
        
        all_data.append(data)

    print(type(all_data))
    try:
        return all_data
    except Exception as e:
        return e



def get_player_stats(player,year):
    fname_lname = player.split(' ')
    fname = fname_lname[0]
    lname = fname_lname[1]
    letter = lname[0].lower()
    print(letter)
    player_id = lname[0:5] + fname[0:2] +'01'
    player_id = player_id.lower()
    print(player_id)
    #url = 'https://www.basketball-reference.com/players/{letter}/{player_id}/gamelog/{year}'
    #response = requests.get(url)
    #soup = BeautifulSoup(response.text, 'html.parser')
    #rows = soup.find_all('tr')

    #for row in rows:
        #print(row)

def get_coach_stats(coach):
    pass

get_team_stats("michigan-state",'2024')