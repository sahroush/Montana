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

def ismedia(imageUrl):
    return(('.jpg' in imageUrl or '.webm' in imageUrl or '.gif' in imageUrl or '.gifv' in imageUrl or '.png' in imageUrl))

def fetch(sub):
    url = makeUrl('',"https://www.reddit.com/r/"+sub)
    subJson = requests.get(url, headers={'User-Agent': 'Montana'}).json()
    posts = subJson['data']['children']
    sfw = []
    nsfw = []
    for post in posts:
        ismed = ismedia(post['data']['url'])
        if(ismed and post['data']['over_18']):
            nsfw += [[post['data']['title'] , post['data']['url']]]
        elif(ismed):
            sfw  += [[post['data']['title'] , post['data']['url']]]
    return(sfw , nsfw)


@bot.command(name='echo', help='Repeats a given message' , usage = "[message...]")
async def echo(ctx , *response):
    if (len(response) == 0):
        response = ["**I can't send an empty message you fucking idiot**"]
    await ctx.send(" ".join(response))


zede_maraz = random.randint(0 , 1 << 62);


@bot.command(name='album', help='posts the most recent pics from the given subreddit \n'+
'nsfw is off in sfw channels unless +nsfw is used \n'+
'shuffles posts when +random is used ' ,usage = "<subreddit> [+nsfw][+random]")
async def album(ctx ,sub , *args):
    sfw , nsfw = fetch(sub)
    posts = sfw
    if("+nsfw" in args or ctx.channel.is_nsfw()):
        posts += nsfw
    if(len(posts) == 0):
        response = "Sorry, couldn't find a pic :sob:"
        await ctx.send(response)
        return
    if("+random" in args):
        random.shuffle(posts)
    cur = 0
    message = await ctx.send(posts[0][1]);
    emojis = ["⏪" , "⏩" , "❌"]
    
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in emojis
        
    await message.clear_reactions()
    if(cur > 0):
        await message.add_reaction("⏪")
    if(len(posts)-1 > cur):
        await message.add_reaction("⏩")
    await message.add_reaction("❌")
    
    while(True):
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=10, check=check)
            if str(reaction.emoji) == "⏩":
                cur+=1
                await message.edit(content=posts[cur][1])
                await message.clear_reactions()
                if(cur > 0):
                    await message.add_reaction("⏪")
                if(len(posts)-1 > cur):
                    await message.add_reaction("⏩")
                await message.add_reaction("❌")
                
            if str(reaction.emoji) == "⏪":
                cur-=1
                await message.edit(content=posts[cur][1])
                await message.clear_reactions()
                if(cur > 0):
                    await message.add_reaction("⏪")
                if(len(posts)-1 > cur):
                    await message.add_reaction("⏩")
                await message.add_reaction("❌")
                
            if str(reaction.emoji) == "❌":
                await message.clear_reactions()
                await message.delete()
                await ctx.message.delete()
                return

        except:
            await message.delete()
            await ctx.message.delete()
            return;

    

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

bot.run(TOKEN)
