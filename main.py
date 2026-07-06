import os
import discord

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Connecté : {client.user}")

    channel = await client.fetch_channel(CHANNEL_ID)
    await channel.send("✅ Le bot fonctionne !")

    await client.close()

client.run(TOKEN)
