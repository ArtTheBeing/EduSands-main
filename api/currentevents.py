import requests

class CurrentEvent():
    def __init__(self):
        self.url = 'https://newsapi.org/v2/everything'
        self.apikey = 'API_KEY'

    def getnews(self):
        query = input('Query: ')
        params = {'q' : query,
                  'apiKey' : self.apikey}
        news = requests.get(url=self.url, params=params)
        return news