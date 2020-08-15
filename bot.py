# bot.py

import random
import textwrap
import time

import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = "Njk5NTk5MzkwNDMxNzcyNzMz" + ".XpWutA.0nvimxpX" + "AW7uNlwRD" + "wW1aok8Zvw"

bot = commands.Bot(command_prefix='`')

starting_time = time.time()


@bot.event
async def on_ready():
    starting_time = time.time()
    await bot.change_presence(activity=discord.Game(name="with my balls"))
    print(f'{bot.user.name} has connected to Discord!')


@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(f'Hi {member.name}, welcome to our Discord server!')


def makeUrl(afterID, subreddit):
    return subreddit.split('/.json')[0] + "/.json?after={}".format(afterID)


def ismedia(imageUrl):
    return ('.jpg' in imageUrl or
            '.webm' in imageUrl or
            '.gif' in imageUrl or
            '.png' in imageUrl) and not '.gifv' in imageUrl


def fetch(sub):
    url = makeUrl('', "https://www.reddit.com/r/" + sub)
    subJson = requests.get(url, headers={'User-Agent': 'Montana'}).json()
    sfw = []
    nsfw = []
    try:
        posts = subJson['data']['children']
        for post in posts:
            ismed = ismedia(post['data']['url'])
            if ismed and post['data']['over_18']:
                nsfw += [[post['data']['title'], post['data']['url']]]
            elif ismed:
                sfw += [[post['data']['title'], post['data']['url']]]
    except:
        pass
    return sfw, nsfw


@bot.command(name='echo', help='Repeats a given message', usage="[message...]")
async def echo(ctx, *response):
    if not response:
        response = ["**I can't send an empty message you fucking idiot**"]
    await ctx.send(" ".join(response))


def wrapped(s):
    wrapper = textwrap.TextWrapper(width=45)
    word_list = wrapper.wrap(text=s)
    s = ""
    for word in word_list:
        s += '\n' + word
    return s


@bot.command(name='album', help='posts the most recent pics from the given subreddit \n' +
                                'nsfw is off in sfw channels unless +nsfw is used \n' +
                                'shuffles posts when +random is used ', usage="<subreddit> [+nsfw][+random]")
async def album(ctx, sub, *args):
    sfw, nsfw = fetch(sub)
    posts = sfw
    if "+nsfw" in args or ctx.channel.is_nsfw():
        posts += nsfw
    if not posts:
        response = "Sorry, couldn't find a pic :sob:"
        await ctx.send(response)
        return
    if "+random" in args:
        random.shuffle(posts)
    cur = 0
    sub = "https://www.reddit.com/r/" + sub
    embed = discord.Embed(title=wrapped(posts[cur][0]), description="", color=242424, url=posts[cur][1])
    embed.set_footer(text=str(cur + 1) + "/" + str(len(posts)))
    embed.set_image(url=posts[cur][1])

    message = await ctx.send(embed=embed)

    emojis = ["⏪", "⏩", "🗑"]

    def check(reaction, user):
        if user == message.author:  # the reaction was made by the bot itself
            return False
        return True  # made by user || third party

    async def Check(reaction, user):
        await message.remove_reaction(reaction, user)
        return not (user != ctx.author or not (str(reaction) in emojis))

    await message.clear_reactions()
    for emoji in emojis:
        await message.add_reaction(str(emoji))

    async def react(reaction, user):
        global cur
        if str(reaction.emoji) == "⏩":
            if cur == len(posts) - 1:
                return
            cur += 1
            embed = discord.Embed(title=wrapped(posts[cur][0]), description="", color=242424, url=posts[cur][1])
            embed.set_footer(text=str(cur + 1) + "/" + str(len(posts)))
            embed.set_image(url=posts[cur][1])
            await message.edit(embed=embed)
            await message.remove_reaction(reaction, user)

        if str(reaction.emoji) == "⏪":
            if cur == 0:
                return
            cur -= 1
            embed = discord.Embed(title=wrapped(posts[cur][0]), description="", color=242424, url=posts[cur][1])
            embed.set_footer(text=str(cur + 1) + "/" + str(len(posts)))
            embed.set_image(url=posts[cur][1])
            await message.edit(embed=embed)
            await message.remove_reaction(reaction, user)

        if str(reaction.emoji) == "🗑":
            await message.delete()
            await ctx.message.delete()
            return

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=10, check=check)
            if await Check(reaction, user):
                await react(reaction, user)
        except:
            await message.clear_reactions()
            return


@album.error
async def album_error_handler(ctx, error):
    await ctx.send(error)


@bot.command(name='ping', help="Used to test Montana's response time.")
async def ping(ctx):
    start = time.perf_counter()
    message = await ctx.send(':ping_pong: Pong!')
    end = time.perf_counter()
    duration = (end - start) * 1000
    await message.edit(content=f'REST API latency: {int(duration)}ms\n'
    f'Gateway API latency: {int(bot.latency * 1000)}ms')


def time_format(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return days, hours, minutes, seconds


def pretty_time_format(seconds, *, shorten=False, only_most_significant=False, always_seconds=False):
    days, hours, minutes, seconds = time_format(seconds)
    timespec = [
        (days, 'day', 'days'),
        (hours, 'hour', 'hours'),
        (minutes, 'minute', 'minutes'),
    ]
    timeprint = [(cnt, singular, plural) for cnt, singular, plural in timespec if cnt]
    if not timeprint or always_seconds:
        timeprint.append((seconds, 'second', 'seconds'))
    if only_most_significant:
        timeprint = [timeprint[0]]

    def format_(triple):
        cnt, singular, plural = triple
        return f'{cnt}{singular[0]}' if shorten else f'{cnt} {singular if cnt == 1 else plural}'

    return ' '.join(map(format_, timeprint))


@bot.command(name='uptime', help="Prints bot uptime")
async def uptime(ctx):
    await ctx.send('Montana has been running for ' + pretty_time_format(time.time() - starting_time))


bot.run(TOKEN)
