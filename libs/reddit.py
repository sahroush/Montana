import requests


def makeUrl(afterID, sub):
    return sub.split('/.json')[0] + "/.json?after={}".format(afterID)


def ismedia(imageUrl, pdf):
    ismed = ('.jpg' in imageUrl or
             '.webm' in imageUrl or
             ('.gif' in imageUrl and not pdf) or
             '.png' in imageUrl) and '.gifv' not in imageUrl
    if pdf:
        response = requests.head(imageUrl, allow_redirects=True)
        size = int(response.headers.get('content-length', -1))
        if size > 2250000:
            ismed = 0
    return ismed


def fetch(sub, pdf):
    url = makeUrl('', "https://www.reddit.com/r/" + sub)
    subJson = requests.get(url, headers={'User-Agent': 'Montana'}).json()
    sfw = []
    nsfw = []
    try:
        posts = subJson['data']['children']
        for post in posts:
            ismed = ismedia(post['data']['url'], pdf)
            if ismed and post['data']['over_18']:
                nsfw += [[post['data']['title'], post['data']['url']]]
            elif ismed:
                sfw += [[post['data']['title'], post['data']['url']]]
    except:
        pass
    return sfw, nsfw
