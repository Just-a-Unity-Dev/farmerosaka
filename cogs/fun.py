import os
import random
from discord.ext import commands
from discord.ext import tasks
from datetime import time
import discord
import aiohttp
from typing import List

from classes.database import Database
from cogs.message_recorder import RecorderCog


class FunCog(
    commands.Cog,
    name="Fun",
    description="Just fun stuff!"
):
    database: Database

    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.database = client.database
        self.qotd_channel = self.client.get_channel(int(os.getenv("QOTD_CHANNEL")))
        self.daily_task.start()

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

    @commands.hybrid_command(
            name="addinstruct",
            brief="adds a instruction.",
            description="adds an instruction that ,instruct can ask."
    )
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def add_instruction_command(self, ctx: commands.Context, *, message: str):
        sanitized_status = message.strip()[:128]
        if sanitized_status == "":
            return await ctx.reply("supply a message, please.")
        cursor = self.database.database.cursor()

        query = "INSERT INTO instructions VALUES (NULL, ?, ?)"
        cursor.execute(query, (ctx.author.id, sanitized_status))
        cursor.execute("SELECT last_insert_rowid();")

        self.database.add_log(
            ctx.author.id,
            "AddInstruction",
            f"Added instruction ID {cursor.fetchone()}"
        )

        self.database.database.commit()
        cursor.close()

        return await ctx.reply(f"added `{message}` as a possible instruction."
                               " thank you collaborator for providing helpful information to my"
                               " knowledge bank, this will help many others!")

    @commands.hybrid_command(
            name="instruct",
            brief="the bot instructs you on how to do things!",
            description="add instructions with the ,addinstruct command."
    )
    async def instruct_command(self, ctx: commands.Context, *, question: str = ""):
        if question == "":
            return await ctx.reply("re-run the command and state what do you need help with")

        cursor = self.database.database.cursor()

        cursor.execute(f"SELECT * FROM instructions ORDER BY RANDOM() LIMIT {random.randint(3,7)};")
        instructions = cursor.fetchall()
        cursor.close()

        message = f"Here are the instructions on: **{question}**"
        i = 0
        for instruction in instructions:
            i += 1
            message += f"\n{i}. {instruction[2]}"
        message += f"\n{i + 1}. Done!"

        return await ctx.reply(message)

    async def send_quote_of_the_day(self):
        """Sends a random quote of the day into the QOTD channel."""
        recorder_cog: RecorderCog = self.client.get_cog("Message recorder")
        selected_qotd = random.choice(recorder_cog.today_messages)

        await self.qotd_channel.send("**Quote of the day from yesterday:**\n"
                                     f"> {selected_qotd[0]}\n"
                                     f"-# Thank you, <@{selected_qotd[1]}>!")

        recorder_cog.today_messages = []

    @tasks.loop(time=time(hour=9, minute=0))
    async def daily_task(self):
        await self.send_quote_of_the_day()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(FunCog(client))
