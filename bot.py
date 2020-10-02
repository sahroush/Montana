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


@bot.command(name='meow', help='posts the most recent pics from a random cat related subreddit \n'
                                'shuffles posts when +random is used',
             usage="[+random]")
async def album(ctx, *args):
    subs = ["cats" , "catsonglass" , "catsstandingup" , "catsonpizza"  , "catsvstechnology" , "illegallysmolcats" , "medievalcats" ,
    "notmycat"  , "meow_irl" , "CatSpotting" , "GrumpyCats" , "Kitty" , "Kitten" , "Kittens" , "SeniorCats" , "illegallybigcats",
    "sadcats" , "cutecats" , "wetcats" , "displeasedkitties" , "sleepingcats" , "KittenGifs"]
    sub = random.choice(subs)
    sfw = fetch(sub)
    posts = sfw
    if not posts:
        response = "no pics found in " + sub
        await ctx.send(response)
        return
    if "+random" in args:
        random.shuffle(posts)
    links = []
    names = []
    for i in posts:
        links += [i[1]]
        names += ["/r/"+sub]
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
