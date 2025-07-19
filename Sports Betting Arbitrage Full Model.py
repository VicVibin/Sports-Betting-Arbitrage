import requests
import json
import pandas as pd
import numpy as np


# Benefits: Can find all the arbitrage in the entire head 2 head market
# COns: Cannot work on outcomes > 2, slow, inefficient
class SBA_slow(object):

    def payoff_arbitrage_database(self, database: pd.DataFrame, wager):
        boolean = None
        for i in range(len(database)):
            payouts = self.american_to_decimal(database.loc[i, "Odds"])
            bets = database.loc[i, "Match"]
            bookmakers = database.loc[i, "Bookmakers"]
            boolean = self.payoff_matrix(wager, bets, payouts, bookmakers)
        return boolean

    def payoff_matrix(self, wager, bets, payouts, bookmakers):
        c = self.quick_arb(payouts) * abs(payouts[-1])
        if c <= 0:
            return None
        else:
            fraction = 1 / c
            payout = wager * payouts[-1] * fraction
            premium = round(payout - wager, 2)
            if premium <= 0:
                return None
            else:
                print(f"Max profit of ${premium} per ${wager} bet")
                print(f"Optimal allocation: {self.optimal_allocation(payouts, payout, bets, bookmakers)}")
            return True

    #  Starts here --> DataFrame of Bets
    def payoff_API(self, wager, API, elem, payout_type="fractional"):
        link = f"https://api.the-odds-api.com/v4/sports/{elem}/odds?regions=us&oddsFormat={payout_type}&apiKey={API}"
        get_response = requests.get(link)
        api_dictionary = get_response.json()
        i = 0
        while i < len(api_dictionary):
            database = self.dataframe_bets(api_dictionary, i)
            boolean, arbitrage_database = self.find_arbitrage(api_dictionary, database, i, type=payout_type)
            if not boolean:
                i += 1
            else:
                i += 1
                infinite_money_glitch = self.payoff_arbitrage_database(arbitrage_database, wager)
                print(infinite_money_glitch)
                return infinite_money_glitch

    #  Moves on to attempting to find arbitrage in this created DataFrame by first converting bets to decimal if otherwise
    def find_arbitrage(self, data, database: pd.DataFrame, i, type="american"):
        if len(database) == 0:
            return None, None
        else:
            arb_database = {"Bookmakers": [], "Match": [], "Odds": []}
            arb_database = pd.DataFrame(arb_database).astype(object)
            sum = 0
            match1 = data[i]['bookmakers'][0]['markets'][0]['outcomes'][0]['name']
            match2 = data[i]['bookmakers'][0]['markets'][0]['outcomes'][1]['name']
            for val1 in database[match1]:
                for val2 in database[match2]:
                    if type == "american":
                        val = self.american_to_decimal([val1, val2])
                        sum = self.quick_arb(val)
                    elif type == "fractional":
                        val = self.fractional_to_decimal([val1, val2])
                        sum = self.quick_arb(val)
                    else:

                        sum = self.quick_arb([val1, val2])
                    if sum:
                        bookmaker_list = database.loc[
                            (database[match1] == val1) | (database[match2] == val2), "Bookmaker"].tolist()
                        arb_database.loc[len(arb_database), :] = [bookmaker_list, [match1, match2], [val1, val2]]
            if not sum:
                return None, None
            return sum, arb_database

    #  Does Quick Arbitrage to Save time if there's no possibility of arbitrage -> Find Arbitrage
    @staticmethod
    def quick_arb(payouts):
        c = 0
        for i in range(len(payouts)):
            c += 1 / payouts[i]
        if c > 1:
            return False
        else:
            return c

    def fast_arb(self, payouts, type="american"):
        if type == "american":
            payouts = self.american_to_decimal(payouts)
        if type == "fractional":
            payouts = self.fractional_to_decimal(payouts)
        c = 0
        for payout in payouts:
            c += 1 / payout
        if c > 1:
            return False
        else:
            return c

    @staticmethod
    def optimal_allocation(payouts, payout, bets, bookmakers):
        bet_dictionary = {}
        if len(bookmakers) > 1:
            for bet, fraction, book in zip(bets, payouts, bookmakers):
                print(f"{bet} : ${round(payout / fraction, 2)}")
                bet_dictionary[bet] = [book, round(payout / fraction, 2), fraction]
        else:
            for bet, fraction in zip(bets, payouts):
                print(f"{bet} : ${round(payout / fraction, 2)}")
                bet_dictionary[bet] = [bookmakers, round(payout / fraction, 2), fraction]
        return bet_dictionary

    # Converts the list of the payouts to decimal style the goes to  ->  quick_arb
    @staticmethod
    def american_to_decimal(odds: list[int]):
        decimal_odds = []
        for i in range(len(odds)):
            if odds[i] < 0:
                decimal = round(100 / -odds[i] + 1, 5)
                decimal_odds.append(decimal)
            if odds[i] >= 0:
                decimal = round(odds[i] / 100 + 1, 5)
                decimal_odds.append(decimal)
        return decimal_odds

    @staticmethod
    def fractional_to_decimal(odds: list[int]):
        decimal_odds = list(np.array(odds) + 1)
        return decimal_odds

    # Develops a DataFrame to store the data in an orderly form ->
    @staticmethod
    def dataframe_bets(data: json, i):
        if len(data) == 0:
            return []
        if len(data[i]['bookmakers']) == 0:
            return []
        else:
            columns = ["Bookmaker"] + [data[i]['bookmakers'][0]['markets'][0]['outcomes'][j]['name']
                                       for j in range(len(data[i]['bookmakers'][0]['markets'][0]['outcomes']))]
            if len(columns) > 3:
                return []
            dataframe = pd.DataFrame(0,
                                     index=range(len(data[i]['bookmakers'])),
                                     columns=columns).astype(object)
            for j in range(len(data[i]['bookmakers'])):
                dataframe.loc[j, "Bookmaker"] = data[i]['bookmakers'][j]['title']
                for k in range(len(data[i]['bookmakers'][0]['markets'][0]['outcomes'])):
                    dataframe.loc[j,
                    data[i]['bookmakers'][j]['markets'][0]['outcomes'][k]['name']] = \
                        data[i]['bookmakers'][j]['markets'][0]['outcomes'][k]['price']
        return dataframe


# Benefits: Extremely fast, can find arbitrage in any outcomes size
# Cons: Only finds the best split and limits to 1 arbitrage per match up
class SBA_Efficient(object):

    # Creates a database to store the arbitrage found ->
    def payoff_arbitrage_database(self, database: pd.DataFrame, wager):
        boolean = None
        for i in range(len(database)):
            payouts = self.american_to_decimal(database.loc[i, "Odds"])
            bets = database.loc[i, "Match"]
            bookmakers = database.loc[i, "Bookmakers"]
            boolean = self.payoff_matrix(wager, bets, payouts, bookmakers)
        return boolean

    # Creates the payoff matrix to be displayed ->
    def payoff_matrix(self, wager, bets, payouts, bookmakers):
        c = self.fast_arb(payouts) * abs(payouts[-1])
        if c <= 0:
            return None
        else:
            fraction = 1 / c
            payout = wager * payouts[-1] * fraction
            premium = round(payout - wager, 2)
            if premium <= 0:
                return None
            else:
                print(f"Max profit of ${premium} per ${wager} bet")
                print(f"Optimal allocation: {self.optimal_allocation(payouts, payout, bets, bookmakers)}")
            return True

    #  Starts here --> DataFrame of Bets
    def payoff_API(self, wager, API, elem, payout_type="fractional"):
        link = f"https://api.the-odds-api.com/v4/sports/{elem}/odds?regions=us&oddsFormat={payout_type}&apiKey={API}"
        get_response = requests.get(link)
        api_dictionary = get_response.json()
        i = 0
        while i < len(api_dictionary):
            database = self.dataframe_bets(api_dictionary, i)
            boolean, arbitrage_database = self.find_arbitrage(database, type=payout_type)
            if not boolean:
                i += 1
            else:
                i += 1
                infinite_money_glitch = self.payoff_arbitrage_database(arbitrage_database, wager)
                print(infinite_money_glitch)
                return infinite_money_glitch

    #  Attempts to find arbitrage in this a Dataframe and returns a list -> Quick_Arb
    def find_arbitrage(self, database: pd.DataFrame, type="american"):
        if len(database) == 0:
            return None, None
        else:
            columns = list(database.columns)
            del columns[0]
            arb_database = {"Bookmakers": [], "Match": [], "Odds": []}
            arb_database = pd.DataFrame(arb_database).astype(object)
            # Get the maximum values for each column
            max_values = database.max().tolist()
            max_id = database.idxmax().tolist()
            del max_values[0]
            del max_id[0]
            bookmakers_list = []
            for i in range(len(max_id)):
                bookmakers_list.append(database.loc[max_id[i], "Bookmaker"])
            boolean = self.fast_arb(max_values, type)
            if boolean:
                arb_database.loc[len(arb_database), :] = [bookmakers_list, [columns], max_values]
            return boolean, arb_database

    #  Does Quick Arbitrage to Save time if there's no possibility of arbitrage, if there is -> Payoff_Arb_DB
    def fast_arb(self, payouts: list[int], type="american"):
        if type == "american":
            payouts = self.american_to_decimal(payouts)
        if type == "fractional":
            payouts = self.fractional_to_decimal(payouts)
        c = 0
        for payout in payouts:
            c += 1 / payout
        if c > 1:
            return False
        else:
            return c

    # Displays the optimal allocation
    @staticmethod
    def optimal_allocation(payouts, payout, bets, bookmakers):
        bet_dictionary = {}
        if len(bookmakers) > 1:
            for bet, fraction, book in zip(bets, payouts, bookmakers):
                print(f"{bet} : ${round(payout / fraction, 2)}")
                bet_dictionary[bet] = [book, round(payout / fraction, 2), fraction]
        else:
            for bet, fraction in zip(bets, payouts):
                print(f"{bet} : ${round(payout / fraction, 2)}")
                bet_dictionary[bet] = [bookmakers, round(payout / fraction, 2), fraction]
        return bet_dictionary

    # Converts the list of the payouts to decimal style the goes to  ->  quick_arb
    @staticmethod
    def american_to_decimal(odds: list[int]):
        decimal_odds = []
        for i in range(len(odds)):
            if odds[i] < 0:
                decimal = round(100 / -odds[i] + 1, 5)
                decimal_odds.append(decimal)
            if odds[i] >= 0:
                decimal = round(odds[i] / 100 + 1, 5)
                decimal_odds.append(decimal)
        return decimal_odds

    @staticmethod
    def fractional_to_decimal(odds: list[int]):
        decimal_odds = list(np.array(odds) + 1)
        return decimal_odds

    # Develops a DataFrame to store the data in an orderly form -> Find Arbitrage
    @staticmethod
    def dataframe_bets(data: json, i):
        if len(data) == 0:
            return []
        if len(data[i]['bookmakers']) == 0:
            return []
        else:
            columns = ["Bookmaker"] + [data[i]['bookmakers'][0]['markets'][0]['outcomes'][j]['name']
                                       for j in range(len(data[i]['bookmakers'][0]['markets'][0]['outcomes']))]
            dataframe = pd.DataFrame(0,
                                     index=range(len(data[i]['bookmakers'])),
                                     columns=columns).astype(object)
            for j in range(len(data[i]['bookmakers'])):
                dataframe.loc[j, "Bookmaker"] = data[i]['bookmakers'][j]['title']
                for k in range(len(data[i]['bookmakers'][j]['markets'][0]['outcomes'])):
                    if len(data[i]['bookmakers'][j]['markets'][0]['outcomes'][k]) > 1:
                        dataframe.loc[j,
                        data[i]['bookmakers'][j]['markets'][0]['outcomes'][k]['name']] = \
                            data[i]['bookmakers'][j]['markets'][0]['outcomes'][k]['price']
                    else:
                        print(f" Out of range error for this index: {data[i]['bookmakers'][j]['markets'][0]['outcomes'][k]}")
        return dataframe


def api():
    api_key = "a66bb1adbfee86730cd4eb1f365b80cb"
    return api_key


def total_checker(wager, api, data):
    value = None
    for i in range(len(data)):
        print(f"Market Being Analyzed: {data[i]["key"]}")
        key = data[i]["key"]
        #  value = SBA_slow().payoff_API(wager, api ,key, payout_type="american")
        value = SBA_Efficient().payoff_API(wager, api, key, payout_type="american")
    return value


true = True
false = False
data2 = [
    {
        "key": "americanfootball_ncaaf",
        "group": "American Football",
        "title": "NCAAF",
        "description": "US College Football",
        "active": True,
        "has_outrights": False
    },
    {
        "key": "americanfootball_ncaaf_championship_winner",
        "group": "American Football",
        "title": "NCAAF Championship Winner",
        "description": "US College Football Championship Winner",
        "active": True,
        "has_outrights": True
    },
    {
        "key": "americanfootball_nfl",
        "group": "American Football",
        "title": "NFL",
        "description": "US Football",
        "active": True,
        "has_outrights": False
    },
    {
        "key": "americanfootball_nfl_super_bowl_winner",
        "group": "American Football",
        "title": "NFL Super Bowl Winner",
        "description": "Super Bowl Winner 2024/2025",
        "active": True,
        "has_outrights": True
    },
    {
        "key": "aussierules_afl",
        "group": "Aussie Rules",
        "title": "AFL",
        "description": "Aussie Football",
        "active": True,
        "has_outrights": False
    },
    {
        "key": "baseball_mlb_world_series_winner",
        "group": "Baseball",
        "title": "MLB World Series Winner",
        "description": "World Series Winner 2025",
        "active": True,
        "has_outrights": True
    },
    {
        "key": "basketball_euroleague",
        "group": "Basketball",
        "title": "Basketball Euroleague",
        "description": "Basketball Euroleague",
        "active": True,
        "has_outrights": False
    },
    {
        "key": "basketball_nba",
        "group": "Basketball",
        "title": "NBA",
        "description": "US Basketball",
        "active": True,
        "has_outrights": False
    },
    {
        "key": "basketball_nba_championship_winner",
        "group": "Basketball",
        "title": "NBA Championship Winner",
        "description": "Championship Winner 2024/2025",
        "active": true,
        "has_outrights": true
    },
    {
        "key": "basketball_nbl",
        "group": "Basketball",
        "title": "NBL",
        "description": "AU National Basketball League",
        "active": True,
        "has_outrights": False
    },
    {
        "key": "basketball_ncaab",
        "group": "Basketball",
        "title": "NCAAB",
        "description": "US College Basketball",
        "active": True,
        "has_outrights": False
    },
    {
        "key": "basketball_ncaab_championship_winner",
        "group": "Basketball",
        "title": "NCAAB Championship Winner",
        "description": "US College Basketball Championship Winner",
        "active": True,
        "has_outrights": True
    },
    {
        "key": "basketball_wncaab",
        "group": "Basketball",
        "title": "WNCAAB",
        "description": "US Women's College Basketball",
        "active": True,
        "has_outrights": False
    },
    {
        "key": "boxing_boxing",
        "group": "Boxing",
        "title": "Boxing",
        "description": "Boxing Bouts",
        "active": True,
        "has_outrights": False
    },
    {
        "key": "cricket_big_bash",
        "group": "Cricket",
        "title": "Big Bash",
        "description": "Big Bash League",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "cricket_international_t20",
        "group": "Cricket",
        "title": "International Twenty20",
        "description": "International Twenty20",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "cricket_odi",
        "group": "Cricket",
        "title": "One Day Internationals",
        "description": "One Day Internationals",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "cricket_test_match",
        "group": "Cricket",
        "title": "Test Matches",
        "description": "International Test Matches",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "golf_masters_tournament_winner",
        "group": "Golf",
        "title": "Masters Tournament Winner",
        "description": "2025 Winner",
        "active": true,
        "has_outrights": true
    },
    {
        "key": "golf_pga_championship_winner",
        "group": "Golf",
        "title": "PGA Championship Winner",
        "description": "2025 Winner",
        "active": true,
        "has_outrights": true
    },
    {
        "key": "golf_the_open_championship_winner",
        "group": "Golf",
        "title": "The Open Winner",
        "description": "2025 Winner",
        "active": true,
        "has_outrights": true
    },
    {
        "key": "golf_us_open_winner",
        "group": "Golf",
        "title": "US Open Winner",
        "description": "2025 Winner",
        "active": true,
        "has_outrights": true
    },
    {
        "key": "icehockey_nhl",
        "group": "Ice Hockey",
        "title": "NHL",
        "description": "US Ice Hockey",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "icehockey_nhl_championship_winner",
        "group": "Ice Hockey",
        "title": "NHL Championship Winner",
        "description": "Stanley Cup Winner 2024/2025",
        "active": true,
        "has_outrights": true
    },
    {
        "key": "icehockey_sweden_allsvenskan",
        "group": "Ice Hockey",
        "title": "HockeyAllsvenskan",
        "description": "Swedish Hockey Allsvenskan",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "mma_mixed_martial_arts",
        "group": "Mixed Martial Arts",
        "title": "MMA",
        "description": "Mixed Martial Arts",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "rugbyleague_nrl",
        "group": "Rugby League",
        "title": "NRL",
        "description": "Aussie Rugby League",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_australia_aleague",
        "group": "Soccer",
        "title": "A-League",
        "description": "Aussie Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_austria_bundesliga",
        "group": "Soccer",
        "title": "Austrian Football Bundesliga",
        "description": "Austrian Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_belgium_first_div",
        "group": "Soccer",
        "title": "Belgium First Div",
        "description": "Belgian First Division A",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_efl_champ",
        "group": "Soccer",
        "title": "Championship",
        "description": "EFL Championship",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_england_efl_cup",
        "group": "Soccer",
        "title": "EFL Cup",
        "description": "League Cup",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_england_league1",
        "group": "Soccer",
        "title": "League 1",
        "description": "EFL League 1",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_england_league2",
        "group": "Soccer",
        "title": "League 2",
        "description": "EFL League 2 ",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_epl",
        "group": "Soccer",
        "title": "EPL",
        "description": "English Premier League",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_fa_cup",
        "group": "Soccer",
        "title": "FA Cup",
        "description": "Football Association Challenge Cup",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_fifa_world_cup_winner",
        "group": "Soccer",
        "title": "FIFA World Cup Winner",
        "description": "FIFA World Cup Winner 2026",
        "active": true,
        "has_outrights": true
    },
    {
        "key": "soccer_france_ligue_one",
        "group": "Soccer",
        "title": "Ligue 1 - France",
        "description": "French Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_germany_bundesliga",
        "group": "Soccer",
        "title": "Bundesliga - Germany",
        "description": "German Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_germany_bundesliga2",
        "group": "Soccer",
        "title": "Bundesliga 2 - Germany",
        "description": "German Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_germany_liga3",
        "group": "Soccer",
        "title": "3. Liga - Germany",
        "description": "German Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_greece_super_league",
        "group": "Soccer",
        "title": "Super League - Greece",
        "description": "Greek Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_italy_serie_a",
        "group": "Soccer",
        "title": "Serie A - Italy",
        "description": "Italian Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_italy_serie_b",
        "group": "Soccer",
        "title": "Serie B - Italy",
        "description": "Italian Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_league_of_ireland",
        "group": "Soccer",
        "title": "League of Ireland",
        "description": "Airtricity League Premier Division",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_netherlands_eredivisie",
        "group": "Soccer",
        "title": "Dutch Eredivisie",
        "description": "Dutch Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_portugal_primeira_liga",
        "group": "Soccer",
        "title": "Primeira Liga - Portugal",
        "description": "Portugese Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_spain_la_liga",
        "group": "Soccer",
        "title": "La Liga - Spain",
        "description": "Spanish Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_spain_segunda_division",
        "group": "Soccer",
        "title": "La Liga 2 - Spain",
        "description": "Spanish Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_spl",
        "group": "Soccer",
        "title": "Premiership - Scotland",
        "description": "Scottish Premiership",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_sweden_allsvenskan",
        "group": "Soccer",
        "title": "Allsvenskan - Sweden",
        "description": "Swedish Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_switzerland_superleague",
        "group": "Soccer",
        "title": "Swiss Superleague",
        "description": "Swiss Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_turkey_super_league",
        "group": "Soccer",
        "title": "Turkey Super League",
        "description": "Turkish Soccer",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_uefa_champs_league",
        "group": "Soccer",
        "title": "UEFA Champions League",
        "description": "European Champions League",
        "active": true,
        "has_outrights": false
    },
    {
        "key": "soccer_uefa_europa_conference_league",
        "group": "Soccer",
        "title": "UEFA Europa Conference League",
        "description": "UEFA Europa Conference League",
        "active": true,
        "has_outrights": False
    },
    {
        "key": "soccer_uefa_europa_league",
        "group": "Soccer",
        "title": "UEFA Europa League",
        "description": "European Europa League",
        "active": True,
        "has_outrights": False
    }
]

api = api()
wage = 100

total_checker(wage, api, data2)
