import nhentai as nh


def fetch_hentai(sixdigit):
    douj = nh.Doujinshi(sixdigit)
    links = []
    for i in range(douj.pages):
        links.append(douj[i])
    return links, douj.name