# the discord bot wrapper
from discord.ext.commands import Greedy, Context  # or a subclass of yours
from typing import Literal, Optional
from discord.ext import commands
from asyncio import sleep
import random

from dotenv import load_dotenv
import discord
import json
import os

# load the env so the TOKEN is fed into the environment vars
load_dotenv()


class HelpCommand(commands.HelpCommand):
    def __init__(self) -> None:
        super().__init__()

    async def send_bot_help(self, mapping) -> None:
        message = ["```toml"]

        for cog in mapping:
            qualified_name = "None"
            if cog is not None:
                qualified_name = cog.qualified_name

            message.append(f"[{qualified_name}]")

            for command in mapping[cog]:
                temporary_message = f"{command.name} = \"{command.brief}\""
                temporary_message += " " + "# " + command.description

                if len(command.aliases) > 0:
                    temporary_message += " " + f"also known as: {','.join(command.aliases)}"

                message.append(temporary_message)
            message.append("\n")
        message.append("```")
        await self.get_destination().send("\n".join(message))

    async def send_cog_help(self, cog) -> None:
        await self.get_destination().send(
            f'{cog.qualified_name}: {[command.name for command in cog.get_commands()]}')

    async def send_command_help(self, command) -> None:
        await self.get_destination().send(command.name)

    async def send_group_help(self, group) -> None:
        await self.get_destination().send(
            f'{group.name}: {[command.name for index, command in enumerate(group.commands)]}')


intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(
    command_prefix=os.getenv("PREFIX"),
    intents=intents,
    help_command=HelpCommand()
)


@client.command(name="sync", brief="Sync commands.")
@commands.is_owner()
async def sync_command(
  ctx: Context,
  guilds: Greedy[discord.Object],
  spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            print("syncing tree")
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            print("copying global to guild")
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            print("clearing and resyncing")
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        elif spec == "%":
            print("clearing")
            ctx.bot.tree.clear_commands()
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"synced {len(synced)} commands "
            f"{'globally' if spec is None else 'to the current guild'}."
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


def pick_status():
    try:
        statuses = json.load(open("statuses.json", "r"))
        return random.choice(statuses)
    except Exception as e:
        print(e)
        return "err!!!"


async def status_task():
    while True:
        await client.change_presence(
            status=discord.Status.idle,
            activity=discord.CustomActivity(name=pick_status()))
        await sleep(random.randint(60, 600)*60)


@client.event
async def on_ready():
    # change presence
    client.loop.create_task(status_task())

    # load extensions
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await client.load_extension(f"cogs.{file[:-3]}")

    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

    print(f'Bot is now online. Ping is {round(client.latency * 1000)}ms.')

if __name__ == "__main__":
    if os.getenv('TOKEN') == 'secret':
        raise Exception("Please set your token with the TOKEN environment variable.")
    client.run(os.getenv('TOKEN'))
