from fuzzywuzzy import fuzz

class DictFetcher:
    """
    This is a helper class that already implements a search algorithm
    for finding a card in a {name:imgurl} dictionary.
    """

    def __init__(self, card_set):
        self.card_set = card_set

    def __getitem__(self ,card):
        max_ratio = (' ', 0)  # maximum score in ratio exam
        max_partial = (' ', 0)  # maximum sort in partial ratio exam
        list_ratio = []
        list_partial = []
        for entry in self.card_set:
            # lets check if an entry is "good enough" to be our card
            ratio = fuzz.ratio(card, entry)
            partial = fuzz.partial_ratio(card, entry)
            if ratio > max_ratio[1]:
                max_ratio = (entry, ratio)
                list_ratio = [max_ratio]
            elif ratio == max_ratio[1]:
                list_ratio.append((entry, ratio))
            if partial > max_partial[1]:
                max_partial = (entry, partial)
                list_partial = [max_partial]
            elif partial == max_partial[1]:
                list_partial.append((entry, partial))
        if max_ratio[1] < 20 and max_partial[1] < 20:
            raise KeyError("Card wasn't found")
        if max_partial[1] > max_ratio[1]:
            return self.card_set[max_partial[0]]
        return self.card_set[max_ratio[0]]