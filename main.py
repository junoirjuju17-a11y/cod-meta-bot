import os
import json
import discord
from discord.ext import tasks
from scraper import get_meta

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

DB_FILE = "published.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@client.event
async def on_ready():
    print(f"✅ Connecté en tant que {client.user}")

    channel = client.get_channel(CHANNEL_ID)

    if channel:
        await channel.send("✅ COD Meta Bot est en ligne !")

    check_meta.start()
@tasks.loop(minutes=30)
async def check_meta():
    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("❌ Salon introuvable")
        return

    old = load_db()

    try:
        weapons = await get_meta()

        for weapon in weapons:
            if weapon not in old:

                embed = discord.Embed(
                    title="🔥 Nouvelle arme méta",
                    description=f"**{weapon}** est maintenant dans la méta.",
                    color=0xff6600
                )

                embed.add_field(
                    name="Source",
                    value="https://wzstats.gg/fr",
                    inline=False
                )

                await channel.send(embed=embed)

                old.append(weapon)

        save_db(old)

    except Exception as e:
        print(e)

client.run(TOKEN)
