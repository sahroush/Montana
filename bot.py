import time
from discord import Status
from discord.ext import commands
from libs.reddit import *
from libs.util import *

TOKEN = os.getenv("TOKEN")

bot = commands.Bot(command_prefix='>')
STATUS = Status.online
starting_time = time.time()


@bot.event
async def on_ready():
    global starting_time
    starting_time = time.time()
    await bot.change_presence(activity=discord.Game(name="Use >help!"))
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='meow', help='posts the most recent pics from the a random cat related subreddit \n'
                                'shuffles posts when +random is used',
             usage="[+random]")
async def album(ctx, *args):
    subs = ["cats" , "catsonglass" , "catsstandingup" , "catsonpizza" , "startledcats" , "catsvstechnology" , "illegallysmolcats" , "medievalcats" ,
    "notmycat" , "petthedamncat" , "meow_irl" , "CatSpotting" , "GrumpyCats" , "Kitty" , "Kitten" , "Kittens" , "SeniorCats" , "illegallybigcats",
    "sadcats" , "cutecats" , "wetcats" , "displeasedkitties" , "sleepingcats" , "KittenGifs"]
    sub = random.choice(subs)
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


@bot.event
async def on_command_error(ctx, error):
    if STATUS is Status.invisible:
        return
    await ctx.send(embed=make_embed(error))


bot.run(TOKEN)
