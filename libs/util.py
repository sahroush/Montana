import asyncio
import os
import random
import textwrap

import discord
import img2pdf
import requests
from PIL import Image  # cuz alpha is a bitch

colors = [0, 1752220, 3066993, 3447003, 10181046, 15844367, 15105570, 15158332,
          9807270, 8359053, 3426654, 1146986, 2067276, 2123412, 7419530, 12745742,
          11027200, 10038562, 9936031, 12370112, 2899536, 16580705, 12320855]


def wrapped(s):
    wrapper = textwrap.TextWrapper(width=32)
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


async def upload(name):
    best_server = requests.get('https://apiv2.gofile.io/getServer').json()
    server = best_server['data']['server']
    files = {
        'file': (name, open(name, 'rb'), "application/pdf")
    }
    response = requests.post('https://' + server + \
                             '.gofile.io/uploadFile', files=files).json()['data']['code']
    return "https://gofile.io/?c=" + response


async def makepdf(links, name):  # low memory usage but slow af
    images = []
    img_num = 1
    for link in links:
        response = requests.head(link, allow_redirects=True)
        size = int(response.headers.get('content-length', -1))
        if size < 5000000:
            img = open(name + str(img_num) + ".wtf", "wb")
            img.write(requests.get(link).content)
            img.close()
            images.append(name + str(img_num) + ".wtf")
            img_num += 1
    filename = f'{name}_{img_num}.pdf'
    pdf = open(filename, "wb")
    pdf.write(img2pdf.convert(images))
    pdf.close()
    for i in images:
        os.remove(i)
    return filename


async def fastmakepdf(links, name):  # super high memory usage but fast
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
    return filename


_pdfsem = asyncio.Semaphore(5)
async def send_pdf(ctx, name, links):
    if len(name) > 25:
        name = name[:20]
    originalname = name
    loading = await ctx.send(file=discord.File('libs/files/loading.gif'))
    async with _pdfsem:
        name += str(random.randint(0, 1000000000))
        if len(links) > 50:
            filename = await makepdf(links, name)
        else:
            filename = await fastmakepdf(links, name)
        url = await upload(filename)
        embed = discord.Embed(
            title=originalname,
            description="",
            color=colors[random.randint(0, len(colors) - 1)],
            url=url
        )
        await ctx.send(embed=embed)
        os.remove(filename)
        await loading.delete()


def fib(n):
    a, b = 0, 1
    for i in range(n):
        a, b = b, a + b
    return a


def has_any_strrole(seq, *roles):
    return any(r.name in roles for r in seq)


def filter_bots(members):
    return [m for m in members if not m.bot]
