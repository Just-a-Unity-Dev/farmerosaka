from enum import Enum

from discord.ext import commands
from discord import Message
from discord.ext import tasks
import random
import os

from classes.is_owner import is_owner

class QOTDSelectMode(Enum):
    MESSAGE_POOL = 1
    AUTHOR_BASED = 2


class QOTDCog(
    commands.Cog,
    name="QOTD",
    description="The quote of the day for today! Yippeeee!"
):
    qotd_messages_by_author = {}
    qotd_messages_pooled = []
    messages_sent_today = 0

    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.qotd_channel = self.client.get_channel(int(os.getenv("QOTD_CHANNEL")))

    @commands.Cog.listener("on_message")
    async def qotd_handler(self, message: Message):
        if message.author.bot:
            return
        author = message.author.id
        if author in self.qotd_messages_by_author:
            self.qotd_messages_by_author[author].append(message)
        else:
            self.qotd_messages_by_author[author] = [message]
        self.qotd_messages_pooled.append(message)
        self.messages_sent_today += 1
    

    @commands.hybrid_command(
            name="forceqotd",
            brief="forcibly sends a qotd",
            description="it forces out a qotd. what else do you want me to say"
    )
    @is_owner()
    async def force_qotd_command(self, ctx: commands.Context):
        await self.send_quote_of_the_day()
        await ctx.reply("Attempted to send the quote of the day.")

    async def send_quote_of_the_day(self):
        """Sends a random quote of the day into the QOTD channel."""

        if self.messages_sent_today <= 0:
            await self.qotd_channel.send("Wow. No messages were sent yesterday... sorry :(")
            return await Exception("No messages were sent today. Failed to get proper QOTD.")

        mode = random.choice(list(QOTDSelectMode))
        selected_qotd: Message
        if mode == QOTDSelectMode.MESSAGE_POOL:
            # Standard mode
            selected_qotd = random.choice(self.qotd_messages_pooled)
        elif mode == QOTDSelectMode.AUTHOR_BASED:
            # Equal chance, or by-author mode
            key = random.choice(list(self.qotd_messages_by_author.keys()))
            selected_qotd = random.choice(self.qotd_messages_by_author[key])

        content = selected_qotd.content
        author = selected_qotd.author.id
        jump_url = selected_qotd.jump_url

        await self.qotd_channel.send("**Quote of the day from yesterday:**\n"
                                     f"> {content}\n-# Thank you, <@{author}>! (see {jump_url})\n"
                                     f"-# Selected via `{mode.name}` mode")

        self.clear_messages()
    
    def clear_messages(self):
        self.messages_sent_today = 0
        self.qotd_messages_by_author = {}
        self.qotd_messages_pooled = []


async def setup(client: commands.Bot) -> None:
    await client.add_cog(QOTDCog(client))
