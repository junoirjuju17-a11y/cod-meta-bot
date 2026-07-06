import os
import discord

TOKEN = os.getenv("DISCORD_TOKEN")
guild = client.guilds[0]
print(f"Serveur : {guild.name} ({guild.id})")

for ch in guild.text_channels:
    print(f"{ch.name} -> {ch.id}")

channel = guild.get_channel(CHANNEL_ID)
intents = discord.Intents.default()

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Connecté : {client.user}")

    channel = await client.fetch_channel(CHANNEL_ID)
    await channel.send("✅ Le bot fonctionne !")

    await client.close()

client.run(TOKEN)
