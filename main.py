import os
import traceback
import discord

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print("=" * 50)
    print(f"Connecté en tant que : {client.user}")
    print("=" * 50)

    print("\nSERVEURS DU BOT :\n")

    for guild in client.guilds:
        print(f"Serveur : {guild.name}")
        print(f"ID : {guild.id}")
        print("-" * 30)

        for channel in guild.text_channels:
            print(f"{channel.name} -> {channel.id}")

        print()

    print("=" * 50)
    print(f"Recherche du salon : {CHANNEL_ID}")
    print("=" * 50)

    try:

        channel = client.get_channel(CHANNEL_ID)

        if channel is None:
            print("Le salon n'est pas dans le cache.")
            print("Tentative avec fetch_channel...")

            channel = await client.fetch_channel(CHANNEL_ID)

        print(f"Salon trouvé : {channel.name}")

        await channel.send("✅ TEST : le bot fonctionne correctement !")

        print("Message envoyé avec succès.")

    except Exception:
        print("\nERREUR :")
        traceback.print_exc()


client.run(TOKEN)
