# bot.py
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
import time , requests  , random

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='^')

@bot.event
async def on_ready():
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
    print(response)
    if(len(response) == 0):
        response = "I can't send an empty message you fucking idiot"
    await ctx.send(response)

@bot.command(name='bigms' , help='Responds with BIGMS')
async def bigms(ctx):
    response = "https://cdn.discordapp.com/attachments/740975196558590073/743150977691156660/insta.gif.mp4"
    await ctx.send(response)

bot.run(TOKEN)
