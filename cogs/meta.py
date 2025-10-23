from discord import app_commands
from discord.ext import commands
import discord
import aiohttp
from typing import List

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

    @commands.hybrid_command(
            name="pfp",
            brief="sets the pfp of farmerosaka.",
            description="immediately sets the pfp of farmerosaka to whatever is attached as a link"
    )
    @commands.cooldown(1, 15, commands.BucketType.guild)
    async def pfp_command(self, ctx: commands.Context, image_url: str = ""):
        image_data: bytes = None
        if image_url == "":
            # Handle attachment-based pfp uploads
            attachments: List[discord.Attachment]
            if ctx.message.reference is None:
                attachments = ctx.message.attachments
            else:
                message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                attachments = message.attachments

            if len(attachments) <= 0:
                return await ctx.reply("add a link, upload an image, or reply to an **image**.")
            image_url = attachments[0].url
            image_data = await attachments[0].read()

        status = await ctx.reply("gimme a second...")
        try:
            if image_data is None:
                # download image link as bytes
                # probably shouldn't be in here but whatever i guess
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status != 200:
                            await status.edit(content=f"failed to dl image, err code {resp.status}")
                            return
                        image_data = await resp.read()

            self.database.add_log(
                ctx.author.id,
                "PFPChange",
                f"Changed the profile picture to [this]({image_url})"
            )
            await self.client.user.edit(avatar=image_data)
            return await status.edit(content="updated my pfp to your liking.")
        except discord.errors.HTTPException as e:
            if e.status == 400:
                print(f"bad request: {e.text.lower()}")
                await status.edit(content=f"bad request: {e.text.lower()}")
            else:
                print(f"bad request: {e.text.lower()}")
                await status.edit(content=f"an http error occurred: {e.status} - {e.text}")
        except Exception as e:
            print(f"An error occurred: {e}")
            return await status.edit(content="an unhandled error occurred, please contact rain.")

    @commands.hybrid_command(
            name="addstatus",
            brief="adds a status.",
            description="adds a status that can be picked."
    )
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def add_status_command(self, ctx: commands.Context, *, message: str):
        sanitized_status = message.strip()[:128]
        if sanitized_status == "":
            return await ctx.reply("supply a message, please.")
        cursor = self.database.database.cursor()

        query = "INSERT INTO statuses VALUES (NULL, ?, ?)"
        cursor.execute(query, (ctx.author.id, sanitized_status))
        cursor.execute("SELECT last_insert_rowid();")

        self.database.add_log(
            ctx.author.id,
            "AddStatus",
            f"Added status ID {cursor.fetchone()}"
        )

        self.database.database.commit()
        cursor.close()

        return await ctx.reply(f"added `{message}` as a possible status to the bot.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"cooldown. try again in {error.retry_after:.2f} seconds.")
        else:
            raise error


async def setup(client: commands.Bot) -> None:
    await client.add_cog(MetaCog(client))
