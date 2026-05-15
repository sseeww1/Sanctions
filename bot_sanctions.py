import os
import sqlite3
import time
from datetime import timedelta
from typing import Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

PREFIX = "+"
MAIN_COLOR = 0x5865F2
ERROR_COLOR = 0xED4245
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.moderation = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

db = sqlite3.connect("sanctions.db")
db.row_factory = sqlite3.Row
cursor = db.cursor()

COMMANDS_LIST = {
    "help": "Affiche l'aide.",
    "helpall": "Affiche l'aide complète.",
    "panel": "Panel visuel de permissions.",
    "perms": "Affiche les rôles classés par permissions.",
    "permsconfig": "Affiche la configuration des permissions.",
    "setroleperm": "Définit le niveau d'un rôle.",
    "delroleperm": "Retire le niveau d'un rôle",
    "setcmdperm": "Définit le niveau d'une commande.",
    "resetcmdperm": "Réinitialise le niveau d'une commande.",
    "delperm": "Retire une permission personnalisée.",
    "wlowner": "Ajoute un owner whitelist.",
    "unwlowner": "Retire un owner whitelist.",
    "ownerlist": "Affiche les owners whitelist.",
    "bl": "Blacklist un utilisateur.",
    "unbl": "Retire une blacklist.",
    "blinfo": "Affiche les infos blacklist.",
    "blrank": "Empêche un membre d'avoir des rôles dangereux.",
    "unblrank": "Retire le blrank.",
    "kick": "Expulse un membre.",
    "ban": "Bannit un utilisateur.",
    "unban": "Débannit un utilisateur.",
    "baninfo": "Affiche les infos ban.",
    "warn": "Avertit un membre.",
    "unwarn": "Supprime le dernier warn.",
    "mute": "Mute temporairement un membre.",
    "unmute": "Retire le mute.",
    "lock": "Verrouille un salon.",
    "unlock": "Déverrouille un salon.",
    "clear": "Supprime des messages.",
    "info": "Guide staff.",
    "sanctions": "Affiche les sanctions.",
    "delsanction": "Supprime une sanction.",
    "clearsanctions": "Supprime toutes les sanctions.",
    "avatar": "Affiche l'avatar.",
    "banner": "Affiche la bannière.",
    "userinfo": "Infos utilisateur.",
    "serverinfo": "Infos serveur.",
}

DEFAULT_COMMAND_LEVELS = {
    "help": 0, "helpall": 0, "avatar": 0, "banner": 0, "userinfo": 0, "serverinfo": 0, "perms": 0,
    "info": 2, "sanctions": 2,
    "warn": 3, "unwarn": 3,
    "mute": 4, "unmute": 4,
    "lock": 5, "unlock": 5, "clear": 5,
    "bl": 6, "unbl": 6, "blinfo": 6,
    "kick": 7, "ban": 7, "unban": 7, "baninfo": 7,
    "panel": 8, "delperm": 8, "setroleperm": 8, "delroleperm": 8, "setcmdperm": 8, "resetcmdperm": 8, "permsconfig": 8,
    "wlowner": 9, "unwlowner": 9, "ownerlist": 9, "blrank": 9, "unblrank": 9, "delsanction": 9, "clearsanctions": 9,
}

USAGES = {
    "bl": "+bl <@user/id> <raison>",
    "unbl": "+unbl <@user/id>",
    "blinfo": "+blinfo <@user/id>",
    "kick": "+kick <@user/id> <raison>",
    "ban": "+ban <@user/id> <raison>",
    "unban": "+unban <user_id> <raison>",
    "baninfo": "+baninfo <user_id>",
    "warn": "+warn <@membre> <raison>",
    "unwarn": "+unwarn <@membre>",
    "mute": "+mute <@membre> <minutes> <raison>",
    "unmute": "+unmute <@membre> <raison>",
    "lock": "+lock [#salon]",
    "unlock": "+unlock [#salon]",
    "clear": "+clear <nombre>",
    "delsanction": "+delsanction <id>",
    "clearsanctions": "+clearsanctions <@membre>",
    "sanctions": "+sanctions <@membre>",
    "setroleperm": "+setroleperm <@rôle> <niveau>",
    "delroleperm": "+delroleperm <@rôle>",
    "setcmdperm": "+setcmdperm <commande> <niveau>",
    "resetcmdperm": "+resetcmdperm <commande>",
    "delperm": "+delperm <@rôle> <commande>",
    "wlowner": "+wlowner <@user/id>",
    "unwlowner": "+unwlowner <@user/id>",
    "blrank": "+blrank <@membre> <raison>",
    "unblrank": "+unblrank <@membre>",
}

PANEL_CATEGORIES = {
    "moderation": {"label": "Modération", "commands": ["bl", "unbl", "blinfo", "warn", "unwarn", "mute", "unmute", "lock", "unlock", "clear", "sanctions", "delsanction", "clearsanctions"]},
    "ban": {"label": "Kick / Ban", "commands": ["kick", "ban", "unban", "baninfo"]},
    "admin": {"label": "Administration", "commands": ["panel", "delperm", "setroleperm", "delroleperm", "setcmdperm", "resetcmdperm", "permsconfig", "wlowner", "unwlowner", "ownerlist", "blrank", "unblrank"]},
    "public": {"label": "Public", "commands": ["help", "helpall", "avatar", "banner", "userinfo", "serverinfo", "perms"]},
}

DANGEROUS_ROLE_PERMISSIONS = [
    "administrator", "manage_guild", "manage_roles", "manage_channels", "ban_members", "kick_members",
    "moderate_members", "manage_messages", "manage_webhooks", "mention_everyone", "manage_nicknames",
    "manage_events", "view_audit_log"
]


def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blacklisted_users (
        guild_id TEXT,
        user_id TEXT,
        reason TEXT,
        moderator_id TEXT,
        created_at INTEGER,
        PRIMARY KEY (guild_id, user_id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blacklisted_roles (
        guild_id TEXT,
        role_id TEXT,
        reason TEXT,
        moderator_id TEXT,
        created_at INTEGER,
        PRIMARY KEY (guild_id, role_id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rank_blacklisted_users (
        guild_id TEXT,
        user_id TEXT,
        reason TEXT,
        moderator_id TEXT,
        created_at INTEGER,
        PRIMARY KEY (guild_id, user_id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS warns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT,
        user_id TEXT,
        moderator_id TEXT,
        reason TEXT,
        created_at INTEGER
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sanctions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT,
        type TEXT,
        user_id TEXT,
        moderator_id TEXT,
        reason TEXT,
        created_at INTEGER,
        expires_at INTEGER
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS command_permissions (
        guild_id TEXT,
        command_name TEXT,
        role_id TEXT,
        PRIMARY KEY (guild_id, command_name, role_id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS role_perm_levels (
        guild_id TEXT,
        role_id TEXT,
        perm_level INTEGER,
        PRIMARY KEY (guild_id, role_id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS command_perm_levels (
        guild_id TEXT,
        command_name TEXT,
        perm_level INTEGER,
        PRIMARY KEY (guild_id, command_name)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS owner_whitelist (
        user_id TEXT PRIMARY KEY,
        added_by TEXT,
        created_at INTEGER
    )
    """)
    db.commit()


def create_embed(title: str, description: str, color: int = MAIN_COLOR):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="Bot sanctions • Préfixe : +")
    return embed


def invalid_usage_embed(usage: str):
    return discord.Embed(
        title="Utilisation invalide",
        description=f"Utilise `{usage}`.",
        color=ERROR_COLOR
    )


def success_embed(title: str, description: str):
    return create_embed(title, description, SUCCESS_COLOR)


def error_embed(title: str, description: str):
    return create_embed(title, description, ERROR_COLOR)


async def get_member_or_user(ctx: commands.Context, value: str):
    value = value.replace("<@", "").replace(">", "").replace("!", "")
    try:
        user_id = int(value)
    except ValueError:
        return None

    member = ctx.guild.get_member(user_id)
    if member:
        return member

    try:
        return await bot.fetch_user(user_id)
    except (discord.NotFound, discord.HTTPException):
        return None


def log_sanction(guild_id: int, sanction_type: str, user_id: int, moderator_id: int, reason: str = "Aucune raison", expires_at: Optional[int] = None):
    cursor.execute("""
    INSERT INTO sanctions
    (guild_id, type, user_id, moderator_id, reason, created_at, expires_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (str(guild_id), sanction_type, str(user_id), str(moderator_id), reason, int(time.time()), expires_at))
    db.commit()
    return cursor.lastrowid


def is_whitelisted_owner(user_id: int):
    cursor.execute("SELECT user_id FROM owner_whitelist WHERE user_id = ?", (str(user_id),))
    return cursor.fetchone() is not None


async def is_bot_owner_user(user: discord.User):
    return await bot.is_owner(user) or is_whitelisted_owner(user.id)


def get_command_perm_level(guild_id: int, command_name: str):
    cursor.execute("SELECT perm_level FROM command_perm_levels WHERE guild_id = ? AND command_name = ?", (str(guild_id), command_name))
    row = cursor.fetchone()
    return int(row["perm_level"]) if row else DEFAULT_COMMAND_LEVELS.get(command_name, 0)


def get_role_perm_level(guild_id: int, role_id: int):
    cursor.execute("SELECT perm_level FROM role_perm_levels WHERE guild_id = ? AND role_id = ?", (str(guild_id), str(role_id)))
    row = cursor.fetchone()
    return int(row["perm_level"]) if row else None


def get_role_auto_perm_level(role: discord.Role):
    perms = role.permissions
    if perms.administrator:
        return 10
    if perms.manage_guild or perms.manage_roles or perms.manage_channels or perms.manage_webhooks or perms.view_audit_log:
        return 8
    if perms.ban_members or perms.kick_members or perms.moderate_members:
        return 7
    if perms.manage_messages or perms.manage_nicknames or perms.mention_everyone or perms.manage_events:
        return 6
    if perms.manage_threads or perms.create_public_threads or perms.create_private_threads or perms.send_messages_in_threads:
        return 5
    if perms.embed_links or perms.attach_files or perms.add_reactions or perms.use_external_emojis or perms.use_external_stickers:
        return 4
    if perms.send_messages or perms.read_message_history or perms.connect or perms.speak:
        return 3
    if perms.view_channel:
        return 2
    return 1


def get_member_perm_level(member: discord.Member):
    if member.guild_permissions.administrator:
        return 10

    levels = []
    for role in member.roles:
        if role.is_default():
            continue
        custom_level = get_role_perm_level(member.guild.id, role.id)
        levels.append(custom_level if custom_level is not None else get_role_auto_perm_level(role))
    return max(levels) if levels else 0


def command_has_custom_permission(guild_id: int, command_name: str):
    cursor.execute("SELECT role_id FROM command_permissions WHERE guild_id = ? AND command_name = ?", (str(guild_id), command_name))
    return cursor.fetchall()


def member_has_command_access(member: discord.Member, command_name: str):
    if member.guild_permissions.administrator:
        return True

    custom_roles = command_has_custom_permission(member.guild.id, command_name)
    if custom_roles:
        allowed_role_ids = [int(row["role_id"]) for row in custom_roles]
        return any(role.id in allowed_role_ids for role in member.roles)

    command_level = get_command_perm_level(member.guild.id, command_name)
    if command_level <= 0:
        return True

    return get_member_perm_level(member) >= command_level


async def require_access(ctx: commands.Context, command_name: str):
    if await is_bot_owner_user(ctx.author):
        return True

    if not ctx.guild:
        await ctx.reply("Cette commande doit être utilisée dans un serveur.")
        return False

    if not member_has_command_access(ctx.author, command_name):
        await ctx.reply("Tu n'as pas accès à cette commande.")
        return False

    return True


def is_user_blacklisted(guild_id: int, user_id: int):
    cursor.execute("SELECT reason FROM blacklisted_users WHERE guild_id = ? AND user_id = ?", (str(guild_id), str(user_id)))
    return cursor.fetchone()


def has_blacklisted_role(member: discord.Member):
    for role in member.roles:
        cursor.execute("SELECT reason FROM blacklisted_roles WHERE guild_id = ? AND role_id = ?", (str(member.guild.id), str(role.id)))
        result = cursor.fetchone()
        if result:
            return result
    return None


def is_rank_blacklisted(guild_id: int, user_id: int):
    cursor.execute("SELECT reason FROM rank_blacklisted_users WHERE guild_id = ? AND user_id = ?", (str(guild_id), str(user_id)))
    return cursor.fetchone()


def role_has_dangerous_permissions(role: discord.Role):
    permissions = role.permissions
    return any(getattr(permissions, permission_name, False) for permission_name in DANGEROUS_ROLE_PERMISSIONS)


async def remove_dangerous_roles(member: discord.Member, reason: str = "Membre blrank"):
    if not member.guild.me.guild_permissions.manage_roles:
        return []

    removed_roles = []
    for role in member.roles:
        if role.is_default():
            continue
        if not role_has_dangerous_permissions(role):
            continue
        if role >= member.guild.me.top_role:
            continue
        try:
            await member.remove_roles(role, reason=reason)
            removed_roles.append(role)
        except (discord.Forbidden, discord.HTTPException):
            continue
    return removed_roles


def can_act_on_member(ctx: commands.Context, member: discord.Member):
    if member.id == ctx.author.id:
        return False, "Tu ne peux pas faire cette action sur toi-même."
    if member.id == bot.user.id:
        return False, "Tu ne peux pas faire cette action sur le bot."
    if member.id == ctx.guild.owner_id:
        return False, "Tu ne peux pas faire cette action sur le propriétaire du serveur."
    if member.top_role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
        return False, "Tu ne peux pas faire cette action sur un membre avec un rôle égal ou supérieur au tien."
    if member.top_role >= ctx.guild.me.top_role:
        return False, "Je ne peux pas agir sur ce membre car son rôle est égal ou supérieur au mien."
    return True, None


class PermissionPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.selected_category = None
        self.selected_command = None
        self.selected_role = None
        self.selected_action = None

        self.category_select = discord.ui.Select(
            placeholder="1. Choisis une catégorie",
            options=[discord.SelectOption(label=data["label"], value=category) for category, data in PANEL_CATEGORIES.items()],
            row=0
        )
        self.category_select.callback = self.category_callback
        self.add_item(self.category_select)

        self.command_select = discord.ui.Select(
            placeholder="2. Choisis une commande",
            options=[discord.SelectOption(label="Choisis d'abord une catégorie", value="none")],
            disabled=True,
            row=1
        )
        self.command_select.callback = self.command_callback
        self.add_item(self.command_select)

        self.role_select = discord.ui.RoleSelect(placeholder="3. Choisis un rôle", row=2)
        self.role_select.callback = self.role_callback
        self.add_item(self.role_select)

        self.action_select = discord.ui.Select(
            placeholder="4. Choisis l'action",
            options=[
                discord.SelectOption(label="Ajouter l'accès", value="add", emoji="✅"),
                discord.SelectOption(label="Retirer l'accès", value="remove", emoji="🗑️"),
                discord.SelectOption(label="Voir les accès", value="view", emoji="📋"),
                discord.SelectOption(label="Réinitialiser", value="reset", emoji="♻️"),
            ],
            row=3
        )
        self.action_select.callback = self.action_callback
        self.add_item(self.action_select)

    def build_embed(self, guild: discord.Guild):
        category_text = f"`{PANEL_CATEGORIES[self.selected_category]['label']}`" if self.selected_category else "`Aucune`"
        command_text = f"`+{self.selected_command}`" if self.selected_command else "`Aucune`"
        role_text = self.selected_role.mention if self.selected_role else "`Aucun`"
        action_text = f"`{self.selected_action}`" if self.selected_action else "`Aucune`"

        embed = create_embed(
            "Panel de permissions avancé",
            f"""
**Catégorie :** {category_text}
**Commande :** {command_text}
**Rôle :** {role_text}
**Action :** {action_text}

Quand une commande a au moins un rôle personnalisé, seuls ces rôles peuvent l'utiliser.
Les administrateurs gardent toujours l'accès.
""",
            MAIN_COLOR
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        return embed

    async def category_callback(self, interaction: discord.Interaction):
        self.selected_category = self.category_select.values[0]
        self.selected_command = None
        self.command_select.options = [
            discord.SelectOption(label=f"+{command}", value=command, description=COMMANDS_LIST.get(command, "Commande")[:100])
            for command in PANEL_CATEGORIES[self.selected_category]["commands"]
        ]
        self.command_select.disabled = False
        await interaction.response.edit_message(embed=self.build_embed(interaction.guild), view=self)

    async def command_callback(self, interaction: discord.Interaction):
        self.selected_command = self.command_select.values[0]
        await interaction.response.edit_message(embed=self.build_embed(interaction.guild), view=self)

    async def role_callback(self, interaction: discord.Interaction):
        self.selected_role = self.role_select.values[0]
        await interaction.response.edit_message(embed=self.build_embed(interaction.guild), view=self)

    async def action_callback(self, interaction: discord.Interaction):
        self.selected_action = self.action_select.values[0]
        await interaction.response.edit_message(embed=self.build_embed(interaction.guild), view=self)

    @discord.ui.button(label="Appliquer", style=discord.ButtonStyle.success, emoji="✅", row=4)
    async def apply_action(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Tu dois être administrateur.", ephemeral=True)
        if not self.selected_command:
            return await interaction.response.send_message("Choisis une commande.", ephemeral=True)
        if not self.selected_action:
            return await interaction.response.send_message("Choisis une action.", ephemeral=True)
        if self.selected_action in ["add", "remove"] and not self.selected_role:
            return await interaction.response.send_message("Choisis un rôle.", ephemeral=True)

        if self.selected_action == "add":
            cursor.execute("INSERT OR IGNORE INTO command_permissions (guild_id, command_name, role_id) VALUES (?, ?, ?)", (str(interaction.guild.id), self.selected_command, str(self.selected_role.id)))
            db.commit()
            return await interaction.response.send_message(f"✅ {self.selected_role.mention} peut utiliser `+{self.selected_command}`.", ephemeral=True)

        if self.selected_action == "remove":
            cursor.execute("DELETE FROM command_permissions WHERE guild_id = ? AND command_name = ? AND role_id = ?", (str(interaction.guild.id), self.selected_command, str(self.selected_role.id)))
            db.commit()
            return await interaction.response.send_message(f"🗑️ {self.selected_role.mention} ne peut plus utiliser `+{self.selected_command}`.", ephemeral=True)

        if self.selected_action == "view":
            cursor.execute("SELECT role_id FROM command_permissions WHERE guild_id = ? AND command_name = ?", (str(interaction.guild.id), self.selected_command))
            rows = cursor.fetchall()
            if not rows:
                desc = f"Aucun rôle personnalisé pour `+{self.selected_command}`."
            else:
                roles = []
                for row in rows:
                    role = interaction.guild.get_role(int(row["role_id"]))
                    if role:
                        roles.append(role.mention)
                desc = "\n".join(roles) if roles else "Aucun rôle trouvé."
            return await interaction.response.send_message(embed=create_embed(f"Accès de +{self.selected_command}", desc, WARNING_COLOR), ephemeral=True)

        if self.selected_action == "reset":
            cursor.execute("DELETE FROM command_permissions WHERE guild_id = ? AND command_name = ?", (str(interaction.guild.id), self.selected_command))
            db.commit()
            return await interaction.response.send_message(f"♻️ Permissions de `+{self.selected_command}` réinitialisées.", ephemeral=True)

    @discord.ui.button(label="Fermer", style=discord.ButtonStyle.danger, emoji="❌", row=4)
    async def close_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=create_embed("Panel fermé", "Le panel est fermé.", ERROR_COLOR), view=None)


class SimplePagesView(discord.ui.View):
    def __init__(self, author: discord.Member, pages):
        super().__init__(timeout=180)
        self.author = author
        self.pages = pages
        self.page = 0

    def build_embed(self):
        title, desc = self.pages[self.page]
        embed = create_embed(title, desc, MAIN_COLOR)
        embed.set_footer(text=f"Page {self.page + 1}/{len(self.pages)} • Préfixe : +")
        return embed

    async def update_message(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="<", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Ce menu ne t'appartient pas.", ephemeral=True)
        self.page = (self.page - 1) % len(self.pages)
        await self.update_message(interaction)

    @discord.ui.button(label=">", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Ce menu ne t'appartient pas.", ephemeral=True)
        self.page = (self.page + 1) % len(self.pages)
        await self.update_message(interaction)

    @discord.ui.button(label="Fermer", style=discord.ButtonStyle.danger, emoji="❌")
    async def close_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=create_embed("Menu fermé", "Le menu est fermé.", ERROR_COLOR), view=None)


@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.roles == after.roles:
        return
    rank_bl = is_rank_blacklisted(after.guild.id, after.id)
    if rank_bl:
        await remove_dangerous_roles(after, reason=f"Membre blrank : {rank_bl['reason'] or 'Aucune raison'}")


@bot.event
async def on_command_error(ctx, error):
    error = getattr(error, "original", error)

    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        usage = USAGES.get(ctx.command.name, f"+{ctx.command.name}")
        return await ctx.reply(embed=invalid_usage_embed(usage))
    if isinstance(error, commands.BadArgument):
        usage = USAGES.get(ctx.command.name)
        if usage:
            return await ctx.reply(embed=invalid_usage_embed(usage))
        return await ctx.reply("Argument invalide.")
    if isinstance(error, commands.MemberNotFound):
        return await ctx.reply("Membre introuvable.")
    if isinstance(error, commands.UserNotFound):
        return await ctx.reply("Utilisateur introuvable.")
    if isinstance(error, commands.CheckFailure):
        return await ctx.reply(str(error))
    if isinstance(error, discord.Forbidden):
        return await ctx.reply("Je n'ai pas les permissions nécessaires pour faire ça.")
    if isinstance(error, discord.HTTPException):
        return await ctx.reply("Discord a refusé l'action ou une erreur API est arrivée.")

    print(type(error), error)
    await ctx.reply("Une erreur interne est arrivée. Regarde la console.")


@bot.before_invoke
async def blacklist_check(ctx):
    if not ctx.guild:
        return
    if await is_bot_owner_user(ctx.author):
        return
    if ctx.author.guild_permissions.administrator:
        return

    user_bl = is_user_blacklisted(ctx.guild.id, ctx.author.id)
    if user_bl:
        raise commands.CheckFailure(f"Tu es blacklist du bot.\nRaison : {user_bl['reason'] or 'Aucune raison'}")

    role_bl = has_blacklisted_role(ctx.author)
    if role_bl:
        raise commands.CheckFailure(f"Ton rôle est blacklist du bot.\nRaison : {role_bl['reason'] or 'Aucune raison'}")


@bot.command()
async def panel(ctx: commands.Context):
    if not await require_access(ctx, "panel"):
        return
    view = PermissionPanel()
    await ctx.reply(embed=view.build_embed(ctx.guild), view=view)


@bot.command()
async def setroleperm(ctx: commands.Context, role: discord.Role, level: int):
    if not await require_access(ctx, "setroleperm"):
        return
    if level < 0 or level > 10:
        return await ctx.reply("Le niveau doit être entre `0` et `10`.")
    cursor.execute("INSERT OR REPLACE INTO role_perm_levels (guild_id, role_id, perm_level) VALUES (?, ?, ?)", (str(ctx.guild.id), str(role.id), level))
    db.commit()
    await ctx.reply(f"Le rôle {role.mention} est maintenant au niveau `Perm {level}`.")


@bot.command()
async def delroleperm(ctx: commands.Context, role: discord.Role):
    if not await require_access(ctx, "delroleperm"):
        return
    cursor.execute("DELETE FROM role_perm_levels WHERE guild_id = ? AND role_id = ?", (str(ctx.guild.id), str(role.id)))
    db.commit()
    await ctx.reply(f"Le niveau personnalisé du rôle {role.mention} a été supprimé.")


@bot.command()
async def setcmdperm(ctx: commands.Context, command_name: str, level: int):
    if not await require_access(ctx, "setcmdperm"):
        return
    command_name = command_name.lower().replace("+", "")
    if command_name not in COMMANDS_LIST:
        return await ctx.reply("Commande inconnue.")
    if level < 0 or level > 10:
        return await ctx.reply("Le niveau doit être entre `0` et `10`.")
    cursor.execute("INSERT OR REPLACE INTO command_perm_levels (guild_id, command_name, perm_level) VALUES (?, ?, ?)", (str(ctx.guild.id), command_name, level))
    db.commit()
    await ctx.reply(f"La commande `+{command_name}` est maintenant en `Perm {level}`.")


@bot.command()
async def resetcmdperm(ctx: commands.Context, command_name: str):
    if not await require_access(ctx, "resetcmdperm"):
        return
    command_name = command_name.lower().replace("+", "")
    cursor.execute("DELETE FROM command_perm_levels WHERE guild_id = ? AND command_name = ?", (str(ctx.guild.id), command_name))
    db.commit()
    await ctx.reply(f"La commande `+{command_name}` a été réinitialisée.")


@bot.command()
async def delperm(ctx: commands.Context, role: discord.Role, command_name: str):
    if not await require_access(ctx, "delperm"):
        return
    command_name = command_name.lower().replace("+", "")
    cursor.execute("DELETE FROM command_permissions WHERE guild_id = ? AND command_name = ? AND role_id = ?", (str(ctx.guild.id), command_name, str(role.id)))
    db.commit()
    await ctx.reply(f"Permission retirée pour {role.mention} sur `+{command_name}`.")


@bot.command()
async def permsconfig(ctx: commands.Context):
    if not await require_access(ctx, "permsconfig"):
        return
    cursor.execute("SELECT role_id, perm_level FROM role_perm_levels WHERE guild_id = ? ORDER BY perm_level DESC", (str(ctx.guild.id),))
    role_rows = cursor.fetchall()
    cursor.execute("SELECT command_name, perm_level FROM command_perm_levels WHERE guild_id = ? ORDER BY perm_level ASC", (str(ctx.guild.id),))
    command_rows = cursor.fetchall()

    roles_text = ""
    for row in role_rows[:15]:
        role = ctx.guild.get_role(int(row["role_id"]))
        roles_text += f"{role.mention if role else row['role_id']} — `Perm {row['perm_level']}`\n"
    if not roles_text:
        roles_text = "Aucun rôle configuré."

    commands_text = ""
    for row in command_rows[:20]:
        commands_text += f"`+{row['command_name']}` — `Perm {row['perm_level']}`\n"
    if not commands_text:
        commands_text = "Aucune commande modifiée."

    embed = create_embed("Configuration des permissions", "Configuration actuelle.", MAIN_COLOR)
    embed.add_field(name="Rôles configurés", value=roles_text[:1024], inline=False)
    embed.add_field(name="Commandes modifiées", value=commands_text[:1024], inline=False)
    await ctx.reply(embed=embed)


@bot.command()
async def perms(ctx: commands.Context):
    if not await require_access(ctx, "perms"):
        return
    levels = {level: [] for level in range(1, 11)}
    for role in ctx.guild.roles:
        if role.is_default():
            continue
        custom = get_role_perm_level(ctx.guild.id, role.id)
        level = custom if custom is not None else get_role_auto_perm_level(role)
        levels.setdefault(level, []).append(role)

    desc = ""
    for level in range(1, 11):
        roles = levels.get(level, [])
        text = ", ".join(role.mention for role in roles[:8]) if roles else "`Aucun rôle`"
        desc += f"**Perm {level}**\n{text}\n\n"
    await ctx.reply(embed=create_embed("Permissions", desc[:4096], MAIN_COLOR))


@bot.command()
async def bl(ctx: commands.Context, user: Optional[str] = None, *, reason: Optional[str] = None):
    if not await require_access(ctx, "bl"):
        return
    if not user:
        return await ctx.reply(embed=invalid_usage_embed(USAGES["bl"]))

    target = await get_member_or_user(ctx, user)
    if not target:
        return await ctx.reply("Utilisateur introuvable.")
    if target.id == ctx.author.id:
        return await ctx.reply("Tu ne peux pas te blacklist toi-même.")
    if target.id == bot.user.id:
        return await ctx.reply("Tu ne peux pas blacklist le bot.")
    if isinstance(target, discord.Member):
        ok, msg = can_act_on_member(ctx, target)
        if not ok:
            return await ctx.reply(msg)

    reason = reason or "Aucune raison"
    cursor.execute("INSERT OR REPLACE INTO blacklisted_users (guild_id, user_id, reason, moderator_id, created_at) VALUES (?, ?, ?, ?, ?)", (str(ctx.guild.id), str(target.id), reason, str(ctx.author.id), int(time.time())))
    db.commit()
    sanction_id = log_sanction(ctx.guild.id, "blacklist", target.id, ctx.author.id, reason)

    await ctx.reply(embed=error_embed("Membre blacklist", f"""
**Utilisateur :** <@{target.id}>
**ID :** `{target.id}`
**Modérateur :** {ctx.author.mention}
**Raison :** {reason}
**ID sanction :** `{sanction_id}`
"""))


@bot.command()
async def unbl(ctx: commands.Context, user: Optional[str] = None):
    if not await require_access(ctx, "unbl"):
        return
    if not user:
        return await ctx.reply(embed=invalid_usage_embed(USAGES["unbl"]))

    target = await get_member_or_user(ctx, user)
    if not target:
        return await ctx.reply("Utilisateur introuvable.")

    cursor.execute("DELETE FROM blacklisted_users WHERE guild_id = ? AND user_id = ?", (str(ctx.guild.id), str(target.id)))
    db.commit()
    if cursor.rowcount == 0:
        return await ctx.reply(f"<@{target.id}> n'était pas blacklist.")

    await ctx.reply(embed=success_embed("Blacklist retirée", f"""
**Utilisateur :** <@{target.id}>
**ID :** `{target.id}`
**Modérateur :** {ctx.author.mention}
"""))


@bot.command()
async def blinfo(ctx: commands.Context, user: Optional[str] = None):
    if not await require_access(ctx, "blinfo"):
        return
    if not user:
        return await ctx.reply(embed=invalid_usage_embed(USAGES["blinfo"]))

    target = await get_member_or_user(ctx, user)
    if not target:
        return await ctx.reply("Utilisateur introuvable.")

    cursor.execute("SELECT reason, moderator_id, created_at FROM blacklisted_users WHERE guild_id = ? AND user_id = ?", (str(ctx.guild.id), str(target.id)))
    row = cursor.fetchone()
    if not row:
        return await ctx.reply(embed=success_embed("Informations blacklist", f"<@{target.id}> n'est pas blacklist."))

    await ctx.reply(embed=error_embed("Informations blacklist", f"""
**Utilisateur :** <@{target.id}>
**ID :** `{target.id}`
**Raison :** {row['reason'] or 'Aucune raison'}
**Modérateur :** <@{row['moderator_id']}>
**Date :** <t:{row['created_at']}:F>
"""))


@bot.command()
async def kick(ctx: commands.Context, user: Optional[str] = None, *, reason: Optional[str] = None):
    if not await require_access(ctx, "kick"):
        return
    if not user:
        return await ctx.reply(embed=invalid_usage_embed(USAGES["kick"]))

    target = await get_member_or_user(ctx, user)
    if not target or not isinstance(target, discord.Member):
        return await ctx.reply("Membre introuvable sur ce serveur.")

    ok, msg = can_act_on_member(ctx, target)
    if not ok:
        return await ctx.reply(msg)
    if not ctx.guild.me.guild_permissions.kick_members:
        return await ctx.reply("Je n'ai pas la permission d'expulser des membres.")

    reason = reason or "Aucune raison"
    await target.kick(reason=reason)
    sanction_id = log_sanction(ctx.guild.id, "kick", target.id, ctx.author.id, reason)

    await ctx.reply(embed=error_embed("Membre expulsé", f"""
**Utilisateur :** <@{target.id}>
**ID :** `{target.id}`
**Modérateur :** {ctx.author.mention}
**Raison :** {reason}
**ID sanction :** `{sanction_id}`
"""))


@bot.command()
async def ban(ctx: commands.Context, user: Optional[str] = None, *, reason: Optional[str] = None):
    if not await require_access(ctx, "ban"):
        return
    if not user:
        return await ctx.reply(embed=invalid_usage_embed(USAGES["ban"]))

    target = await get_member_or_user(ctx, user)
    if not target:
        return await ctx.reply("Utilisateur introuvable.")

    if isinstance(target, discord.Member):
        ok, msg = can_act_on_member(ctx, target)
        if not ok:
            return await ctx.reply(msg)
    if not ctx.guild.me.guild_permissions.ban_members:
        return await ctx.reply("Je n'ai pas la permission de bannir des membres.")

    reason = reason or "Aucune raison"
    await ctx.guild.ban(target, reason=reason)
    sanction_id = log_sanction(ctx.guild.id, "ban", target.id, ctx.author.id, reason)

    await ctx.reply(embed=error_embed("Membre banni", f"""
**Utilisateur :** <@{target.id}>
**ID :** `{target.id}`
**Modérateur :** {ctx.author.mention}
**Raison :** {reason}
**ID sanction :** `{sanction_id}`
"""))


@bot.command()
async def unban(ctx: commands.Context, user_id: Optional[int] = None, *, reason: Optional[str] = None):
    if not await require_access(ctx, "unban"):
        return
    if not user_id:
        return await ctx.reply(embed=invalid_usage_embed(USAGES["unban"]))
    if not ctx.guild.me.guild_permissions.ban_members:
        return await ctx.reply("Je n'ai pas la permission de débannir des membres.")

    reason = reason or "Aucune raison"
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=reason)
    except discord.NotFound:
        return await ctx.reply("Cet utilisateur n'est pas banni ou est introuvable.")
    except discord.HTTPException:
        return await ctx.reply("Impossible de débannir cet utilisateur.")

    await ctx.reply(embed=success_embed("Membre débanni", f"""
**Utilisateur :** <@{user_id}>
**ID :** `{user_id}`
**Modérateur :** {ctx.author.mention}
**Raison :** {reason}
"""))


@bot.command()
async def baninfo(ctx: commands.Context, user_id: Optional[int] = None):
    if not await require_access(ctx, "baninfo"):
        return
    if not user_id:
        return await ctx.reply(embed=invalid_usage_embed(USAGES["baninfo"]))

    try:
        user = await bot.fetch_user(user_id)
        ban_entry = await ctx.guild.fetch_ban(user)
        cursor.execute("SELECT id, reason, moderator_id, created_at FROM sanctions WHERE guild_id = ? AND user_id = ? AND type = 'ban' ORDER BY id DESC LIMIT 1", (str(ctx.guild.id), str(user_id)))
        row = cursor.fetchone()
        extra = ""
        if row:
            extra = f"""
**ID sanction :** `{row['id']}`
**Modérateur bot :** <@{row['moderator_id']}>
**Date enregistrée :** <t:{row['created_at']}:F>
"""
        await ctx.reply(embed=error_embed("Informations ban", f"""
**Utilisateur :** {ban_entry.user}
**ID :** `{ban_entry.user.id}`
**Raison Discord :** {ban_entry.reason or 'Aucune raison'}
{extra}
"""))
    except discord.NotFound:
        await ctx.reply("Cet utilisateur n'est pas banni.")


@bot.command()
async def warn(ctx: commands.Context, member: discord.Member, *, reason: str):
    if not await require_access(ctx, "warn"):
        return
    cursor.execute("INSERT INTO warns (guild_id, user_id, moderator_id, reason, created_at) VALUES (?, ?, ?, ?, ?)", (str(ctx.guild.id), str(member.id), str(ctx.author.id), reason, int(time.time())))
    db.commit()
    log_sanction(ctx.guild.id, "warn", member.id, ctx.author.id, reason)
    cursor.execute("SELECT COUNT(*) AS total FROM warns WHERE guild_id = ? AND user_id = ?", (str(ctx.guild.id), str(member.id)))
    total_warns = cursor.fetchone()["total"]
    await ctx.reply(f"{member.mention} a reçu un avertissement.\nRaison : {reason}\nTotal de warns : {total_warns}")


@bot.command()
async def unwarn(ctx: commands.Context, member: discord.Member):
    if not await require_access(ctx, "unwarn"):
        return
    cursor.execute("SELECT id FROM warns WHERE guild_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1", (str(ctx.guild.id), str(member.id)))
    warn_row = cursor.fetchone()
    if not warn_row:
        return await ctx.reply(f"{member.mention} n'a aucun warn.")
    cursor.execute("DELETE FROM warns WHERE id = ?", (warn_row["id"],))
    db.commit()
    await ctx.reply(f"Le dernier warn de {member.mention} a été supprimé.")


@bot.command()
async def mute(ctx: commands.Context, member: discord.Member, minutes: int, *, reason="Aucune raison"):
    if not await require_access(ctx, "mute"):
        return
    if minutes < 1 or minutes > 40320:
        return await ctx.reply("La durée doit être entre 1 et 40320 minutes.")
    ok, msg = can_act_on_member(ctx, member)
    if not ok:
        return await ctx.reply(msg)
    if not ctx.guild.me.guild_permissions.moderate_members:
        return await ctx.reply("Je n'ai pas la permission de modérer les membres.")

    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until, reason=reason)
    expires_at = int(time.time()) + minutes * 60
    log_sanction(ctx.guild.id, "mute", member.id, ctx.author.id, reason, expires_at)
    await ctx.reply(f"{member.mention} a été mute pendant **{minutes} minute(s)**.\nRaison : {reason}")


@bot.command()
async def unmute(ctx: commands.Context, member: discord.Member, *, reason="Aucune raison"):
    if not await require_access(ctx, "unmute"):
        return
    if not ctx.guild.me.guild_permissions.moderate_members:
        return await ctx.reply("Je n'ai pas la permission de modérer les membres.")
    await member.timeout(None, reason=reason)
    await ctx.reply(f"{member.mention} a été unmute.\nRaison : {reason}")


@bot.command()
async def blrank(ctx: commands.Context, member: discord.Member, *, reason="Aucune raison"):
    if not await require_access(ctx, "blrank"):
        return
    cursor.execute("INSERT OR REPLACE INTO rank_blacklisted_users (guild_id, user_id, reason, moderator_id, created_at) VALUES (?, ?, ?, ?, ?)", (str(ctx.guild.id), str(member.id), reason, str(ctx.author.id), int(time.time())))
    db.commit()
    removed_roles = await remove_dangerous_roles(member, reason=f"Blrank par {ctx.author} : {reason}")
    removed = ", ".join(role.mention for role in removed_roles) if removed_roles else "Aucun rôle dangereux retiré."
    await ctx.reply(f"{member.mention} est maintenant **blrank**.\n{removed}\nRaison : {reason}")


@bot.command()
async def unblrank(ctx: commands.Context, member: discord.Member):
    if not await require_access(ctx, "unblrank"):
        return
    cursor.execute("DELETE FROM rank_blacklisted_users WHERE guild_id = ? AND user_id = ?", (str(ctx.guild.id), str(member.id)))
    db.commit()
    if cursor.rowcount == 0:
        return await ctx.reply(f"{member.mention} n'était pas blrank.")
    await ctx.reply(f"{member.mention} n'est plus blrank.")


@bot.command()
async def lock(ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
    if not await require_access(ctx, "lock"):
        return
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=False, reason=f"Salon verrouillé par {ctx.author}")
    await ctx.reply(embed=error_embed("Salon verrouillé", f"Le salon {channel.mention} a été verrouillé."))


@bot.command()
async def unlock(ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
    if not await require_access(ctx, "unlock"):
        return
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=None, reason=f"Salon déverrouillé par {ctx.author}")
    await ctx.reply(embed=success_embed("Salon déverrouillé", f"Le salon {channel.mention} a été déverrouillé."))


@bot.command()
async def clear(ctx: commands.Context, amount: int):
    if not await require_access(ctx, "clear"):
        return
    if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:
        return await ctx.reply("Je n'ai pas la permission `Gérer les messages` dans ce salon.")
    if amount < 1:
        return await ctx.reply("Tu dois indiquer un nombre supérieur à `0`.")
    if amount > 100:
        return await ctx.reply("Tu ne peux pas supprimer plus de `100` messages à la fois.")
    deleted = await ctx.channel.purge(limit=amount + 1, reason=f"Clear par {ctx.author}")
    confirmation = await ctx.send(f"✅ `{max(len(deleted) - 1, 0)}` message(s) supprimé(s).")
    await confirmation.delete(delay=3)


@bot.command()
async def info(ctx: commands.Context):
    if not await require_access(ctx, "info"):
        return
    await ctx.reply(embed=create_embed("Guide staff", """
**Règles staff :**
- Reste calme et professionnel.
- Vérifie le contexte avant d'agir.
- Garde des preuves si possible.

**Commandes utiles :**
`+warn @user raison`
`+mute @user minutes raison`
`+kick @user raison`
`+ban @user raison`
`+bl @user raison`
`+sanctions @user`
""", MAIN_COLOR))


@bot.command()
async def delsanction(ctx: commands.Context, sanction_id: int):
    if not await require_access(ctx, "delsanction"):
        return
    cursor.execute("SELECT * FROM sanctions WHERE guild_id = ? AND id = ?", (str(ctx.guild.id), sanction_id))
    sanction = cursor.fetchone()
    if not sanction:
        return await ctx.reply("Aucune sanction trouvée avec cet ID.")
    cursor.execute("DELETE FROM sanctions WHERE guild_id = ? AND id = ?", (str(ctx.guild.id), sanction_id))
    db.commit()
    await ctx.reply(f"La sanction `{sanction_id}` a été supprimée.")


@bot.command()
async def clearsanctions(ctx: commands.Context, member: discord.Member):
    if not await require_access(ctx, "clearsanctions"):
        return
    cursor.execute("DELETE FROM sanctions WHERE guild_id = ? AND user_id = ?", (str(ctx.guild.id), str(member.id)))
    cursor.execute("DELETE FROM warns WHERE guild_id = ? AND user_id = ?", (str(ctx.guild.id), str(member.id)))
    db.commit()
    await ctx.reply(f"Toutes les sanctions de {member.mention} ont été supprimées.")


@bot.command()
async def sanctions(ctx: commands.Context, member: discord.Member):
    if not await require_access(ctx, "sanctions"):
        return
    cursor.execute("SELECT id, type, moderator_id, reason, created_at, expires_at FROM sanctions WHERE guild_id = ? AND user_id = ? ORDER BY id DESC LIMIT 10", (str(ctx.guild.id), str(member.id)))
    rows = cursor.fetchall()
    if not rows:
        return await ctx.reply(f"{member.mention} n'a aucune sanction enregistrée.")
    desc = ""
    for row in rows:
        expires = f"\nExpire : <t:{row['expires_at']}:R>" if row["expires_at"] else ""
        desc += f"**ID :** `{row['id']}` | **Type :** `{row['type']}`\n**Modérateur :** <@{row['moderator_id']}>\n**Raison :** {row['reason'] or 'Aucune raison'}\n**Date :** <t:{row['created_at']}:F>{expires}\n\n"
    await ctx.reply(embed=create_embed(f"Sanctions de {member}", desc[:4096], WARNING_COLOR))


@bot.command()
async def avatar(ctx: commands.Context, user: Optional[discord.User] = None):
    if not await require_access(ctx, "avatar"):
        return
    user = user or ctx.author
    embed = create_embed("Avatar utilisateur", f"Avatar de {user.mention}.")
    embed.set_image(url=user.display_avatar.url)
    await ctx.reply(embed=embed)


@bot.command()
async def banner(ctx: commands.Context, user: Optional[discord.User] = None):
    if not await require_access(ctx, "banner"):
        return
    user = user or ctx.author
    fetched_user = await bot.fetch_user(user.id)
    if not fetched_user.banner:
        return await ctx.reply("Cet utilisateur n'a pas de bannière.")
    embed = create_embed("Bannière utilisateur", f"Bannière de {fetched_user.mention}.")
    embed.set_image(url=fetched_user.banner.url)
    await ctx.reply(embed=embed)


@bot.command()
async def userinfo(ctx: commands.Context, member: Optional[discord.Member] = None):
    if not await require_access(ctx, "userinfo"):
        return
    member = member or ctx.author
    joined_at = int(member.joined_at.timestamp()) if member.joined_at else int(member.created_at.timestamp())
    embed = create_embed("Informations utilisateur", f"""
**Utilisateur :** {member.mention}
**ID :** `{member.id}`
**Compte créé :** <t:{int(member.created_at.timestamp())}:F>
**Arrivé sur le serveur :** <t:{joined_at}:F>
**Rôle le plus haut :** {member.top_role.mention}
""")
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.reply(embed=embed)


@bot.command()
async def serverinfo(ctx: commands.Context):
    if not await require_access(ctx, "serverinfo"):
        return
    guild = ctx.guild
    embed = create_embed("Informations serveur", f"""
**Nom :** {guild.name}
**ID :** `{guild.id}`
**Propriétaire :** {guild.owner.mention if guild.owner else 'Inconnu'}
**Membres :** {guild.member_count}
**Salons :** {len(guild.channels)}
**Rôles :** {len(guild.roles)}
**Création :** <t:{int(guild.created_at.timestamp())}:F>
""")
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.reply(embed=embed)


@bot.command()
async def wlowner(ctx: commands.Context, user: discord.User):
    if not await is_bot_owner_user(ctx.author):
        return await ctx.reply("Cette commande est réservée aux owners du bot.")
    cursor.execute("INSERT OR REPLACE INTO owner_whitelist (user_id, added_by, created_at) VALUES (?, ?, ?)", (str(user.id), str(ctx.author.id), int(time.time())))
    db.commit()
    await ctx.reply(f"{user.mention} est maintenant dans la whitelist owner du bot.")


@bot.command()
async def unwlowner(ctx: commands.Context, user: discord.User):
    if not await is_bot_owner_user(ctx.author):
        return await ctx.reply("Cette commande est réservée aux owners du bot.")
    if user.id == ctx.author.id and not await bot.is_owner(ctx.author):
        return await ctx.reply("Tu ne peux pas te retirer toi-même de la whitelist owner.")
    cursor.execute("DELETE FROM owner_whitelist WHERE user_id = ?", (str(user.id),))
    db.commit()
    if cursor.rowcount == 0:
        return await ctx.reply(f"{user.mention} n'était pas dans la whitelist owner.")
    await ctx.reply(f"{user.mention} a été retiré de la whitelist owner du bot.")


@bot.command()
async def ownerlist(ctx: commands.Context):
    if not await is_bot_owner_user(ctx.author):
        return await ctx.reply("Cette commande est réservée aux owners du bot.")
    cursor.execute("SELECT user_id, added_by, created_at FROM owner_whitelist ORDER BY created_at ASC")
    rows = cursor.fetchall()
    desc = "**Owner principal :** propriétaire de l'application Discord\n\n"
    if not rows:
        desc += "Aucun utilisateur dans la whitelist owner."
    else:
        for row in rows:
            desc += f"• <@{row['user_id']}> — ajouté par <@{row['added_by']}> le <t:{row['created_at']}:F>\n"
    await ctx.reply(embed=create_embed("Whitelist owner du bot", desc, WARNING_COLOR))


@bot.command()
async def helpall(ctx: commands.Context):
    pages = [
        ("📚 Aide générale", "`+help` — Aide principale\n`+helpall` — Menu complet\n`+panel` — Panel permissions"),
        ("⛔ Blacklist", "`+bl @user/id raison`\n`+unbl @user/id`\n`+blinfo @user/id`\n`+blrank @membre raison`\n`+unblrank @membre`"),
        ("🔨 Kick / Ban", "`+kick @user/id raison`\n`+ban @user/id raison`\n`+unban user_id raison`\n`+baninfo user_id`"),
        ("🛡️ Modération", "`+warn @membre raison`\n`+unwarn @membre`\n`+mute @membre minutes raison`\n`+unmute @membre raison`\n`+clear nombre`\n`+lock #salon`\n`+unlock #salon`"),
        ("⚙️ Administration", "`+setroleperm @rôle niveau`\n`+delroleperm @rôle`\n`+setcmdperm commande niveau`\n`+resetcmdperm commande`\n`+permsconfig`\n`+wlowner @user`\n`+unwlowner @user`\n`+ownerlist`"),
    ]
    view = SimplePagesView(ctx.author, pages)
    await ctx.reply(embed=view.build_embed(), view=view)


@bot.command(name="help")
async def help_command(ctx: commands.Context):
    embed = create_embed("Aide du bot sanctions", "Voici les commandes principales du bot.", MAIN_COLOR)
    embed.add_field(name="⛔ Blacklist", value="`+bl @user/id raison`\n`+unbl @user/id`\n`+blinfo @user/id`", inline=False)
    embed.add_field(name="🔨 Kick / Ban", value="`+kick @user/id raison`\n`+ban @user/id raison`\n`+unban user_id raison`\n`+baninfo user_id`", inline=False)
    embed.add_field(name="🛡️ Modération", value="`+warn @membre raison`\n`+mute @membre minutes raison`\n`+clear nombre`\n`+lock #salon`\n`+unlock #salon`\n`+sanctions @membre`", inline=False)
    embed.add_field(name="⚙️ Administration", value="`+panel`\n`+setroleperm @rôle niveau`\n`+setcmdperm commande niveau`\n`+permsconfig`\n`+ownerlist`", inline=False)
    await ctx.reply(embed=embed)


if __name__ == "__main__":
    init_db()
    token = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("Ajoute ton token dans le fichier .env avec TOKEN=ton_token")
    bot.run(token)
