import requests


def makeUrl(afterID, sub):
    return sub.split('/.json')[0] + "/.json?after={}".format(afterID)


def ismedia(imageUrl):
    ismed = ('.jpg' in imageUrl or
             '.webm' in imageUrl or
             ('.gif' in imageUrl ) or
             '.png' in imageUrl) and '.gifv' not in imageUrl
    return ismed


def fetch(sub):
    url = makeUrl('', "https://www.reddit.com/r/" + sub)
    subJson = requests.get(url, headers={'User-Agent': 'NekoBot'}).json()
    sfw = []
    try:
        posts = subJson['data']['children']
        for post in posts:
            ismed = ismedia(post['data']['url'])
            if ismed:
                sfw += [[post['data']['title'], post['data']['url']]]
    except:
        pass
    return sfw
