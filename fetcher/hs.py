from fetcher import dict_fetcher
import requests

class HsFetcher(dict_fetcher.DictFetcher):

    def __init__(self):
        card_set = {}
        card_set_url = "https://api.hearthstonejson.com/v1/31532/enUS/cards.collectible.json"
        for card in requests.get(card_set_url).json():
            card_set[card['name']] = self.get_card_art_link(card['id'])
        return super().__init__(card_set)
    

    def get_card_art_link(card_id):
        """
        fetches a card image from hearthstonejson.com based on the id of the card.
        """
        return "https://art.hearthstonejson.com/v1/render/latest/enUS/256x/{}.png".format(card_id)