from discord.ext import commands
from classes.database import Database
from typing import Optional, Literal
from tabulate import tabulate
import discord


class LandlordCog(
    commands.Cog,
    name="Landlord",
    description="Self-management of personal roles and channels."
):
    database: Database
    MAX_PERSONAL_ROLES = 3
    status_int_lut = {
        0: "personal",
        1: "whitelist",
        2: "public"
    }
    status_str_lut = {}

    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.database = client.database
        # idk if this is pythonic but like ... ok
        self.status_str_lut = dict(zip(self.status_int_lut.values(), self.status_int_lut.keys()))

    def role_is_owner(self, owner_id: int, role_id: int):
        return len(self.database.database.execute("SELECT * FROM roles WHERE id=? AND owner=?",
                                                  (role_id, owner_id,)).fetchall()) > 0

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
        status: Literal['personal', 'whitelist', 'public']
    ):
        role_count = self.get_role_count(ctx.author.id)
        if role_count >= self.MAX_PERSONAL_ROLES:
            return await ctx.reply("you have three custom roles."
                                   " use an existing one or delete one to save space.")

        if status not in self.status_str_lut.keys():
            return await ctx.reply("argument after name must be either `personal`, "
                                   f"`whitelist` or `public`, `{status}` is invalid.")
        status_int = self.status_str_lut(status)

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
        self.database.add_log(ctx.author.id, "RoleCreateRole", f"Changed role ID"
                              f"({cursor.lastrowid}) color")

    @commands.hybrid_command(
            name="listroles",
            brief="list all your roles",
            description="it lists all your roles ... duh"
    )
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def list_roles_command(
        self,
        ctx: commands.Context,
        user: discord.User = None
    ):
        id = ctx.author.id
        if user is not None:
            id = user.id

        cursor = self.database.database.cursor()
        cursor.execute("SELECT id, status FROM roles WHERE owner=?", (id,))

        column_names = [description[0] for description in cursor.description]
        column_names.append("role name")

        cursor_data = list(map(lambda x: [x[0], self.status_int_lut[x[1]], "ROLE NAME GOES HERE"],
                               cursor.fetchall()))
        for data in cursor_data:
            role = ctx.guild.get_role(int(data[0]))
            data[2] = role.name

        data = tabulate(cursor_data, column_names, tablefmt="rounded_grid")
        await ctx.reply(f"{len(cursor_data)}/{self.MAX_PERSONAL_ROLES} slots used"
                        f"\n```{data}```")

    @commands.hybrid_command(
            name="renamerole",
            brief="renames a role",
            description="renames a role given an ID and a new name"
    )
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def rename_role_command(self, ctx: commands.Context, id: int, *, name: str):
        is_owner = self.role_is_owner(ctx.author.id, id)
        if not is_owner:
            return await ctx.reply("you're not the owner of this role.")
        status = await ctx.reply("changing...")
        await ctx.guild.get_role(id).edit(name=name.strip())
        await status.edit(content="changed!")
        self.database.add_log(ctx.author.id, "RoleNameChange",
                              f"Changed role name ({id}) to {name}")

    @commands.hybrid_command(
            name="colorrole",
            brief="colors the role",
            description="changes the role color... duhhh"
    )
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def color_role_command(self, ctx: commands.Context, id: int, *, new_value: str):
        is_owner = self.role_is_owner(ctx.author.id, id)
        if not is_owner:
            return await ctx.reply("you're not the owner of this role.")

        try:
            parsed_color = discord.Colour.from_str(new_value.strip())
        except ValueError:
            return await ctx.reply("invalid color. either supply a hexcode (`#123abc`) "
                                   "or an rgb value `rgb(12, 58, 188)`")

        status = await ctx.reply("changing...")
        await ctx.guild.get_role(id).edit(colour=parsed_color)
        await status.edit(content="changed!")
        self.database.add_log(ctx.author.id, "RoleColorChange", f"Changed role ID ({id}) color")

    @commands.hybrid_command(
            name="selfunrole",
            brief="removes a custom role",
            description="removes yourself from a custom role"
    )
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def self_unrole_command(self, ctx: commands.Context, id: int):
        cursor = self.database.database.cursor()
        cursor.execute("SELECT status, id FROM roles WHERE id=?", (id,))
        data = cursor.fetchone()
        if data is None:
            return await ctx.reply("invalid unregistered role... is it even a custom one?")
        await ctx.author.remove_roles(ctx.guild.get_role(id))
        return await ctx.reply("removed you from the role!")

    @commands.hybrid_command(
            name="selfrole",
            brief="gives yourself a role",
            description="gives yourself a role that you own or that is public"
    )
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def self_role_command(self, ctx: commands.Context, id: int):
        cursor = self.database.database.cursor()
        cursor.execute("SELECT status, id FROM roles WHERE id=?", (id,))
        data = cursor.fetchone()
        if data is None:
            return await ctx.reply("invalid unregistered role... is it even a custom one?")
        role_status = data[0]
        if (role_status == 0 and self.role_is_owner(ctx.author.id, id)) or role_status == 2:
            await ctx.author.add_roles(ctx.guild.get_role(id), reason="Self-role command")
            await ctx.reply("assigned you to the role! :>")
            self.database.add_log(ctx.author.id, "RoleAdd", f"Added role row ID ({data[1]})")
        else:
            if role_status == 0:
                await ctx.reply("you must be the owner to get this role!")
            elif role_status == 1:
                await ctx.reply("you must be whitelisted by the owner to get this role!")

    @commands.hybrid_command(
            name="rolestatus",
            brief="sets role status",
            description="sets the status of a role or gets its current status"
    )
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def role_status_command(
        self,
        ctx: commands.Context,
        role_id: int,
        status: Optional[Literal['personal', 'whitelist', 'public']]
    ):
        is_owner = self.role_is_owner(ctx.author.id, role_id)
        cursor = self.database.database.cursor()
        cursor.execute("SELECT status FROM roles WHERE id=?", (role_id,))
        data = cursor.fetchone()

        if data is None:
            return await ctx.reply("role is not registered in database. is it a custom role?")

        if not is_owner or status is None:
            return await ctx.reply(f"role is under permission `{self.status_int_lut[data[0]]}`.")

        sanitized_status = status.strip()
        if sanitized_status not in self.status_str_lut.keys():
            return await ctx.reply("argument after ID must be either `personal`, "
                                   f"`whitelist` or `public`, `{status}` is invalid.")

        new_id = self.status_str_lut[sanitized_status]
        cursor.execute("UPDATE roles SET status=? WHERE id=?", (new_id, role_id,))
        self.database.database.commit()
        cursor.close()
        await ctx.reply(f"set new permission status to `{sanitized_status}`")
        self.database.add_log(ctx.author.id, "RolePermissionChange", f"Changed ID ({data[1]}) "
                              f"to permission {sanitized_status} ({new_id})")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(LandlordCog(client))
