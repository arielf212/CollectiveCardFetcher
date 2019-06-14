import requests
from fetcher import dict_fetcher

class CollectiveFetcher(dict_fetcher.DictFetcher):
    """
    This fetches every collective card that is not undraftable (requested by toukkan)
    """

    def __init__(self):
        cards = {}
        # every card ingame is stored here 
        request_url = 'https://server.collective.gg/api/public-cards/'
        for card_info in requests.get(request_url).json()['cards']:
            # some old cards don't have an image link
            if card_info['imgurl'] is not None and card_info['rarity'] != "Undraftable":
                cards[card_info['name'].lower()] = card_info['imgurl']
        super().__init__(cards)     

    


class CollectiveTokenFetcher(dict_fetcher.DictFetcher):
    """
    This fetches every collective card that is undraftable (aka a token).
    (requested by toukkan)
    """

    def __init__(self):
        cards = {}
        # every card ingame is stored here 
        request_url = 'https://server.collective.gg/api/public-cards/'
        for card_info in requests.get(request_url).json()['cards']:
            # some old cards don't have an image link
            if card_info['imgurl'] is not None and card_info['rarity'] == "Undraftable":
                cards[card_info['name'].lower()] = card_info['imgurl']
        super().__init__(cards)


class CollectiveAnyFetcher(dict_fetcher.DictFetcher):
    """
    This fetches any collective card that exists inside the game
    """
    def __init__(self):
        cards = {}
        # every card ingame is stored here 
        request_url = 'https://server.collective.gg/api/public-cards/'
        for card_info in requests.get(request_url).json()['cards']:
            # some old cards don't have an image link
            if card_info['imgurl'] is not None:
                cards[card_info['name'].lower()] = card_info['imgurl']
        super().__init__(cards)