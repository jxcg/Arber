import requests
import yaml
import flask

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
        self.params = params # dict
        self.arb = ArbAuth() # ArbAuth object
        self.matches = {} # dict

    def get_odds_from_odds_api(self):
        url = f"{self.arb.api_url}/upcoming/odds/?regions={self.params['region']}&markets={self.params['markets']}&apiKey={self.arb.api_key}"
        response = requests.get(url, headers=self.arb.headers)
        if response.status_code == 200:
            print("OK")
            print("Response status code: ", response.status_code)
            print(response.json())

        else:
            print("Error")

    def get_odds(self):
        matches = []
        url = f"{self.arb.api_url}/{self.params['scope']}/odds/?regions={self.params['region']}&markets={self.params['markets']}&apiKey={self.arb.api_key}"
        response = requests.get(url, headers=self.arb.headers)
        if response.status_code == 200:
            print("OK")
            print("Response status code: ", response.status_code)
            self.matches = response.json()
            print(type(self.matches))
            print(self.matches)
        
        else:
            print("Error")

        


    def get_arbitrage_opportunity(self, odds):
        EXCHANGE_BOOKIES = ['betfair_ex_uk', 'matchbook', 'smarkets']
        opportunities = []
        
        for event in self.matches:
            print(event)
            
if __name__ == "__main__":
    test_params = {
        "region": 'uk',
        "markets": 'h2h',
        "scope": 'upcoming'
    }

    test_params_soccer_epl = {
        "region": 'uk',
        "markets": 'h2h',
        "scope": 'serie_a'
    }

    
    arb = Arbitrage(test_params)
    #arb.get_odds_from_odds_api()
    arb.get_arbitrage_opportunity(arb.get_odds())
