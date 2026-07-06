import os
import discord

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Connecté : {client.user}")

    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("Salon introuvable")
        return

    await channel.send("✅ Le bot fonctionne !")

    print("Message envoyé !")

client.run(TOKEN)
