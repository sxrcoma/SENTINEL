import discord
from discord.ext import commands
import sqlite3
from datetime import datetime
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- DATABASE ----------
def init_ban_db():
    conn = sqlite3.connect("ban_tracker.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            guild_id INTEGER,
            channel_id INTEGER,
            reason TEXT,
            banned_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def track_ban(user_id, username, guild_id, channel_id, reason):
    conn = sqlite3.connect("ban_tracker.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bans (user_id, username, guild_id, channel_id, reason, banned_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        username,
        guild_id,
        channel_id,
        reason,
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

def get_ban_count():
    conn = sqlite3.connect("ban_tracker.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM bans")
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_recent_bans(limit=5):
    conn = sqlite3.connect("ban_tracker.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT username, user_id, reason, banned_at
        FROM bans
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    print("BOT ONLINE")
    init_ban_db()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    TARGET_CHANNEL_ID = 1496565527554822254

    if message.channel.id == TARGET_CHANNEL_ID:
        try:
            await message.author.ban(reason="Spam channel rule")

            track_ban(
                user_id=message.author.id,
                username=str(message.author),
                guild_id=message.guild.id if message.guild else 0,
                channel_id=message.channel.id,
                reason="Spam channel rule"
            )

        except Exception as e:
            print("BAN FAILED:", e)

    await bot.process_commands(message)

# ---------- COMMANDS ----------
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def bancount(ctx):
    await ctx.send(f"Total tracked bans: {get_ban_count()}")

@bot.command()
async def recentbans(ctx):
    rows = get_recent_bans(5)

    if not rows:
        await ctx.send("No tracked bans yet.")
        return

    msg = "\n".join(
        f"{username} ({user_id}) | {reason} | {banned_at}"
        for username, user_id, reason, banned_at in rows
    )

    await ctx.send(f"Recent bans:\n{msg}")

# ---------- START BOT ----------
bot.run(os.getenv("DISCORD_TOKEN"))