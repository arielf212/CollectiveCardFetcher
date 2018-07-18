import praw
from discord.ext import commands
from fuzzywuzzy import fuzz
import asyncio
import os # I need this to use environment variables on heroku
import csv # this is to browse the core set
# Reddit variables
reddit = praw.Reddit(client_id = 'x4FICJQqO4D14g' , client_secret = 'i9kip94Qs6R4Kfy77XYzDuv0z8Q' , user_agent = 'Card fetcher for Collective.') # gives access to reddit
collective = reddit.subreddit('collectivecg') # gives access to the Collective subreddit

# discord variables
bot = commands.Bot(command_prefix='?')

#regular variables
global post
post = False

# functions
def get_card_name(text):
    '''takes a string and extracts card names from it. card names are encapsulated in [[xxxx]] where xxxx is the card name'''
    cards = [] # list of names of cards
    start = text.find('[[')
    while start != -1: # until there are no more brackets
        end = text.find(']]')
        if end == -1:
            return cards # if there is an opener but no closer then someone fucked up
        else:
            cards.append(text[start+2:end]) # gets the name of the card
        text = text[end+2 : ] # cuts out the part with the card
        start = text.find('[[') # and the circle begins anew
    return cards

def save_card(name , link):
    '''saves a link to a card picture with the name specified in the temp_cards.csv document'''
    with open('temp_cards.csv' , 'a') as temp_cards_file:
        temp_cards = csv.writer(temp_cards_file , delimiter = ',')
        temp_cards.writerow([name , link])

def load_core_set():
    '''loads the core set cards from core_set.csv into a dictionary called core_set'''
    core_set = {}
    with open('core_set.csv' , 'r') as core_set_file:
        core_set_csv = csv.reader(core_set_file , delimiter = ',')
        for row in core_set_csv:
            name , link = row # unpack the row into a name and a link
            core_set[name] = link # adds the card into the core_set dictionary
    return core_set

def load_temp_cards():
    '''loads the temp saved cards from temp_cards.csv into a dictionary called temp_cards'''
    temp_cards = {}
    with open('temp_cards.csv' , 'r') as temp_cards_file:
        temp_cards_csv = csv.reader(temp_cards_file , delimiter = ',')
        for row in temp_cards_csv:
            if row != []: # there is a bug that adds empty lines .this prevent the program from crashing from it
                name , link = row # unpack the row into a name and a link
                temp_cards[name] = link # adds the card into the core_set dictionary
    return temp_cards

def get_card():
    '''fetches the newest card from reddit'''
    for card in collective.new(limit = 1):
        return 'https://www.reddit.com' + card.permalink

async def repost_card(post_channel):
    last_card = get_card()
    while True:
        card = get_card()
        if card != last_card:
            last_card = card
            await bot.send_message(post_channel , card)
        await asyncio.sleep(10)

def get_link(card):
    max_ratio = (' ', 0)  # maximum score in ratio exam
    max_partial = (' ', 0)  # maximum sort in partial ratio exam
    list_ratio = []
    list_partial = []
    #lets put the core_set and temp_cards together
    search_list = temp_cards.copy()
    search_list.update(core_set)
    for entry in search_list:
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
    if max_partial[1] > max_ratio[1]:
        return search_list[max_partial[0]]
    return search_list[max_ratio[0]]

def get_top(num , week):
    return_list = []
    index = 1
    while index <= num:
        post = ''
        for submission in collective.search('flair:(week ' + str(week) + ')',limit = index , sort = 'top'):
            post = submission
        if post.title.startswith('[Cosmetic'):
            num+=1
            index+=1
        else:
            return_list.append(post.url)
            index+=1
    return return_list

# events
@bot.event
async def on_message(message):
    global post
    if message.content.startswith('!'):
        parameters = message.content.split(' ') # all commands look like this : '!command par1 par2 par3...'
        if parameters[0] == '!save':
            save_card(' '.join(parameters[1:-1]), parameters[-1]) # saved the card data (name , link) into the csv with temp cards.
            temp_cards[parameters[1]] = parameters[2] # adds the card to the current dictionary
            await bot.send_message(message.channel , '{} was added!'.format(parameters[1])) # sends confirmation message
            return 0 # quits the function
        elif parameters[0] == '!alive':
            await bot.send_message(message.channel , 'im alive and well!')
        elif parameters[0] == '!server':
            await bot.send_message(message.channel , 'https://discordapp.com/api/oauth2/authorize?client_id=465866501715525633&permissions=522304&scope=bot')
        elif parameters[0] == '!github' or parameters[0] == '!code':
            await bot.send_message(message.channel , 'https://github.com/fireasembler/CollectiveCardFetcher')
        elif parameters[0] == '!start':
            post = True
            await bot.send_message(message.channel, 'will start posting here!')
            bot.loop.create_task(repost_card(message.channel))
        elif parameters[0] == '!stop':
            post = False
            await bot.send_message(message.channel, "will stop!")
        elif parameters[0] == '!nice' and parameters[1] in ['art', 'art!']:
            await bot.send_file(message.channel , 'nice art.jpg')
        elif parameters[0].startswith('!good'):
            os.environ['GOOD'] = str(int(os.environ['GOOD']) + 1)
            await bot.send_message(message.channel , 'thank you! :)')
        elif parameters[0].startswith('!bad'):
            os.environ['BAD'] = str(int(os.environ['BAD']) + 1)
            await bot.send_message(message.channel , 'ill try better next time :(')
        elif parameters[0] == '!score':
            await bot.send_message(message.channel , 'good: ' + os.environ.get('GOOD'))
            await bot.send_message(message.channel ,'bad: ' + os.environ.get('BAD'))
    else:
        cards = get_card_name(message.content) # this gets all card names in the message
        links = [] # here are the card links stored
        for card in cards:
            if card.startswith('top '):
                if len(card.split(' ')) == 2: # the name looks like this :"top X"
                    num = card.split(' ')[1]
                    if num.isdigit():
                        links += get_top(int(num) , 9)
                elif len(card.split(' ')) == 4 and card.split(' ')[2] == 'week': # the name looks like this: "top X week Y"
                    num = card.split(' ')[1]
                    week = card.split(' ')[3]
                    if num.isdigit() and week.isdigit():
                        links += get_top(int(num) , int(week))
            else:
                found = False
                for post in collective.search(card , limit = 1): # this searches the subreddit for the card name with the [card] tag and takes the top suggestion
                    if post.title.startswith('[Card]') or post.title.startswith('[DC') or post.title.startswith('[Meta]'):
                        links.append(post.url)
                        found = True
                if not found: # if we didn't find any cards that go by that name
                    links.append(get_link(card))
        if links: # if there are any links
            for x in range((len(links)//5)+1): # this loops runs one time plus once for every five links since discord can only display five pictures per message
                await bot.send_message(message.channel , '\n'.join(links[5*x:5*(x+1)]))

#main
core_set = load_core_set()
temp_cards = load_temp_cards()
bot.run(os.environ.get('BOT_TOKEN'))
