import os
import discord

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Connecté : {client.user}")

    try:
        channel = await client.fetch_channel(CHANNEL_ID)

        await channel.send("✅ Le bot fonctionne !")

        print("Message envoyé")

    except Exception as e:
        print(e)

client.run(TOKEN)
