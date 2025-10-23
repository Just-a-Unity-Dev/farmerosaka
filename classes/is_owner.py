from discord.ext import commands
import os
OWNER_USER_ID = int(os.getenv("OWNER_ID"))


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == OWNER_USER_ID
    return commands.check(predicate)
