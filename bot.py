import praw , discord
import os # I need this to use environment variables on heroku
import csv # this is to browse the core set
from discord.ext import commands

# Reddit variables
reddit = praw.Reddit(client_id = 'x4FICJQqO4D14g' , client_secret = 'i9kip94Qs6R4Kfy77XYzDuv0z8Q' , user_agent = 'Card fetcher for collective.') # gives access to reddit
collective = reddit.subreddit('collectivecg') # gives access to the Collective subreddit

# discord variables
bot = commands.Bot(command_prefix='?')

# functions
def get_card_name(text):
    '''takes a striing and extracts card names from it. card names are encapsulated in [[xxxx]] where xxxx is the card name'''
    cards = [] # list of names of cards
    start = text.find('[[')
    while start != -1: # until there are no more brackets
        end = text.find(']]')
        if end == -1:
            return cards # if there is an opener but no closer then someone fucked up
        else:
            cards.append(text[start+2:end]) # gets the name of the card
        text = text[end+2 : ] # cuts out the part with the card
        start = text.find('[[') # and the cicle begins anew
    return cards

def save_card(name , link):
    with open('temp_cards.csv' , 'a') as temp_cards_file:
        temp_cards = csv.writer(temp_cards_file , delimiter = ',')
        temp_cards.writerow([name , link])
# events
@bot.event
async def on_message(message):
    if message.content.startswith('!'):
        parameters = message.content.split(' ') # all commands look like this : '!command par1 par2 par3...'
        if parameters[0] == '!save':
            save_card(parameters[1] , parameters[2]) # saved the card data (name , link) into the csv with temp cards.
    else:
        cards = get_card_name(message.content) # this gets all card names in the message
        links = [] # here are the card links stored
        for card in cards:
            if card.startswith('top ') and len(card.split(' ')) == 2: # the name looks like this :"top X"
                num = card.split(' ')[1]
                if num.isdigit():
                    num = int(num)
                    for post in collective.top(limit = int(num) , time_filter='week'):
                        links.append(post.url)
            else:
                found = False
                for post in collective.search('[card] {}'.format(card) , limit = 1): # this searches the subreddit for the card name with the [card] tag and takes the top suggestion
                    found = True
                    links.append(post.url)
                if not found: # if we didnt find any cards that go by that name
                    with open('core_set.csv' , 'r') as core_set_file: # the we check in the core_set
                        with open('temp_cards.csv' , 'r') as temp_cards_file:
                            core_set = csv.reader(core_set_file , delimiter = ',') # this opens the csv file
                            temp_cards = csv.reader(temp_cards_file , delimiter = ',')
                            for core_card in core_set + temp_cards: # this runs trough all the rows
                                name , link = core_card
                                if name.lower() == card.lower():
                                    links.append(link)
                                    found = True
                                if found:
                                    break # no need to continue searching
        await bot.send_message(message.channel , '\n'.join(links))
bot.run(os.environ.get('BOT_TOKEN'))