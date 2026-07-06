import os
import discord
from discord.ext import tasks
from scraper import get_meta
from database import Database

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()

client = discord.Client(intents=intents)

db = Database()


@client.event
async def on_ready():
    print("=" * 60)
    print(f"Bot connecté : {client.user}")
    print("=" * 60)

    if not check_meta.is_running():
        check_meta.start()


@tasks.loop(minutes=10)
async def check_meta():

    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("Salon introuvable")
        return

    try:

        metas = await get_meta()

        if len(metas) == 0:
            print("Aucune arme récupérée.")
            return

        for weapon in metas:

            if db.exists(weapon["name"]):
                continue

            embed = discord.Embed(
                title="🔥 Nouvelle arme META",
                description=weapon["name"],
                colour=0xff5500
            )

            embed.add_field(
                name="Tier",
                value=weapon["tier"],
                inline=True
            )

            embed.add_field(
                name="Type",
                value=weapon["type"],
                inline=True
            )

            embed.add_field(
                name="Source",
                value="https://wzstats.gg/fr",
                inline=False
            )

            if weapon["image"] != "":
                embed.set_thumbnail(url=weapon["image"])

            await channel.send(embed=embed)

            db.add(weapon["name"])

            print("Nouvelle arme :", weapon["name"])

    except Exception as e:
        print(e)


client.run(TOKEN)
