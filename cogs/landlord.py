from discord.ext import commands
from classes.database import Database
from typing import Optional, Literal


class LandlordCog(
    commands.Cog,
    name="Landlord",
    description="Self-management of personal roles and channels."
):
    database: Database
    MAX_PERSONAL_ROLES = 3

    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.database = client.database

    def get_role_count(self, owner_id: int) -> int:
        cursor = self.database.database.cursor()
        cursor.execute("SELECT id FROM roles WHERE owner=?", (owner_id,))
        return len(cursor.fetchall())

    @commands.hybrid_command(
            name="createrole",
            brief="creates a role",
            description="immediately sets the pfp of farmerosaka to whatever is attached as a link"
    )
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def create_role_command(
        self,
        ctx: commands.Context,
        role_name: str,
        status: Optional[Literal['personal', 'whitelist', 'public']]
    ):
        role_count = self.get_role_count(ctx.author.id)
        if role_count >= self.MAX_PERSONAL_ROLES:
            return await ctx.reply("you have three custom roles."
                                   " use an existing one or delete one to save space.")

        status_int = 0
        if status == 'whitelist':
            status_int = 1
        if status == 'public':
            status_int = 2

        role = await ctx.guild.create_role(name=role_name)
        role_id = role.id

        cursor = self.database.database.cursor()
        cursor.execute("INSERT INTO roles VALUES (?, ?, ?, ?)",
                       (role_id, ctx.author.id, status_int, Database.utc_time_now(),))
        self.database.database.commit()

        self.database.add_log(ctx.author.id, "CreateRole",
                              f"Created role with ID {cursor.lastrowid}", cursor)
        await ctx.reply(
            f"created role, you have `{role_count + 1}/{self.MAX_PERSONAL_ROLES}` slots used"
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(LandlordCog(client))
