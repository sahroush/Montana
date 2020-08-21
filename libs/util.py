import textwrap
import discord
import asyncio
import random
import requests
import img2pdf
import os
from PIL import Image #cuz alpha is a bitch


colors = [0, 1752220, 3066993, 3447003, 10181046, 15844367, 15105570, 15158332,
          9807270, 8359053, 3426654, 1146986, 2067276, 2123412, 7419530, 12745742,
          11027200, 10038562, 9936031, 12370112, 2899536, 16580705, 12320855]


def wrapped(s):
    wrapper = textwrap.TextWrapper(width=20)
    word_list = wrapper.wrap(text=s)
    s = ""
    for word in word_list:
        s += '\n' + word
    return s


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


def make_embed(text):
    return discord.Embed(description=str(text), color=colors[random.randint(0, len(colors) - 1)])


async def pagify(bot, ctx, links, names):
    cur = 0
    embed = discord.Embed(title=wrapped(names[cur]), description="", color=colors[random.randint(0, len(colors) - 1)],
                          url=links[cur])
    embed.set_footer(text=str(cur + 1) + "/" + str(len(links)))
    embed.set_image(url=links[cur])

    message = await ctx.send(embed=embed)

    emojis = ["⏪", "⏩", "🗑"]

    def check(reaction, user):
        if user == message.author or reaction.message.id != message.id:  # the reaction was made by the bot itself
            return False
        return True  # made by user || third party

    async def Check(reaction, user):
        await message.remove_reaction(reaction, user)
        return not (user != ctx.author or not (str(reaction) in emojis))

    await message.clear_reactions()
    for emoji in emojis:
        await message.add_reaction(str(emoji))

    async def react(reaction, user):
        nonlocal cur
        if str(reaction.emoji) == "⏩":
            if cur == len(links) - 1:
                return False
            cur += 1
            embed = discord.Embed(title=wrapped(names[cur]), description="", color=242424, url=links[cur])
            embed.set_footer(text=str(cur + 1) + "/" + str(len(links)))
            embed.set_image(url=links[cur])
            await message.edit(embed=embed)
            await message.remove_reaction(reaction, user)

        if str(reaction.emoji) == "⏪":
            if cur == 0:
                return False
            cur -= 1
            embed = discord.Embed(title=wrapped(names[cur]), description="", color=242424, url=links[cur])
            embed.set_footer(text=str(cur + 1) + "/" + str(len(links)))
            embed.set_image(url=links[cur])
            await message.edit(embed=embed)
            await message.remove_reaction(reaction, user)

        if str(reaction.emoji) == "🗑":
            await message.delete()
            await ctx.message.delete()
            return True

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=180, check=check)
            if await Check(reaction, user):
                if await react(reaction, user):
                    break
        except asyncio.TimeoutError:
            await message.clear_reactions()
            break
        except:
            break




async def upload(name):
    best_server = requests.get('https://apiv2.gofile.io/getServer').json()
    server = best_server['data']['server']
    files = {
        'file': (name, open(name, 'rb') , "application/pdf")
    }
    response = requests.post('https://'+server+\
     '.gofile.io/uploadFile', files=files).json()['data']['code']
    return("https://gofile.io/?c="+response)


cnt = 0


async def makepdf(links , name): # low memory usage but slow
    images = []
    img_num = 1
    for link in links:
        response = requests.head(link, allow_redirects=True)
        size = int(response.headers.get('content-length', -1))
        if size < 5000000:
            img = Image.open(requests.get(link, stream=True).raw).convert('RGB')
            img.save(name + str(img_num) + ".png") #won't matter as long as it's an image format
            img.close()
            images.append(name + str(img_num) + ".png")
            img_num+=1

    filename = f'{name}_{img_num}.pdf'
    pdf = open(filename , "wb")
    pdf.write(img2pdf.convert(images))
    pdf.close()
    for i in images:
        os.remove(i)
    return(filename)
    
async def fastmakepdf(links , name): # super high memory usage but fast
    images = []
    for link in links:
        response = requests.head(link, allow_redirects=True)
        size = int(response.headers.get('content-length', -1))
        if size < 5000000:
            images.append(Image.open(requests.get(link, stream=True).raw).convert('RGB'))
    filename = f'{name}.pdf'
    images[0].save(filename, save_all=True, append_images=images[1:])
    for i in images:
        i.close()
    return(filename)
    
async def send_pdf(ctx, name, links):
    originalname = name
    loading = await ctx.send(file=discord.File('libs/files/loading.gif'))
    global cnt
    while cnt >= 9:
        await asyncio.sleep(2)
    cnt += 1
    name += str(random.randint(0, 1000000000))
    if(len(links) > 50 ) :
        filename = await makepdf(links , name)
    else :
        filename = await fastmakepdf(links , name)
    url = await upload(filename)
    embed = discord.Embed(title=originalname, description="", color=colors[random.randint(0, len(colors) - 1)],
                          url=url)
    await ctx.send(embed = embed)
    os.remove(filename)
    await loading.delete()
    cnt -= 1
