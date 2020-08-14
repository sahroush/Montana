# bot.py
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
import time, requests, random

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


def fetch(sub, x=0):
    url = makeUrl('', sub)
    subJson = requests.get(url, headers={'User-Agent': 'MyRedditScraper'}).json()
    post = subJson['data']['children']
    if (len(post) < x):
        return (0)
    imageUrl = (post[x]['data']['url'])
    imageTitle = (post[x]['data']['title'])
    if (not ('.jpg' in imageUrl or '.webm' in imageUrl or '.gif' in imageUrl or '.gifv' in imageUrl or '.png' in imageUrl)):
        return (fetch(sub, x + 1))
    else:
        return (imageUrl, imageTitle)
        

@bot.command(name='echo', help='Repeats a given message' , usage = "[message...]")
async def echo(ctx , *response):
    if (len(response) == 0):
        response = ["**I can't send an empty message you fucking idiot**"]
    await ctx.send(" ".join(response))


def fetchrecent(sub, x=0):
    url = makeUrl('', sub)
    subJson = requests.get(url, headers={'User-Agent': 'MyRedditScraper'}).json()
    post = subJson['data']['children']
    try:
        imageUrl = (post[x]['data']['url'])
        imageTitle = (post[x]['data']['title'])
        if (
                not (
                        '.jpg' in imageUrl or '.webm' in imageUrl or '.gif' in imageUrl or '.gifv' in imageUrl or '.png' in imageUrl)):
            return (fetchrecent(sub, x + 1))
        else:
            return (imageUrl, x)
    except:
        return (0, 0)


def getsubsize(sub):
    try:
        url = makeUrl('', sub)
        subJson = requests.get(url, headers={'User-Agent': 'MyRedditScraper'}).json()
        post = subJson['data']['children']
        stuff = []
        for i in range(len(post)):
            imageUrl = (post[i]['data']['url'])
            imageTitle = (post[i]['data']['title'])
            if (('.jpg' in imageUrl or '.webm' in imageUrl or '.gif' in imageUrl or '.gifv' in imageUrl or '.png' in imageUrl)):
                mark = 1;
                stuff += [[imageUrl, imageTitle]]
        return (len(stuff))
    except :
        return (0)

zede_maraz = random.randint(0 , 1 << 62);

@bot.command(name='recent', help='posts the most recent pics from the given subreddit' , usage = "[subreddit...] [cnt = subsize...]")
async def recent(ctx ,sub , cnt =  zede_maraz):
    sub = "https://www.reddit.com/r/" + sub
    sz = getsubsize(sub);
    if (cnt <= 0):
        response = "What did you expect moron"
        await ctx.send(response)
        return
    if(cnt == zede_maraz):
        cnt = sz;
    if(sz == 0):
        response = "Sorry, couldn't find a pic :sob:"
        await ctx.send(response)
        return
    if (cnt > sz):
        await ctx.send("I'm sorry I could only find " + str(sz) + " pics, anyways here you go :blush:")
    cnt = min(cnt, sz)
    x = 0
    while ((0, 0) != fetchrecent(sub, x) and cnt > 0):
        (url, x) = fetchrecent(sub, x)
        x += 1
        cnt -= 1;
        await ctx.send(url)
    return
    

@recent.error
async def recent_error_handler(ctx , error):
    response = "you probably did something idiotic"
    await ctx.send(response)
    

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
    await ctx.send("Montana has been running for " + str(int((time.time() - starting_time) // 60)) + " minutes")


def rnd(sub):
    url = makeUrl('', sub)
    subJson = requests.get(url, headers={'User-Agent': 'MyRedditScraper'}).json()
    post = subJson['data']['children']
    mark = 0
    stuff = []
    for i in range(len(post)):
        imageUrl = (post[i]['data']['url'])
        imageTitle = (post[i]['data']['title'])
        if (('.jpg' in imageUrl or '.webm' in imageUrl or '.gif' in imageUrl or '.gifv' in imageUrl or '.png' in imageUrl)):
            mark = 1;
            stuff += [[imageUrl, imageTitle]]
    if (mark == 0):
        return ("Sorry, couldn't find a pic :sob:");
    x = random.randint(0, len(stuff) - 1);

    return (stuff[x][0])


@bot.command(name='random', help='posts a random pic from the given subreddit', usage = "[subreddit...]")
async def rndom(ctx , sub):
    await ctx.send(rnd("https://www.reddit.com/r/" + sub))

@rndom.error
async def recent_error_handler(ctx , error):
    response = "you probably did something stupid"
    await ctx.send(response)

bot.run(TOKEN)
