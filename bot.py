# bot.py
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
import time , requests  , random

load_dotenv()
TOKEN = "Njk5NTk5MzkwNDMxNzcyNzMz" + ".XpWutA.0nvimxpX" + "AW7uNlwRD"+"wW1aok8Zvw"

bot = commands.Bot(command_prefix='^')

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

def fetch(sub , x = 0):
    url = makeUrl('', sub)
    subJson = requests.get(url, headers={'User-Agent': 'MyRedditScraper'}).json()
    post = subJson['data']['children']
    if(len(post) < x):
        return(0)
    imageUrl = (post[x]['data']['url'])
    imageTitle = (post[x]['data']['title'])
    if(not('jpg' in imageUrl or 'webm' in imageUrl or 'gif' in imageUrl or 'gifv' in imageUrl or 'png' in imageUrl)):
        return(fetch(sub , x + 1))
    else :
        return(imageUrl , imageTitle)

@bot.command(name='latest' , help='posts the most recent pic in the given subreddit')
async def latest(ctx):
    response = (ctx.message.content[7:]).strip()
    if(len(response) == 0):
        response = "I can't do anything with an empty message you fucking idiot"
        await ctx.send(response)
        return
    else:
        try:
            (url  , title ) = fetch("https://www.reddit.com/r/"+ response)
            response = url;
        except:
            response = "Sorry, couldn't find a pic :sob:"
    await ctx.send(response)

@bot.command(name='echo' , help='Repeats a given message')
async def echo(ctx):
    response = (ctx.message.content[5:]).strip()
    if(len(response) == 0):
        response = "I can't send an empty message you fucking idiot"
    await ctx.send(response)

def fetchrecent(sub , x = 0):
    url = makeUrl('', sub)
    subJson = requests.get(url, headers={'User-Agent': 'MyRedditScraper'}).json()
    post = subJson['data']['children']
    try : 
        imageUrl = (post[x]['data']['url'])
        imageTitle = (post[x]['data']['title'])
        if(not('jpg' in imageUrl or 'webm' in imageUrl or 'gif' in imageUrl or 'gifv' in imageUrl or 'png' in imageUrl)):
            return(fetchrecent(sub , x + 1))
        else :
            return(imageUrl , x)
    except : 
        return(0 , 0)

@bot.command(name='recent' , help='posts the recent pics in the given subreddit')
async def recent(ctx):
    response = (ctx.message.content[7:]).strip()
    if(len(response) == 0):
        response = "I can't do anything with an empty message you fucking idiot"
        await ctx.send(response)
        return
    elif ((0 , 0 )!= fetchrecent("https://www.reddit.com/r/"+ response)):
        x = 0;
        while((0 , 0 )!= fetchrecent("https://www.reddit.com/r/"+ response , x)):
            (url  , x ) = fetchrecent("https://www.reddit.com/r/"+ response , x)
            x+=1
            await ctx.send(url)
        return
    else:
        response = "Sorry, couldn't find a pic :sob:"
        await ctx.send(response)
        
@bot.command(name='ping' , help="Used to test Montana's response time.")
async def ping(ctx):
    await ctx.send(f'Pong! {round (bot.latency * 1000)}ms ')

@bot.command(name='uptime' , help="Prints bot uptime")
async def uptime(ctx):
    await ctx.send("Montana has been running for " + str(int((time.time() - starting_time)//60)) + " minutes")

bot.run(TOKEN)
