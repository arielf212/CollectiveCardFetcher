import requests

class MtgFetcher:

    def __getitem__(self, card_name):
        """
        This method uses the scryfall api in order to get the card image.
        """

        if self.exists(card_name):
            return 'https://api.scryfall.com/cards/named?fuzzy={};format=image;version=png'.format(card_name.replace(' ', '%20'))
        else: raise KeyError("Card not found")
    
    def exists(self, card_name):
        url = 'https://api.scryfall.com/cards/named/'
        available = requests.get(url, {'fuzzy': card_name}).json() 
        return available['object'] == 'card'