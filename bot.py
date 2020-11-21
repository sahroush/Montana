import time
import pytz
from datetime import datetime
from discord import Status
from discord.ext import commands
from libs.reddit import *
from libs.util import *
from libs.nhentaiparser import *

TOKEN = os.getenv("TOKEN")

bot = commands.Bot(command_prefix=commands.when_mentioned_or('`'))
STATUS = Status.online
starting_time = time.time()

localtz = pytz.timezone("Asia/Tehran")


@bot.event
async def on_ready():
    global starting_time
    starting_time = time.time()
    await bot.change_presence(activity=discord.Game(name="Use `help!"))
    print(f'{bot.user.name} has connected to Discord!')


@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(f'Hi {member.name}, welcome to our Discord server!')


@bot.command(name='echo', help='Repeats a given message', usage="[message...]")
async def echo(ctx, *response):
    if not response:
        response = ["**I can't send an empty message you fucking idiot**"]
    await ctx.send(" ".join(response))


@bot.command(name='album', help='posts the most recent pics from the given subreddit \n'
                                'nsfw is off in sfw channels unless +nsfw is used \n'
                                'shuffles posts when +random is used'
                                'sends a pdf instead of an album when +pdf is used',
             usage="<subreddit> [+nsfw][+random][+pdf]")
async def album(ctx, sub, *args):
    sfw, nsfw = fetch(sub, "+pdf" in args)  # pdf ==> no gifs
    posts = sfw
    if ctx.channel.type is discord.ChannelType.private and "+pdf" not in args:
        response = "Sorry, this command is not available in DMs :sob:"
        await ctx.send(response)
        return
    if "+nsfw" in args or (ctx.channel.type is not discord.ChannelType.private and ctx.channel.is_nsfw()):
        posts += nsfw
    if not posts:
        response = "Sorry, couldn't find a pic :sob:"
        await ctx.send(response)
        return
    if "+random" in args:
        random.shuffle(posts)
    links = []
    names = []
    for i in posts:
        links += [i[1]]
        names += [i[0]]
    if "+pdf" in args:
        await send_pdf(ctx, sub, links)
    else:
        await pagify(bot, ctx, links, names)


@bot.command(name='nhentai',
             help='posts the given sauce \n'
                  'nsfw is off in sfw channels unless +nsfw is used \n'
                  'sends a pdf instead of an album when +pdf is used',
             usage="<source number> [+nsfw][+pdf]", hidden=True)
async def nhentai(ctx, sixdigit: int, *args):
    posts, name = fetch_hentai(sixdigit)
    if ctx.channel.type is discord.ChannelType.private and "+pdf" not in args:
        response = "Sorry, this command is not available in DMs :sob:"
        await ctx.send(response)
        return
    if not ("+nsfw" in args or ctx.channel.is_nsfw()):
        response = "Sorry, this commnd will only work either when used in a nsfw channel or with +nsfw tag used"
        await ctx.send(response)
        return
    if not posts:
        response = "Sorry, couldn't find a Doujin :sob:"
        await ctx.send(response)
        return
    names = [name] * len(posts)
    if "+pdf" in args:
        await send_pdf(ctx, name, posts)
    else:
        await pagify(bot, ctx, posts, names)


@bot.command(name='ping', help="Used to test Montana's response time.")
async def ping(ctx):
    start = time.perf_counter()
    message = await ctx.send(':ping_pong: Pong!')
    end = time.perf_counter()
    duration = (end - start) * 1000
    await message.edit(content=f'REST API latency: {int(duration)}ms\n'
                               f'Gateway API latency: {int(bot.latency * 1000)}ms')


@bot.command(name='uptime', help="Prints bot uptime")
async def uptime(ctx):
    global starting_time
    await ctx.send('Montana has been running for ' + pretty_time_format(time.time() - starting_time))


@bot.command(name="dokme", help="Toggle status", aliases=['lurk'], hidden=True)
@commands.has_role('Admin')
async def dokme(ctx):
    global STATUS
    if STATUS is Status.invisible:
        STATUS = Status.online
        await ctx.send(embed=make_embed("I am online now"))
    elif STATUS is Status.online:
        STATUS = Status.invisible
        await ctx.send(embed=make_embed("Pushed dokme successfully"))
    await bot.change_presence(status=STATUS, activity=discord.Game(name="Use `help!"))


@bot.command(name="remind", brief="Set a reminder", usage="hh:mm[:ss] <message>")
async def remind(ctx, finish: str, *msg):
    """Set a reminder to echo <message> at given time.
    You may mention some role in your message"""

    hour, minute, *second = list(map(int, finish.split(":")))
    second = second[0] if second else 0
    if not (0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60):
        raise ValueError("Given time is not formatted properly")

    now = datetime.now(localtz)
    when = localtz.localize(datetime(year=now.year, month=now.month, day=now.day,
                                     hour=hour, minute=minute, second=second))
    if when < now:
        return await ctx.send("Time travel?")

    msg = ' '.join(msg)
    await ctx.message.delete()
    await ctx.send(embed=make_embed(f"<@{ctx.author.id}> set a reminder at {finish}, \"{msg}\""))
    delta = when - now
    await asyncio.sleep(delta.total_seconds())
    await ctx.send(msg)


@bot.event
async def on_command_error(ctx, error):
    if STATUS is Status.invisible:
        return
    if isinstance(error, commands.CommandNotFound):
        return await ctx.message.add_reaction('\U0001F928')
    await ctx.send(embed=make_embed(error))


bot.run(TOKEN)
