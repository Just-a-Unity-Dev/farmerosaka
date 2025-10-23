from discord.ext import commands
from classes.database import Database
from classes.is_owner import is_owner
from tabulate import tabulate


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
    async def eval_sql_command(
        self,
        ctx: commands.Context,
        *,
        message: str
    ):
        status = await ctx.reply("running sql... :cloud:")
        sql_code = message.strip()

        cursor = self.database.database.cursor()
        message = "failed to run code: "
        try:
            cursor.execute(sql_code)
            self.database.database.commit()
        except Exception as e:
            message += repr(e)
        else:
            if cursor.description is None:
                column_names = (description[0] for description in cursor.description)
                cursor_data = list(cursor.fetchall())
                data = tabulate(cursor_data, column_names, tablefmt="rounded_grid")
                message = f"```{data}```"
            else:
                message = "successfully ran sql code!"

        if len(message) > 2000:
            return await status.edit(content="data specified could not\
                                      fit in the 2000 character limit.")

        await status.edit(content=message)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(AdminCog(client))
