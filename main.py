import os
import discord
from discord.ext import tasks

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("===================================")
    print(f"Connecté en tant que {client.user}")
    print("===================================")

    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("Salon introuvable")
        return

    print("Salon trouvé")

    await channel.send("✅ Le bot fonctionne !")

client.run(TOKEN)
