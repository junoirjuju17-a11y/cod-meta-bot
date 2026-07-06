import os
import discord

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Connecté : {client.user}")

    print("Serveurs :")
    for guild in client.guilds:
        print(f"- {guild.name} ({guild.id})")

        print("Salons :")
        for ch in guild.text_channels:
            print(f"  {ch.name} -> {ch.id}")

    try:
        channel = client.get_channel(CHANNEL_ID)

        if channel is None:
            print("❌ Salon introuvable")
            return

        await channel.send("✅ Test du bot réussi !")
        print("✅ Message envoyé")

    except Exception as e:
        print(e)

client.run(TOKEN)
