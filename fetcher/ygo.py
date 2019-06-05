import requests

class YugiohFetcher():

    def __getitem__(self, card_name):
        # checks using the ygoprices api if the cards exists at all.
        # if it does, the api will return a link with the full name as one of the query string.
        # we can rip out that name, and return a card image with the same name.
        query = requests.get('https://yugiohprices.com/search_card?search_text=' + card_name)
        if query:
            return 'https://static-3.studiobebop.net/ygo_data/card_images/{}.jpg'.format(
                query.url.split('name=')[-1].replace('+', '_').replace('-', '_').replace('%22', '_')
                )
        else:
            raise KeyError("Card not found")