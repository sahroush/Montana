import textwrap
import discord
import asyncio

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
    
async def pagify(bot , ctx , links , names):
    cur = 0
    embed = discord.Embed(title=wrapped(names[cur]), description="", color=242424, url=links[cur])
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
            reaction, user = await bot.wait_for("reaction_add", timeout=10, check=check)
            if await Check(reaction, user):
                if await react(reaction, user):
                    break
        except asyncio.TimeoutError:
            break
        except:
            await message.clear_reactions()
            break