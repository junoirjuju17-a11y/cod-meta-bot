import os
import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup

TOKEN=os.getenv("DISCORD_TOKEN")
CHANNEL_ID=int(os.getenv("CHANNEL_ID","0"))

intents=discord.Intents.default()
client=discord.Client(intents=intents)
last_title=None

@tasks.loop(minutes=30)
async def check_meta():
    global last_title
    ch=client.get_channel(CHANNEL_ID)
    if not ch:
        return
    try:
        r=requests.get("https://wzstats.gg/",timeout=15,headers={"User-Agent":"Mozilla/5.0"})
        soup=BeautifulSoup(r.text,"html.parser")
        title=soup.title.text.strip()
        if title!=last_title:
            last_title=title
            await ch.send(f"🔥 Mise à jour détectée sur WZStats !\\nTitre : **{title}**\\nhttps://wzstats.gg/")
    except Exception as e:
        print(e)

@client.event
async def on_ready():
    print(f"Connecté : {client.user}")
    check_meta.start()

client.run(TOKEN)
