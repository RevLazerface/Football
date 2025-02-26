import requests
from bs4 import BeautifulSoup
import csv
import time

def main():
    # NOTE Time stuff is just for experimenting
    start = time.time()

    # Define the dataframe and empty dic_list to write into 
    dic_list = []

    # Set variables for loop ranges to loop through all relevant pages
    year_range = list(range(1970, 2023))
    week_range = list(range(1, 23))

    for i in year_range:
        print(i)
        for j in week_range:
            print(j)
            # Download contents of the web page
            URL = f"https://www.pro-football-reference.com/years/{i}/week_{j}.htm"

            # Check that URL is valid (needed since some years have shorter seasons)
            found = False
            while True:
                time.sleep(1)
                r = requests.get(URL, headers = {'User-agent': 'Super Bot Power Level Over 9000'})
                if r.status_code == 404:
                    break
                # NOTE The site started giving me this 429 error, and the retry time is a damned hour. Fortunately, I already have the 
                # csv from when I used it before. I was able to run it for just th 2022 season and merge that with the original table 
                # for the full dataset. This script still works, it's just slow to the point of near uselessness from the 429 error now.   
                if r.status_code == 429:
                    retry = int(r.headers["Retry-After"])
                    print(f"the server has requested we retry after {retry} seconds, or {'{:.2f}'.format(retry/60)} minutes")
                    time.sleep(retry)
                    continue
                found = True
                break
            if not found:
                break
            
            # Create BeautifulSoup object
            page = r.text
            soup = BeautifulSoup(page, 'html.parser')

            # Set game_type variable
            headings = soup.select("div.section_heading h2")
            game_type = str(headings[1].string)
            game_type = ''.join([i for i in game_type if not i.isdigit()])
            if "week" in game_type.lower():
                game_type = "Regular Season"

            # Set lists to gather team_name and won variables
            winners = get_list("winner", soup)
            losers = get_list("loser", soup)
            draws = get_list("draw", soup)

            # Create loop to iterate over each list and add them to the db
            for _ in range(len(winners)):
                w_team, w_city, w_score, w_won = add_entry(winners[_], True)
                l_team, l_city, l_score, l_won = add_entry(losers[_], False)
                if w_score == "NO DATA" or l_score == "NO DATA":
                    point_dif = "NO DATA"
                else:
                    point_dif = int(w_score)-int(l_score)
                dic_list.append({'year': i, 'week': j, 'team': w_team, 'city': w_city, 'score': w_score, 'won': w_won, 'point_dif': point_dif, 'game_type': game_type.strip()})
                dic_list.append({'year': i, 'week': j, 'team': l_team, 'city': l_city, 'score': l_score, 'won': l_won, 'point_dif': -point_dif, 'game_type': game_type.strip()})
                
            for _ in range(len(draws)):
                d_team, d_city, d_score, d_won = add_entry(draws[_], False)
                dic_list.append({'year': i, 'week': j, 'team': d_team, 'city': d_city, 'score': d_score, 'won': d_won, 'point_dif': 0, 'game_type': game_type.strip()})

    # Write results to a csv file (NOTE This took 7 minutes, probably not the best approach)
    keys = dic_list[0].keys()
    with open('foobaw3.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(dic_list)
    
    end = time.time()
    total_time = end - start
    print("\n"+ str(total_time))

# Quick method for getting both the winners and losers lists easily
def get_list(string, soup):
    this_list = soup.find_all("tr", class_=string)
    new_list = []
    for entry in this_list:
        name = entry.select_one("td > a").string
        teams = name.split(" ")
        score = entry.select_one("td.right").string
        new_list.append({"team": teams[-1], "city": name.replace(teams[-1], " ").strip(), "score": score})
    return new_list

# Ensures and easily identifiable empty row is added if there's an error in the scraping process for any reason
def add_entry(dict, bool):
    if dict == {}:
        team = "NO DATA"
        city = "NO DATA"
        score = "NO DATA"
        won = False
    else:
        team = dict['team']
        city = dict['city']
        score = dict['score']
        won = bool
    return team, city, score, won

if __name__ == "__main__":
    main()