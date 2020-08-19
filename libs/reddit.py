import requests


def makeUrl(afterID, sub):
    return sub.split('/.json')[0] + "/.json?after={}".format(afterID)


def ismedia(imageUrl):
    return ('.jpg' in imageUrl or
            '.webm' in imageUrl or
            '.gif' in imageUrl or
            '.png' in imageUrl) and '.gifv' not in imageUrl


def fetch(sub):
    url = makeUrl('', "https://www.reddit.com/r/" + sub)
    subJson = requests.get(url, headers={'User-Agent': 'Montana'}).json()
    sfw = []
    nsfw = []
    try:
        posts = subJson['data']['children']
        for post in posts:
            ismed = ismedia(post['data']['url'])
            if ismed and post['data']['over_18']:
                nsfw += [[post['data']['title'], post['data']['url']]]
            elif ismed:
                sfw += [[post['data']['title'],  post['data']['url']]]
    except:
        pass
    return sfw, nsfw
