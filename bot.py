import praw
from discord.ext import commands
import asyncio
import os # I need this to use environment variables on heroku
import csv # this is to browse the core set
# Reddit variables
reddit = praw.Reddit(client_id = 'x4FICJQqO4D14g' , client_secret = 'i9kip94Qs6R4Kfy77XYzDuv0z8Q' , user_agent = 'Card fetcher for collective.') # gives access to reddit
collective = reddit.subreddit('collectivecg') # gives access to the Collective subreddit

# discord variables
bot = commands.Bot(command_prefix='?')

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

async def post_from_reddit():
    global last_post , post_channel , does_repost
    while True:
        if does_repost:
            for post in collective.new(limit = 1):
                print(post.title + " " + last_post)
                if post.title != last_post: # if the post title isnt the same as the last post then we can post it
                    await bot.send_message(post_channel , post.url)
                    last_post = post.title
            await asyncio.sleep(10) #runs every ten seconds

# events
@bot.event
async def on_message(message):
    global last_post , post_channel , does_repost
    if message.content.startswith('!'):
        parameters = message.content.split(' ') # all commands look like this : '!command par1 par2 par3...'
        if parameters[0] == '!save':
            save_card(parameters[1] , parameters[2]) # saved the card data (name , link) into the csv with temp cards.
            temp_cards[parameters[1]] = parameters[2] # adds the card to the current dictionary
            await bot.send_message(message.channel , '{} was added!'.format(parameters[1])) # sends confirmation message
            return 0 # quits the function
        elif parameters[0] == '!alive':
            await bot.send_message(message.channel , 'im alive and well!')
        elif parameters[0] == '!server':
            await bot.send_message(message.channel , 'https://discordapp.com/api/oauth2/authorize?client_id=458351287310876672&permissions=522304&scope=bot')
        elif parameters[0] == '!github' or parameters[0] == '!code':
            await bot.send_message(message.channel , 'https://github.com/fireasembler/CollectiveCardFetcher')
        elif parameters[0] == '!repost':
            print("reposrty")
            post_channel = message.channel
            does_repost = True
        elif parameters[0] == '!stopost':
            does_repost = False
    else:
        cards = get_card_name(message.content) # this gets all card names in the message
        links = [] # here are the card links stored
        for card in cards:
            print(card)
            if card.startswith('top ') and len(card.split(' ')) == 2: # the name looks like this :"top X"
                num = card.split(' ')[1]
                if num.isdigit():
                    num = int(num)
                    for post in collective.top(limit = int(num) , time_filter='week'):
                        links.append(post.url)
            else:
                found = False
                for post in collective.search(card , limit = 1): # this searches the subreddit for the card name with the [card] tag and takes the top suggestion
                    print(post.title)
                    if post.title.startswith('[Card]') or post.title.startswith('[DC') or post.title.startswith('[Meta]'):
                        links.append(post.url)
                        found = True
                print(found)
                if not found: # if we didn't find any cards that go by that name
                    print(found)
                    print(card in core_set)
                    if card in core_set:
                        links.append(core_set[card])
                    elif card in temp_cards:
                        links.append(temp_cards[card])
        if links: # if there are any links
            for x in range((len(links)//5)+1): # this loops runs one time plus once for every five links since discord can only display five pictures per message
                await bot.send_message(message.channel , '\n'.join(links[5*x:5*(x+1)]))
@bot.event
async def on_ready():
    bot.loop.create_task(post_from_reddit())

#main
core_set = load_core_set()
temp_cards = load_temp_cards()
global last_post , does_repost
does_repost = False
for post in collective.new(limit = 1):
    last_post = post.title # we need this variable to check if a post was already posted before reposting it
bot.run(os.environ.get('BOT_TOKEN'))