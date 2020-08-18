import time
import os
import discord
from discord import Status
from discord.ext import commands
from libs.reddit import *
from libs.util import *
from libs.nhentai import *

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    TOKEN = "Njk5NTk5MzkwNDMxNzcyNzMz" + ".XpWutA.0nvimxpX" + "AW7uNlwRD" + "wW1aok8Zvw"  # The most idiotic idea

bot = commands.Bot(command_prefix='`')
STATUS = Status.online
starting_time = time.time()


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


@bot.command(name='album', help='posts the most recent pics from the given subreddit \n' +
                                'nsfw is off in sfw channels unless +nsfw is used \n' +
                                'shuffles posts when +random is used ', usage="<subreddit> [+nsfw][+random]")
async def album(ctx, sub, *args):
    sfw, nsfw = fetch(sub)
    posts = sfw
    if ctx.channel.type is discord.ChannelType.private:
        response = "Sorry, this command is not available in DMs :sob:"
        await ctx.send(response)
        return
    if "+nsfw" in args or ctx.channel.is_nsfw():
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
    await pagify(bot, ctx, links, names)


@bot.command(name='nhentai',
             help='posts the given sauce \n' +
                  'nsfw is off in sfw channels unless +nsfw is used \n',
             usage="<source number> [+nsfw]")
async def nhentai(ctx, sixdigit: int, *args):
    posts, name = fetch_hentai(sixdigit)
    if ctx.channel.type is discord.ChannelType.private:
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


@bot.command(name="dokme", help="Toggle status", aliases=['lurk'])
@commands.has_role('Admin')
async def dokme(ctx):
    global STATUS
    if STATUS is Status.invisible:
        STATUS = Status.online
        await bot.change_presence(status=STATUS)
        await ctx.send(embed=make_embed("I am online now"))
    elif STATUS is Status.online:
        STATUS = Status.invisible
        await ctx.send(embed=make_embed("Pushed dokme successfully"))
    await bot.change_presence(status=discord.Status.invisible, activity=discord.Game(name="Use `help!"))


@bot.event
async def on_command_error(ctx, error):
    if STATUS is Status.invisible:
        return
    await ctx.send(embed=make_embed(error))


bot.run(TOKEN)
