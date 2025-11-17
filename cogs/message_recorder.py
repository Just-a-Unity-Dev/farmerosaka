from discord.ext import commands
from discord import Message
from discord.ext import tasks
import os

from classes.is_owner import is_owner


class RecorderCog(
    commands.Cog,
    name="Message recorder",
    description="Records your messages (unless you don't want to)"
):
    messages = []
    today_messages = []
    corpus = ""

    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.opt_out_id = int(os.getenv('MESSAGE_RECORDER_OPT_OUT_ROLE_ID'))
        self.messages = []

        with open("corpus.txt", "w+") as f:
            self.corpus = f.read().strip()

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return
        if message.author.get_role(self.opt_out_id) is not None:
            return
        self.messages.append([message.content, message.author.id, message.jump_url])
        self.today_messages.append([message.content, message.author.id, message.jump_url])
        self.corpus += " " + message.content

    @commands.hybrid_command(
            name="savecorpus",
            brief="saves corpus",
            description="saves the corpus"
    )
    @is_owner()
    async def pfp_command(self, ctx: commands.Context):
        self.save_corpus()
        await ctx.reply("Saved corpus.")

    def save_corpus(self):
        with open("corpus.txt", "w") as f:
            f.write(self.corpus.strip())
        print("Saved corpus to file.")

    @tasks.loop(minutes=60)
    async def autosave_corpus(self):
        self.save_corpus()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(RecorderCog(client))
