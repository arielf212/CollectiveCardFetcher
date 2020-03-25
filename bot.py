import reddit, database
import fetcher.collective, fetcher.eternal, fetcher.mtg, fetcher.ygo, fetcher.hs
import discord, requests
from PIL import Image
from discord.ext import commands
import re, os, io

# global variables
bot = commands.Bot(command_prefix="!")
collective_sub = reddit.CollectiveSub()

# database connections
try:
    db = database.Database(os.environ.get("DATABASE_URL"))
    new_command_table = database.TableWrapper(db, "new_command", "name", "content")
    memes_table = database.TableWrapper(db, "memes", "name", "content")
    admins_table = database.TableWrapper(db, "admins", "user_id", "privileges")
except:
    print("db off")
 
# This is the fetcher dict. when a search modifier is specified,
# the bot looks here for the right fetcher to use.
# if you are extending this bot, add your fetcher through here.
# a fetcher class must have a __getitem__ method that returns a string
# on success and KeyError on failure.
# if you want to override the default search, override the value of the key "none".

card_fetchers = {
    "none": fetcher.collective.CollectiveFetcher(),
    "tk": fetcher.collective.CollectiveTokenFetcher(),
    "coll": fetcher.collective.CollectiveAnyFetcher(),
    "sub": collective_sub,
    "mtg": fetcher.mtg.MtgFetcher(),
    "et": fetcher.eternal.EternalFetcher(),
    "ygo": fetcher.ygo.YugiohFetcher(),
    'hs': fetcher.hs.HsFetcher()
}

# editing the "!help" command, to actually become... helpful :P 
embed = discord.Embed(title="CollectiveCardFetcher Help", description="here is a list of commands for the bot:", color=0x00FFFF)
embed.add_field(name='!alive', value='The bot will respond with "im alive and well!"')
embed.add_field(name='!server', value="The bot will respond with a link that can be used to add him to a server. note: you need to be an admin in a server to add a bot.")
embed.add_field(name='!github', value="The bot will respond with a link to the github page of the bot.")
embed.add_field(name='!good', value='Ups the score of the bot. Will make the bot respond with a thankful message.')
embed.add_field(name='!bad', value='Reduces the score of the bot. Will make the bot respond with an apologetic message.')
embed.add_field(name='!score', value='The bot will respond with the amount of votes given to him trough !bad and !good')
embed.add_field(name='!image <link>', value='Will return the art of the card linked.')
embed.add_field(name='!concat "card name that is in the game, use _ for spaces" "link for update"', value="creates a cool infographic that shows the update")
embed.add_field(name='!new', value='Takes a topic and returns an explanation about it')
embed.add_field(name="!meme", value="Takes a name and returns a meme saved under that name")
embed.add_field(name='!leaderboard', value='Responds with an embed holding the value of the current leaderboard.')
bot.remove_command('help')

# functions
def get_card_name(text):
    """
    takes a string and extracts card names from it. 
    card names are encapsulated in [[xxxx]] where xxxx is the card name.
    """

    cards = []  # list of names of cards
    start = text.find('[[')
    while start != -1:  # until there are no more brackets
        end = text.find(']]')
        # if there is an opener but no closer then we skip it
        if end != -1:
            query = text[start + 2:end]
            if query.find(':') > 0:
                mod = query[:query.find(':')].lower()
                card = query[query.find(':')+1:].lstrip(' ')
                if mod not in card_fetchers:
                    card = query
                    mod = 'none'
                cards.append((mod, card))
            else:
                cards.append(('none',query))  # gets the name of the card
        text = text[end+2:]  # cuts out the part with the card
        start = text.find('[[')  # and the circle begins anew
    return cards

def get_top_sub(request):
    """
    gets the top carss of the week based on the request given.
    """

    request = request.lower()
    week_types = ['week', 'preseason']
    top_types = week_types + ['dc', 'update']
    # the form is: "top <num> (<type> (<num>)?)?"
    request_group = re.match(
        "top ([0-9]+)(?: ({})(?: ([0-9]+))?)?".format('|'.join(top_types)),
        request
    )
    if request_group is not None: # if the request was valid
        num, search_type, week = request_group.groups()
        if week is None:
            week = os.environ.get("WEEK")
        if search_type is None:
            search_type = week_types[-1]
        if search_type in week_types:
            if search_type == 'week':
                week = f"week {week}"
            else:
                week = f"{search_type} week {week}"
            week = f'"{week}"'
        if search_type in week_types:
            search_type = 'card'
        return collective_sub.get_top(int(num), '['+search_type, week)
    else: raise ValueError("Request wasn't valid")

def is_admin(user_id):
    return user_id in admins_table


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
    await bot.send_file(ctx.message.channel, 'images/nice_art.jpg')


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
    if link in new_command_table:
        await bot.say(new_command_table[link].replace(r"\n", "\n"))
    else:
        await bot.say("{} isnt a link I can give. the current links are: {}".format(
            link,
            ','.join(new_command_table.get_all_keys())
            ))


@bot.command(pass_context=True)
async def image(ctx, link):
    if link.startswith('https://files.collective.gg/p/cards/'):
        card_id = '-'.join(link.split('/')[-1].split('-')[:-1])
        card_data = requests.get('https://server.collective.gg/api/card/'+card_id).json()
        if len(card_data) > 1:
            for prop in card_data['card']['Text']['Properties']:
                if prop['Symbol']['Name'] == 'PortraitUrl':
                    img = requests.get(prop['Expression']['Value']).content
                    await bot.send_file(ctx.message.channel, io.BytesIO(img), filename='card.png')
        else:
            await bot.say('sorry, card was not found')
    else:
        await bot.say('sorry, but this isnt a link!')


# this was done by OWN3D
# thank you very much! ^^
@bot.command(pass_context=True)
async def concat(ctx,*args):
    ori_card, link = args
    if link.startswith('https://files.collective.gg/p/cards/'):
        try:
            ori_card = ori_card.replace("_", " ")
            ori_link = card_fetchers['coll'][ori_card]

            images = []
            response = requests.get(ori_link)
            images.append(Image.open(io.BytesIO(response.content)))

            images.append(Image.open('images/arrow.png'))

            response = requests.get(link)
            images.append(Image.open(io.BytesIO(response.content)))

            widths, heights = zip(*(i.size for i in images))
            total_width = sum(widths)
            max_height = max(heights)

            new_im = Image.new('RGB', (total_width, max_height))

            x_offset = 0
            for im in images:   
               new_im.paste(im, (x_offset,0))
               x_offset += im.size[0]
            new_im.save("trash/update.png", "png")
            await bot.send_file(ctx.message.channel, "trash/update.png", filename="update.png")
        except Exception as e:
            await bot.say('card not found!')
            raise e
    else:
        await bot.say('sorry, but this isnt a link!')


@bot.command(pass_context=True)
async def meme(ctx, link):
    if link == 'list':
        await bot.say(','.join(memes_table.get_all_keys()))
        return
    if link in memes_table:
        await bot.send_file(ctx.message.channel, io.BytesIO(memes_table[link]), filename="meme.png")
    else:
        await bot.say("couldn't find {}".format(link))


@bot.command()
async def leaderboard():
    leaderboard = discord.Embed(title="leaderboard", color=0x00FFFF)
    for spot in requests.get('https://server.collective.gg/api/public/leaderboards').json()['multi']:
        leaderboard.add_field(
            name='{}) {} {} {}'.format(
                spot['deck_rank'],
                spot['username'],
                spot['elo'],
                spot['hero_name']
            ),
            value=(spot['deck_rank'])+1,
            inline=False
        )
    
    await bot.say(embed=leaderboard)

@bot.command()
async def code():
    await bot.say("C word alert! The word you are looking for is **blocks**.")


# dev/admin commands
def get_admin(ctx:discord.ext.commands.Context) -> discord.Role:
    '''returns the card fetcher admin role of the server'''
    user = ctx.message.author
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
    for fetcher in card_fetchers:
        fetcher.__init__()
    await bot.say('done updating the cards!')


@bot.command(pass_context=True)
async def add(ctx, *args):
    if is_admin(ctx.message.author.id):
        if args[0] == "meme":
            if len(args) == 1:
                await bot.say("you haven't specified a name for the meme!")
            else:
                meme = requests.get(ctx.message.attachments[0]['url']).content
                memes_table[args[1]] = meme
                await bot.say("{} has been added!".format(args[1]))
        else:
            new_command[args[0]] = ' '.join(args[1:])
            await bot.say("{} has been added!".format(args[0]))


@bot.command(pass_context=True)
async def remove(ctx, *args):
    if is_admin(ctx.message.author.id):
        if args[0] == "meme":
            if len(args) == 1:
                await bot.say("you haven't specified a name for the meme!")
            memes_table.remove(args[1])
            await bot.say("{} has been removed!".format(args[1]))
        else:
            new_command_table.remove(args[0])
            await bot.say("{} has been removed!".format(args[0]))


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
        if card.lower().startswith('top '):  # if the search asks for the top X
            try:
                links += get_top_sub(card)
            except ValueError as e:
                links.append(e.args[0])
        elif mod in card_fetchers:
            try:
                links.append(card_fetchers[mod][card])
            except KeyError:
                links.append("could not find {}".format(card))
        else:
            links.append("{} is not a supported search modifier".format(mod))
    if links:  # if there are any links
        # this loops runs one time plus once for every five links
        # since discord can only display five pictures per message
        for x in range((len(links)//5)+1):
            await bot.send_message(message.channel , '\n'.join(links[5*x:5*(x+1)]))
    await bot.process_commands(message)


@bot.event
async def on_reaction_add(reaction, user):
    """
    deletes any message written by the bot.
    """
    if reaction.emoji == '👎' and reaction.message.author == bot.user:
        await bot.delete_message(reaction.message)


bot.run(os.environ.get('BOT_TOKEN'))
