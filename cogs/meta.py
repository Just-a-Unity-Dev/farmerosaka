from discord import Message, app_commands
from discord.ext import commands
import re

from classes.database import Database


class MetaCog(
    commands.Cog,
    name="Meta",
    description="Meta stuff, including displaying information."
):
    database: Database

    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.database = client.database
        self.VERSION = "0.0.1"

    @commands.hybrid_command(
            name="ping",
            brief="pong.",
            description="get's the latency of the bot to the discord API."
    )
    @app_commands.allowed_installs(guilds=True)
    async def ping(self, ctx: commands.Context):
        """Gets the latency of the bot."""
        await ctx.reply(f'pong. {round(self.client.latency * 1000)}ms.')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"cooldown. try again in {error.retry_after:.2f} seconds.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("you're not the owner of this bot. shoo, shoo.")
        else:
            raise error

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        pattern = re.compile(r"(youtu\.be)\/(.*)\?si=(.*)")
        if pattern.search(message.content):
            await message.reply("**HEY**. Please remove the `?si=` part of your youtube links."
                                " You may keep `&t=` for timestamps.\nThe `?si=` is a"
                                " source identifier used to **track you**. For the better"
                                " of everyone in the server, please remove it. Thank you!")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(MetaCog(client))
