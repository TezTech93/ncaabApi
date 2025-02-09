import requests
import bs4
from bs4 import BeautifulSoup

url3 = 'https://sportsbook.draftkings.com/leagues/basketball/ncaab'

def current_gamelines(url):
    a = 0
    all_gamelines = []
    content = requests.get(url)
    soup = BeautifulSoup(content.content, 'html.parser')
    table = soup.find('table')
    if table:
        print('table found')
    else:
        try:
            data = soup.find_all('td')
            if data:
                print(data)
            else:
                print('this shit tweaking')
        except Exception as e:   
            print(e)
        print('error fetching data')
    tr_data = table.find_all('tr')
    print(len(tr_data))
    gameline = []

    for data in tr_data:
        for i in data:
            a += 1
            if a > 4:
                gameline.append(i.text)
                if len(gameline) == 8:
                    hSpread = gameline[1][:-4]
                    hSpreadOdds = gameline[1][-4:]
                    aSpread = gameline[5][:-4]
                    aSpreadOdds = gameline[5][-4:]
                    ovSpread = gameline[2][:-4].replace('\xa0', '')
                    ovSpreadOdds = gameline[2][-4:]
                    unSpread = gameline[6][:-4].replace('\xa0', '')
                    unSpreadOdds = gameline[6][-4:]
                    my_dict = {
                    'home': gameline[0],'away':gameline[4],
                    'home_ml':gameline[3],'away_ml':gameline[7], 
                    'home_spread':hSpread,'away_spread':aSpread,
                    'home_spread_odds': hSpreadOdds, 'away_spread_odds': aSpreadOdds,
                    'over':ovSpread,'under':unSpread,
                    'over_odds': ovSpreadOdds, 'under_odds': unSpreadOdds}
                    all_gamelines.append(my_dict)
                    gameline = []
                    print(a)

    print(all_gamelines)
    return all_gamelines

ncaab_game_lines = current_gamelines(url3)