import praw
import io
from discord.ext import commands
import discord
import requests # this is for the mtg search
from fuzzywuzzy import fuzz
import psycopg2
import asyncio
import os # I need this to use environment variables on heroku
import csv # this is to browse the core set
import json # for ygo cards


# Reddit variables
reddit = praw.Reddit(client_id=os.environ.get("CID"),
                     client_secret=os.environ.get("CSECRET"),
                     user_agent='Card fetcher for Collective.')  # gives access to reddit
collective = reddit.subreddit('collectivecg') # gives access to the Collective subreddit

# discord variables
bot = commands.Bot(command_prefix='!')
embed = discord.Embed(title="CollectiveCardFetcher Help", description="here is a list of commands for the bot:", color=0x00FFFF)
embed.add_field(name='!alive', value='The bot will respond with "im alive and well!"')
embed.add_field(name='!server', value="The bot will respond with a link that can be used to add him to a server. note: you need to be an admin in a server to add a bot.")
embed.add_field(name='!github', value="The bot will respond with a link to the github page of the bot.")
embed.add_field(name='!good', value='Ups the score of the bot. Will make the bot respond with a thankful message.')
embed.add_field(name='!bad', value='Reduces the score of the bot. Will make the bot respond with an apologetic message.')
embed.add_field(name='!score', value='The bot will respond with the amount of votes given to him trough !bad and !good')
embed.add_field(name='!image <link>', value='Will return the art of the card linked.')
embed.add_field(name='!new', value='Takes a topic and returns an explanation about it')
embed.add_field(name="!meme", value="Takes a name and returns a meme saved under that name")
embed.add_field(name='!leaderboard', value='Responds with an embed holding the value of the current leaderboard.')
bot.remove_command('help')
# the database
db = psycopg2.connect(os.environ.get("DATABASE_URL"), sslmode='require')
cursor = db.cursor()

# functions
def get_card_name(text):
    '''takes a string and extracts card names from it. card names are encapsulated in [[xxxx]] where xxxx is the card name'''
    cards = []  # list of names of cards
    start = text.find('[[')
    while start != -1:  # until there are no more brackets
        end = text.find(']]')
        if end == -1:
            return cards  # if there is an opener but no closer then someone fucked up
        else:
            query = text[start + 2:end]
            if query.find(':') > 0:
                mod = query[:query.find(':')].lower()
                card = query[query.find(':')+1:].lstrip(' ')
                if mod not in POSSIBLE_MODS:
                    card = query
                    mod = 'none'
                cards.append((mod, card))
            else:
                cards.append(('none',query))  # gets the name of the card
        text = text[end+2:]  # cuts out the part with the card
        start = text.find('[[')  # and the circle begins anew
    return cards


def load_core_set():
    '''loads the core set cards from core_set.csv into a dictionary called core_set'''
    core_set = {}
    for card_info in requests.get('https://server.collective.gg/api/public-cards/').json()['cards']:
        if card_info['imgurl'] is not None:
            core_set[card_info['name'].lower()] = card_info['imgurl']
    return core_set



def load_hs():
    cards = {}
    card_data = requests.get('https://api.hearthstonejson.com/v1/25770/enUS/cards.json').json()
    for card in card_data:
        if 'name' not in card:
            continue
        cards[card['name'].lower()] = card['id']
    return cards

def load_from_csv(fname):
    cards = {}
    with open(fname, 'r') as fcard_list:
        card_list = csv.reader(fcard_list, delimiter=',')
        for row in card_list:
            name, link = row
            cards[name.lower()] = link
    return cards

def get_from_set(card,card_set):
    max_ratio = (' ', 0)  # maximum score in ratio exam
    max_partial = (' ', 0)  # maximum sort in partial ratio exam
    list_ratio = []
    list_partial = []
    for entry in card_set:
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
        return "{} wasn't found, please try again".format(card)
    if max_partial[1] > max_ratio[1]:
        return card_set[max_partial[0]]
    return card_set[max_ratio[0]]

def get_mtg(card):
    '''sends a link to an image file of the mtg card'''
    # check scryfall api at scryfall website
    available = requests.get('https://api.scryfall.com/cards/named/', {'fuzzy': card}).json()
    if available['object'] == 'card':
        return 'https://api.scryfall.com/cards/named?fuzzy={};format=image;version=png'.format(card.replace(' ', '%20'))
    return "sorry, couldn't find {}. please try again.".format(card)

def get_ygo(card):
    query = requests.get('https://yugiohprices.com/search_card?search_text=' + card)
    if query:
        return 'https://static-3.studiobebop.net/ygo_data/card_images/{}.jpg'.format(query.url.split('name=')[-1].replace('+', '_').replace('-', '_').replace('%22', '_'))
    else:
        return '{} was not found. please be more specific'.format(card)

def get_top(num, search):
    ret = []
    if num >= 1000:
        return "You requested too many posts at once. please try to ask for less posts next time!"
    # takes the top 1000 cards of this week and sorts them in order of upvotes
    posts = sorted(collective.search(search, limit=1000, sort='top'), key=lambda x: x.score, reverse=True)
    for post in list(filter(lambda x: x.title.lower().startswith('[card'), posts))[:num]:
        ret.append(post.url+' | '+str(post.score)+' | '+str(int(post.upvote_ratio*100))+'%')
    return ret

def get_all_content(table):
    """
    table - the name of the table
    this function return a list of all of the available keys of the table specified
    """
    # this will return a list of tuples of names
    cursor.execute("select name from {}".format(table))
    # this takes the list of tuples and converts it to a list of keys and then sorts it alphabetically
    return sorted(x[0] for x in cursor.fetchall())

# commands
@bot.command()
async def alive():
    await bot.say('im alive and well!')

@bot.command()
async def server():
    await bot.say('https://discordapp.com/api/oauth2/authorize?client_id=465866501715525633&permissions=522304&scope=bot')

@bot.command()
async def github():
    await bot.say('https://github.com/fireasembler/CollectiveCardFetcher')

@bot.command(pass_context=True)
async def nice(ctx):
    await bot.send_file(ctx.message.channel, 'memes/nice art.jpg')

@bot.command()
async def good():
    os.environ['GOOD'] = str(int(os.environ['GOOD']) + 1)
    await bot.say('thank you! :)')

@bot.command()
async def bad():
    os.environ['BAD'] = str(int(os.environ['BAD']) + 1)
    await bot.say('ill try better next time :(')

@bot.command()
async def score():
    await bot.say('good: ' + os.environ.get('GOOD'))
    await bot.say('bad: ' + os.environ.get('BAD'))

@bot.command()
async def new(link):
    cursor.execute("select content from new_command where name=%s", [link])
    fetch = cursor.fetchall()
    if fetch:
        await bot.say(fetch[0][0].replace(r"\n", "\n"))
    else:
        await bot.say("{} isnt a link I can give. the current links are: {}".format(link, ','.join(get_all_content('new_command'))))

@bot.command(pass_context=True)
async def image(ctx, link):
    if link.startswith('https://files.collective.gg/p/cards/'):
        card_id = '-'.join(link.split('/')[-1].split('-')[:-1])
        card_data = requests.get('https://server.collective.gg/api/card/'+card_id).json()
        if len(card_data) > 1:
            for prop in card_data['card']['Text']['Properties']:
                if prop['Symbol']['Name'] == 'PortraitUrl':
                    if os.path.exists('card.png'):
                        os.remove('card.png')
                    with open('card.png', 'wb+') as img:
                        img_link =  requests.get(prop['Expression']['Value'])
                        img.write(img_link.content)
                        await bot.send_file(ctx.message.channel, 'card.png')
        else:
            await bot.say('sorry, card was not found')
    else:
        await bot.say('sorry, but this isnt a link!')

@bot.command(pass_context=True)
async def meme(ctx, link):
    if link == 'list':
        await bot.say(','.join(get_all_content("memes")))
        return
    cursor.execute("select content from memes where name=%s", [link])
    fetch = cursor.fetchall()
    if fetch:
        await bot.send_file(ctx.message.channel, io.BytesIO(fetch[0][0]), filename="meme.png")
    else:
        await bot.say("couldn't find {}".format(link))

@bot.command()
async def leaderboard():
    leaderboard = discord.Embed(title="leaderboard", color=0x00FFFF)
    for spot in requests.get('https://server.collective.gg/api/public/leaderboards').json()['multi']:
        leaderboard.add_field(name='{}) {} {} {}'.format(spot['deck_rank'], spot['username'], spot['elo'],
                                                         spot['hero_name']), value=(spot['deck_rank'])+1, inline=False)
    await bot.say(embed=leaderboard)

@bot.command()
async def code():
    await bot.say("C word alert! The word you are looking for is **blocks**.")

# dev/admin commands
def get_admin(ctx:discord.ext.commands.Context) -> discord.Role:
    '''returns the card fetcher admin role of the server'''
    user:discord.Member = ctx.message.author    
    return discord.utils.get(user.server.roles, name = os.environ.get("MOD_ROLE"))

@bot.command(pass_context=True)
async def say(ctx):
    if ctx.message.author.id == '223876086994436097':
        await bot.delete_message(ctx.message)
        await bot.say(' '.join(ctx.message.content.split(' ')[1:]))
    else:
        await bot.say('YOU CANT CONTROL ME!!!!!!')

@bot.command(pass_context=True)
async def update(ctx):
    global core_set
    if get_admin(ctx) in ctx.message.author.roles:
        core_set = {}
        for card_info in requests.get('https://server.collective.gg/api/public-cards/').json()['cards']:
            if card_info['imgurl'] is not None:
                core_set[card_info['name']] = card_info['imgurl']
        await bot.say('done updating the cards!')

@bot.command(pass_context=True)
async def add(ctx, *args):
    if get_admin(ctx) in ctx.message.author.roles:
        if args[0] == "meme":
            if len(args) == 1:
                await bot.say("you haven't specified a name for the meme!")
            else:
                meme = requests.get(ctx.message.attachments[0]['url']).content
                cursor.execute("insert into memes values(%s,%s,%s)", (args[1], True, meme))
                await bot.say("{} has been added!".format(args[1]))
        else:
            cursor.execute("insert into new_command values(%s,%s,%s)", (args[0], True, args[1:]))
            await bot.say("{} has been added!".format(args[0]))
        db.commit()

@bot.command(pass_context=True)
async def edit(ctx, *args):
    if get_admin(ctx) in ctx.message.author.roles:
        cursor.execute("update new_command set is_file=%s, content=%s where name=%s", (True, args[1:], args[0]))
        db.commit()
        await bot.say("{} has been edited!".format(args[0]))

@bot.command(pass_context=True)
async def remove(ctx, *args):
    if get_admin(ctx) in ctx.message.author.roles:
        is_meme = args[0] == "meme"
        table = "memes" if is_meme else "new_command"
        cursor.execute("delete from {} where name=%s".format(table), [" ".join(args[is_meme:])])
        db.commit()
        await bot.say("{} has been removed!".format(args[is_meme]))

@bot.command()
async def help():
    await bot.say(embed=embed)

# events
@bot.event
async def on_message(message):
    cards = get_card_name(message.content)  # this gets all card names in the message
    links = []  # here are the card links stored
    for card in cards:
        mod, card = card
        if card.lower().startswith('top '):
            card = card.lower()
            if len(card.split(' ')) == 2:  # the name looks like this :"top X"
                num = card.split(' ')[1]
                week = os.environ.get('WEEK')
                links += get_top(int(num), 'flair:(' + week + ')')
            elif len(card.split(' ')) == 4:  # the name looks like this: "top X week Y"
                num = card.split(' ')[1]
                week = card.split(' ')[3]
                if num.isdigit() and week.isdigit():
                    if card.split(' ')[2] == 'week':
                        links += get_top(int(num), 'flair:(' + week + ')')
                    elif card.split(' ')[2] == 'dc':
                        links += get_top(int(num), '[DC' + week)
        else:
            if mod == 'none':
                links.append(get_from_set(card, core_set))
            elif mod == 'sub':
                found = False
                for post in collective.search(card, limit=1):  # this searches the subreddit for the card name with the [card] tag and takes the top suggestion
                    if post.title.startswith('['):
                        links.append(post.url)
                        found = True
                if not found:
                    links.append('{} was not found in the subreddit.'.format(card))
            elif mod == 'mtg':
                links.append(get_mtg(card))
            elif mod == 'sb':
                links.append(get_from_set(card,stormbound_cards))
            elif mod == 'ygo':
                links.append(get_ygo(card))
            elif mod == 'et':
                links.append(get_from_set(card,eternal_cards))
            elif mod == 'hs':
                links.append('https://art.hearthstonejson.com/v1/render/latest/enUS/512x/'+get_from_set(card,hs_cards)+'.png')
            else:
                links.append("the mode you chose is not present at this moment. current mods are: {}".format(','.join(POSSIBLE_MODS)))
    if links:  # if there are any links
        # this loops runs one time plus once for every five links
        # since discord can only display five pictures per message
        for x in range((len(links)//5)+1):
            await bot.send_message(message.channel , '\n'.join(links[5*x:5*(x+1)]))
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction,user):
    if reaction.emoji == '👎' and reaction.message.author == bot.user:
        await bot.delete_message(reaction.message)

#main
core_set = load_core_set()
stormbound_cards = load_from_csv("stormbound.csv")
eternal_cards = load_from_csv("eternal_list.csv")
hs_cards = load_hs()
POSSIBLE_MODS = ['mtg', 'sub', 'sb', 'ygo', 'et', 'hs']
bot.run(os.environ.get('BOT_TOKEN'))
