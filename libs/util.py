import asyncio
import os
import random
import textwrap
import tempfile

import aiohttp
import aiofiles
import discord
import img2pdf
import requests # keep for backward compatibility
from zipstream import AioZipStream
from PIL import Image  # cuz alpha is a bitch

colors = [0, 1752220, 3066993, 3447003, 10181046, 15844367, 15105570, 15158332,
          9807270, 8359053, 3426654, 1146986, 2067276, 2123412, 7419530, 12745742,
          11027200, 10038562, 9936031, 12370112, 2899536, 16580705, 12320855]


def with_session(func):
    async def wrapper(*args, **kwargs):
        async with aiohttp.ClientSession(headers={"User-Agent": "Montana/1.0"}) as session:
            result = await func(session, *args, **kwargs)
        return result
    return wrapper


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
    return discord.Embed(description=str(text), color=random.choice(colors))


async def filesender(file_name=None):
    async with aiofiles.open(file_name, 'rb') as f:
        chunk = await f.read(64*1024)
        while chunk:
            yield chunk
            chunk = await f.read(64*1024)


@with_session
async def upload(session, name):
    async with session.get('https://apiv2.gofile.io/getServer') as resp:
        data = await resp.json()
        server = data['data']['server']
    upload_uri = f'https://{server}.gofile.io/uploadFile'
    postdata = aiohttp.FormData()
    postdata.add_field(
        'file',
        filesender(name),
        filename=name,
        content_type='application/pdf'
    )
    async with session.post(upload_uri, data=postdata) as resp:
        data = await resp.json()
        code = data['data']['code']
    return f"https://gofile.io/?c={code}"


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


@with_session
async def async_makepdf(session, links, name):
    with tempfile.TemporaryDirectory() as tempdir:
        files = []
        for i, link in enumerate(links):
            async with session.head(link, allow_redirects=True) as resp:
                size = int(resp.headers.get('Content-Length', -1))
            if size > 5e6:  # 5 MB
                continue
            image_filename = f'{tempdir}/{i}.idk'
            async with session.get(link) as resp:
                content = await resp.content.read()
            imgio = img2pdf.BytesIO(content)
            image = Image.open(imgio).convert('RGB')
            # Unknown ExifOrientationError on PNG format
            image.save(image_filename, format='JPEG')
            files.append(image_filename)
        filename = f'{name}.pdf'
        async with aiofiles.open(filename, mode='wb') as file:
            await file.write(img2pdf.convert(files))
    return filename


async def write_zipfile(zipfile, files):
    # larger chunk size will increase performance
    aiozip = AioZipStream(files, chunksize=32768)
    async with aiofiles.open(zipfile, mode='wb') as z:
        async for chunk in aiozip.stream():
            await z.write(chunk)

@with_session
async def async_makezip(session, links, name):
    with tempfile.TemporaryDirectory() as tempdir:
        files = []
        for i, link in enumerate(links):
            async with session.head(link, allow_redirects=True) as resp:
                size = int(resp.headers.get('Content-Length', -1))
            if size > 5e6:  # 5 MB
                continue
            image_filename = f'{tempdir}/{i}.idk'
            async with session.get(link) as resp:
                content = await resp.content.read()
            imgio = img2pdf.BytesIO(content)
            image = Image.open(imgio).convert('RGB')
            # Unknown ExifOrientationError on PNG format
            image.save(image_filename, format='JPEG')
            files.append({'file' : image_filename , 'name' : name + image_filename[ : -4] + '.jpg'})
        filename = f'{name}.zip'
        await write_zipfile(filename, files)
    return filename


_filesemaphore = asyncio.Semaphore(3)
async def send_file(ctx, name, links, file_format):
    assert file_format in ('pdf', 'zip'), ValueError('bad file format')
    if len(name) > 25:
        name = name[:20]
    originalname = name
    loading = await ctx.send(file=discord.File('static/loading.gif'))
    async with _filesemaphore:
        name += str(random.randint(0, 1000000000))
        if file_format == 'pdf':
            filename = await async_makepdf(links, name)
        elif file_format == 'zip':
            filename = await async_makezip(links, name)
        url = await upload(filename)
        embed = discord.Embed(
            title=originalname,
            description="",
            color=random.choice(colors),
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
