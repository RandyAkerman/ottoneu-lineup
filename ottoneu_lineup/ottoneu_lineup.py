import os
import pandas as pd
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
import pickle
from constants import STATS


def main():
    roster = get_roster()
    fangraph_roster = clean_roster(roster)
    performance = scrape_fangraphs(fangraph_roster)
    # standings = get_current_standings()
    # lineup = optimize_lineup()
    return(performance)

def get_roster():

    league_number = os.getenv("LEAGUE_NUMBER")

    url = f"https://ottoneu.fangraphs.com/{league_number}/rosterexport"

    league_roster = pd.read_csv(url)

    team_number = int(os.getenv("TEAM_NUMBER"))
    team_roster = league_roster.loc[(league_roster.TeamID == team_number) & (league_roster['FG MajorLeagueID'].notnull())]

    return(team_roster)

def clean_roster(roster):
    # TODO: Remove players who are not eligible to play
    roster['name_slug'] = roster.Name.str.lower().str.replace(' ', '-', regex=False)
    roster['FG MajorLeagueID'] = roster['FG MajorLeagueID'].astype('int')

    return(roster)

def login_fangraphs(driver):

    url = f"https://blogs.fangraphs.com/wp-login.php?redirect_to=https://www.fangraphs.com/"
    
    driver.get(url)

    account = driver.find_element(By.ID, "user_login")

    account.send_keys(os.getenv("FANGRAPHS_USER"))

    pw = driver.find_element(By.ID, "user_pass")

    pw.send_keys(os.getenv("FANGRAPHS_PASS"))

    driver.find_element(By.ID,"wp-submit").click()

def get_performance(driver, player_slug, player_id):

    url = f"https://www.fangraphs.com/players/{player_slug}/{player_id}"

    driver.get(url)

    try:
        header = driver.find_element(By.XPATH, "//div[@id='daily-projections']/div[3]/div[@class='fg-data-grid undefined with-selected-rows sort-disabled  ']/div[@class='table-wrapper-outer']/div[@class='table-wrapper-inner']/div[@class='table-scroll']/table/thead")
    except NoSuchElementException:
        return dict()
    except WebDriverException:
        return dict()
    else:
        header_labels = header.find_elements(By.TAG_NAME, 'th')

    header_list = [th.text for th in header_labels]

    body = driver.find_element(By.XPATH, "//div[@id='daily-projections']/div[3]/div[@class='fg-data-grid undefined with-selected-rows sort-disabled  ']/div[@class='table-wrapper-outer']/div[@class='table-wrapper-inner']/div[@class='table-scroll']/table/tbody")
    body_values = body.find_elements(By.TAG_NAME, 'td')

    body_list = [td.text for td in body_values]
    
    performance_dict = dict(zip(header_list,body_list))
    player_info = {'player_id': player_id, 'player_slug':player_slug}
    performance_dict.update(player_info)

    return(performance_dict)

def scrape_fangraphs(fangraph_roster):
    service = Service(executable_path=os.getenv("CHROME_PATH"))
    options = Options()
    # options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)

    login_fangraphs(driver)

    performance_dict = [get_performance(driver,y,x) for x,y in zip(fangraph_roster["FG MajorLeagueID"],fangraph_roster["name_slug"])]

    filtered_dict = list(filter(None,performance_dict))
    # TODO: Split between pitchers and batters
    filtered_stats = [{key : val for key, val in sub.items() if key in STATS} for sub in filtered_dict]
    # Hitters: PA	R	HR	OBP	SLG available (R,HR)
    # TODO: Develop OBP and SLG proxy
    # OBP = (Hits + Walks + Hit by Pitch) / (At Bats + Walks + Hit by Pitch + Sacrifice Flies)
    # SLG = (1B + 2Bx2 + 3Bx3 + HRx4)/AB #NOTE: Isn't AB just 1B+2B+3B+HR+SO+BB?
    # Pitchers: IP	K	HR9	ERA	WHIP available (IP,K,HR, BB)
    # TODO: Develop ERA proxy
    # ERA = 9 x earned runs / innings pitched
    # WHIP = adding the number of walks and hits allowed and dividing this sum by the number of innings pitched

    # Split pitchers and batters
    batters = []
    pitchers = []

    for i in range(len(filtered_stats)):
        if 'Pos' in filtered_stats[i].keys():
            batters.append(filtered_stats[i])
        else:
            pitchers.append(filtered_stats[i])

    performance = dict()
    performance['batters'] = batters
    performance['pitchers'] = pitchers
    pickle.dump(performance, open('tmp/performance.pickle', 'wb'))
    return(performance)

if __name__ == '__main__':
    main()
