import asyncio
from collections import namedtuple

import discord


class Paginator:
    emojis = namedtuple("Emoji", ["prev", "next", "remove"])("⏪", "⏩", "🗑")

    def __init__(self, bot, ctx, names, images, public=False, timeout=180):
        self.bot = bot
        self.ctx = ctx
        self.names = names
        self.images = images
        assert len(names) == len(images)
        self.public = public
        self.timeout = timeout
        self.index = 0
        self.message = None

    @property
    def current_name(self):
        return self.names[self.index]

    @property
    def current_image(self):
        return self.images[self.index]

    @property
    def footer(self):
        return f'{self.index + 1}/{len(self.images)}'

    @property
    def embed(self):
        title = self.current_name
        description = ""
        if len(title) > 256:
            description = "..." + title[100:]
            title = title[:100] + "..."
        embed = discord.Embed(
            title=title,
            description=description,
            color=242424, url=self.current_image
        )
        embed.set_footer(text=self.footer)
        embed.set_image(url=self.current_image)
        return embed

    def reaction_trigger(self, reaction, user):
        if reaction.message.id != self.message.id:  # reacted on other messages
            return False
        if user == self.message.author:  # the reaction was made by the bot itself
            return False
        if not self.public and user != self.ctx.author:  # made by other users
            return False
        if str(reaction) not in self.emojis:  # not trigger emoji
            return False
        return True  # made by user || third party

    async def react_handler(self, reaction, user):
        react_emoji = str(reaction)
        await self.message.remove_reaction(reaction, user)

        if react_emoji == self.emojis.remove:
            await self.message.delete()
            await self.ctx.message.delete()
            return True

        if react_emoji == self.emojis.next and self.index + 1 < len(self.images):
            self.index += 1
            await self.message.edit(embed=self.embed)

        elif react_emoji == self.emojis.prev and self.index > 0:
            self.index -= 1
            await self.message.edit(embed=self.embed)

        return False

    async def pagify(self):
        self.message = await self.ctx.send(embed=self.embed)
        for emoji in self.emojis:
            await self.message.add_reaction(emoji)

        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add",
                    timeout=self.timeout,
                    check=self.reaction_trigger
                )
                if await self.react_handler(reaction, user):
                    break
            except asyncio.TimeoutError:
                try:
                    for emoji in self.emojis:
                        await self.message.clear_reaction(emoji)
                except discord.NotFound:
                    pass
                break
