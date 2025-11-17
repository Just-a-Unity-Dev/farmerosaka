from discord.ext import commands
from discord import Message
from discord.ext import tasks
import os


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

        with open("corpus.txt", "r") as f:
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

    @tasks.loop(minutes=60)
    async def autosave_corpus(self):
        with open("corpus.txt", "w") as f:
            f.write(self.corpus)
        print("Autosaved corpus.")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(RecorderCog(client))
