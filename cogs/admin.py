from discord.ext import commands
from classes.database import Database
from classes.is_owner import is_owner


class AdminCog(
    commands.Cog,
    name="Admin",
    description="Administrative-related cogs."
):
    database: Database

    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.database = client.database

    @commands.hybrid_command(
            name="evalsql",
            brief="evaluates sql.",
            description="opens a cursor, and runs the sql script"
    )
    @is_owner()
    async def inspect_command(
        self,
        ctx: commands.Context,
        *,
        message: str
    ):
        sql_code = message.strip()

        cursor = self.database.database.cursor()
        cursor.execute(sql_code)
        await ctx.reply("`{}`".format('\n'.join(map(lambda x: repr(x), cursor.fetchall()))))


async def setup(client: commands.Bot) -> None:
    await client.add_cog(AdminCog(client))
