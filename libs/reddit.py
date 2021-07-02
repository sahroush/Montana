import aiohttp
from libs.util import with_session


def makeUrl(afterID, sub):
    return sub.split('/.json')[0] + "/.json?after={}".format(afterID)


def ismedia(imageUrl, pdf):
    ismed = ('.jpg' in imageUrl or
             '.webm' in imageUrl or
             ('.gif' in imageUrl and not pdf) or
             '.png' in imageUrl) and '.gifv' not in imageUrl
    return ismed


@with_session
async def fetch(session, sub, pdf):
    url = makeUrl('', "https://www.reddit.com/r/" + sub)
    async with session.get(url) as resp:
        sub_json = await resp.json()
    sfw = []
    nsfw = []
    posts = sub_json['data']['children']
    for post in posts:
        if 'title' not in post['data'] or 'url' not in post['data']:
            continue
        title, url = post['data']['title'], post['data']['url']

        # check file type
        if not ismedia(url, pdf):
            continue

        # check file size
        if pdf:
            async with session.head(url, allow_redirects=True) as resp:
                size = int(resp.headers.get('Content-Length', -1))
            if size > 2.25e6:   # 2.25 MB
                continue

        # add to their category
        if post['data']['over_18']:
            nsfw.append((title, url))
        else:
            sfw.append((title, url))
    return sfw, nsfw
