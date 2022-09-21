import argparse
import pandas as pd
# import requests
# from bs4 import BeautifulSoup
# from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By  

def main():
    roster = get_roster(league_id, team_id)
    fangraph_roster = clean_roster(roster)
    performance = [get_performance(y,x) for x,y in zip(roster["FG MajorLeagueID"],roster["name_slug"])]
    standings = get_current_standings()
    lineup = optimize_lineup()
    return(lineup)

def get_roster(league_id, team_id):
    url = f"https://ottoneu.fangraphs.com/{league_id}/rosterexport"

    league_roster = pd.read_csv(url)

    team_roster = league_roster.loc[(league_roster.TeamID == team_id) & (league_roster['FG MajorLeagueID'].notnull())]

    return(team_roster)

def clean_roster(roster):
    roster['name_slug'] = roster.Name.str.lower().str.replace(' ', '-', regex=False)
    roster['FG MajorLeagueID'] = roster['FG MajorLeagueID'].astype('int')

    return(roster)

def get_performance(player_slug, player_id):

    service = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service)

    url = f"https://www.fangraphs.com/players/{player_slug}/{player_id}"

    driver.get(url)

    header = driver.find_element(By.XPATH, "//div[@id='daily-projections']/div[3]/div[@class='fg-data-grid undefined with-selected-rows sort-disabled  ']/div[@class='table-wrapper-outer']/div[@class='table-wrapper-inner']/div[@class='table-scroll']/table/thead")
    header_labels = header.find_elements(By.TAG_NAME, 'th')

    header_list = [th.text for th in header_labels]

    body = driver.find_element(By.XPATH, "//div[@id='daily-projections']/div[3]/div[@class='fg-data-grid undefined with-selected-rows sort-disabled  ']/div[@class='table-wrapper-outer']/div[@class='table-wrapper-inner']/div[@class='table-scroll']/table/tbody")
    body_values = body.find_elements(By.TAG_NAME, 'td')

    body_list = [td.text for td in body_values]

    performance_dict = dict(zip(header_list,body_list))

    return(performance_dict)

def get_current_standings():
    # need to determine what scoring categories team needs the most help with
    return(standings)

def optimize_lineup():
    # based on the players available, their likely performance and the team scoring needs return the best lineup
    return(lineup_dict)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--league_id',
        required=True,
        type=str,
        help='League id'
    )

    parser.add_argument(
        '--team_id',
        required=True,
        type=str,
        help='team id'
    )

    args = parser.parse_args()

    main(args.date)
