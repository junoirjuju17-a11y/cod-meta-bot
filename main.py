import os
import discord

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("=" * 60)
    print("BOT CONNECTÉ")
    print("=" * 60)

    for guild in client.guilds:
        print(f"\nServeur : {guild.name}")
        print(f"ID : {guild.id}")

        print("\nSALONS :")

        for channel in guild.channels:
            print(f"{channel.name} -> {channel.id}")

    await client.close()

client.run(TOKEN)
