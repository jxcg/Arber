from flask import Flask, render_template, request
import requests
import yaml


class ArbAuth():
    def __init__(self):
        self.config = self.read_config()
        self.api_key = self.config['api']['key']
        self.api_url = self.config['api']['url']
        self.headers = {'Authorization': f'Bearer {self.api_key}'}

    def read_config(self):
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        return config


class Arbitrage():
    def __init__(self, params):
        self.params = params
        self.arb = ArbAuth()
        self.matches = []

    #Fetch match odds from the Odds API.

    def get_odds(self):
        list_of_sports = ['soccer_epl', 'americanfootball_nfl', 'basketball_nba', 'icehockey_nhl', 'baseball_mlb']

        url = (
            f"{self.arb.api_url}/{self.params['scope']}/odds/"
            f"?regions={self.params['region']}"
            f"&markets={self.params['markets']}"
            f"&daysFrom=21"           
            f"&apiKey={self.arb.api_key}"
        )

            
        print(url)
        response = requests.get(url, headers=self.arb.headers)
        if response.status_code == 200:
            self.matches = response.json()
        else:
            print("Error fetching odds:", response.status_code, response.text)

        return self.matches
    def get_arbitrage_opportunity(self, matches, total_stake=100.0):
        EXCHANGE_BOOKIES = ['matchbook']
        opportunities = []

        for event in matches:
            if 'bookmakers' not in event or not event['bookmakers']:
                continue

            # Filter out exchange-based bookmakers
            filtered_bookmakers = [
                b for b in event['bookmakers']
                if b['key'] not in EXCHANGE_BOOKIES
            ]

            best_odds = {}
            for bookmaker in filtered_bookmakers:
                for market in bookmaker['markets']:
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            outcome_name = outcome['name']
                            outcome_price = outcome['price']
                            # We assume the link is in outcome['url'] 
                            # (or outcome.get('url'), or another field)
                            outcome_link = outcome.get('url', '')

                            # Update if better
                            if outcome_name not in best_odds:
                                best_odds[outcome_name] = {
                                    "price": outcome_price,
                                    "bookie": bookmaker['title'],
                                    "bookie_key": bookmaker['key'],
                                    "link": outcome_link
                                }
                            else:
                                if outcome_price > best_odds[outcome_name]['price']:
                                    best_odds[outcome_name] = {
                                        "price": outcome_price,
                                        "bookie": bookmaker['title'],
                                        "bookie_key": bookmaker['key'],
                                        "link": outcome_link
                                    }

            if len(best_odds) < 2:
                continue

            # Sum of reciprocals check
            sum_of_reciprocals = sum(1.0 / data['price'] for data in best_odds.values())
            is_arb = (sum_of_reciprocals < 1.0)

            if is_arb:
                # Dutching
                stakes = {}
                for outcome_name, data in best_odds.items():
                    fraction = (1.0 / data['price']) / sum_of_reciprocals
                    stake_amount = fraction * total_stake
                    stakes[outcome_name] = round(stake_amount, 2)

                # Guaranteed payout from first outcome
                first_outcome = next(iter(best_odds))
                guaranteed_payout = round(
                    stakes[first_outcome] * best_odds[first_outcome]['price'],
                    2
                )
                potential_profit = round(guaranteed_payout - total_stake, 2)

                opportunities.append({
                    "event_id": event.get("id"),
                    "sport_key": event.get("sport_key"),
                    "commence_time": event.get("commence_time"),
                    "home_team": event.get("home_team"),
                    "away_team": event.get("away_team"),
                    "best_odds": best_odds,  # each outcome -> {price, bookie, link, ...}
                    "sum_of_reciprocals": sum_of_reciprocals,
                    "stakes": stakes,
                    "total_stake": total_stake,
                    "guaranteed_payout": guaranteed_payout,
                    "potential_profit": potential_profit
                })

        return opportunities



###############################################################################
# FLASK APP
###############################################################################
app = Flask(__name__)
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/opportunities", methods=["GET", "POST"])
def opportunities():
    """
    GET: Show all arbitrage opportunities.
    POST: Process manual odds input from the mini calculator at the page bottom.
    """
    # 1) Always fetch real arbitrage opportunities for the page

    list_of_scopes = ['soccer_epl', 'americanfootball_nfl', 'basketball_nba', 'icehockey_nhl', 'baseball_mlb']
    params = {
        "region": "uk",
        "markets": "h2h",
    }
    american_football = {
        "region": "uk",
        "markets": "h2h",
    }



    
    arb = Arbitrage(params)
    matches = arb.get_odds()
    ops = arb.get_arbitrage_opportunity(matches, total_stake=100.0)
    
    # 2) Initialize calculator results as None or defaults



    
    calc_is_arb = None
    calc_sum_recips = 0.0
    calc_stakes = []
    calc_payout = 0.0
    calc_profit = 0.0
    calc_bankroll = 0.0

    # 3) If user POSTs manual odds, process them
    if request.method == "POST":
        try:
            # Grab odds from form
            odds1 = float(request.form["odds1"])
            odds2 = float(request.form["odds2"])
            # odds3 is optional - if empty, ignore
            odds3_raw = request.form.get("odds3", "").strip()
            bankroll = float(request.form["bankroll"])
            calc_bankroll = bankroll

            # Build a list of valid odds
            odds_list = [odds1, odds2]
            if odds3_raw:
                odds_list.append(float(odds3_raw))

            # Sum of reciprocals
            calc_sum_recips = sum(1.0 / o for o in odds_list)

            # Check if arbitrage
            calc_is_arb = (calc_sum_recips < 1.0)

            if calc_is_arb:
                # Compute stakes for each outcome
                for o in odds_list:
                    fraction = (1.0 / o) / calc_sum_recips
                    stake_amount = fraction * bankroll
                    calc_stakes.append(round(stake_amount, 2))
                
                # Guaranteed payout from first outcome
                calc_payout = round(calc_stakes[0] * odds_list[0], 2)
                calc_profit = round(calc_payout - bankroll, 2)
            
        except (ValueError, KeyError):
            # In case user inputs invalid data
            pass

    # 4) Render the template
    return render_template(
        "opportunities.html",
        opportunities=ops,

        # Calculator results
        calc_is_arb=calc_is_arb,
        calc_sum_recips=calc_sum_recips,
        calc_stakes=calc_stakes,
        calc_payout=calc_payout,
        calc_profit=calc_profit,
        calc_bankroll=calc_bankroll
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)