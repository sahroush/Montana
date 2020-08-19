import requests


def makeUrl(afterID, sub):
    return sub.split('/.json')[0] + "/.json?after={}".format(afterID)


def ismedia(imageUrl , include_gifs):
    return ('.jpg' in imageUrl or
            '.webm' in imageUrl or
            ('.gif' in imageUrl and include_gifs) or
            '.png' in imageUrl) and '.gifv' not in imageUrl


def fetch(sub , include_gifs):
    url = makeUrl('', "https://www.reddit.com/r/" + sub)
    subJson = requests.get(url, headers={'User-Agent': 'Montana'}).json()
    sfw = []
    nsfw = []
    try:
        posts = subJson['data']['children']
        for post in posts:
            ismed = ismedia(post['data']['url'] , include_gifs)
            if ismed and post['data']['over_18']:
                nsfw += [[post['data']['title'], post['data']['url']]]
            elif ismed:
                sfw += [[post['data']['title'],  post['data']['url']]]
    except:
        pass
    return sfw, nsfw