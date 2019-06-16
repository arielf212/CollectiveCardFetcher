import praw, os

class CollectiveSub:
    """
    this class is used in order to get data from the collective subreddit.
    """

    def __init__(self):
        reddit = praw.Reddit(client_id=os.environ.get("CID"),
                     client_secret=os.environ.get("CSECRET"),
                     user_agent='Card fetcher for Collective.')
        self.sub = reddit.subreddit('collectivecg')
    

    def __getitem__(self, card_name):
        """
        fetches a card from the subreddit.
        """
        # searches the usbreddit for a card with the given name
        # and grabs the first result who's name starts with "["
        for post in self.sub.search(card_name, limit=1):
            if post.title.startswith('['):
                return post.url
        raise KeyError("Card Not found")
    

    def get_top(self, num, type, week):
        """
        Returns the top <num> post of the subreddit that were posted on week <week> of type <type>.
        for example: get_top(10, "card", 44) will return the top 10 posted cards of week 44.
        """
        ret = []
        if num >= 1000:
            return "You requested too many posts at once. please try to ask for less posts next time!"
        # takes the top 1000 cards of this week and sorts them in order of upvotes
        posts = sorted(
            self.sub.search('flair:' + week, limit=1000, sort='top'),
             key=lambda x: x.score,
             reverse=True
        )
        for post in list(filter(lambda x: x.title.lower().startswith(type), posts))[:num]:
            ret.append(post.url + ' | ' + str(post.score) + ' | ' + str(int(post.upvote_ratio*100))+'%')
        return ret