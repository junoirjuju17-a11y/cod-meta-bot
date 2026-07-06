import os
import discord
from discord.ext import tasks
from scraper import get_meta

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()

client = discord.Client(intents=intents)

last_meta = None


@client.event
async def on_ready():
    print(f"✅ Connecté : {client.user}")

    if not check_meta.is_running():
        check_meta.start()


@tasks.loop(minutes=10)
async def check_meta():
    global last_meta

    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("❌ Salon introuvable")
        return

    try:
        weapons = await get_meta()

        if not weapons:
            print("Aucune arme trouvée.")
            return

        current = weapons[0]

        if last_meta is None:
            last_meta = current
            print(f"Méta actuelle : {current}")
            return

        if current != last_meta:
            last_meta = current

            await channel.send(
                f"🔥 **Nouvelle arme META détectée !**\n\n"
                f"**{current}**\n\n"
                f"https://wzstats.gg/fr"
            )

            print("Nouvelle méta envoyée.")

    except Exception as e:
        print(e)


client.run(TOKEN)
