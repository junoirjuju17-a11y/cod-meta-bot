import aiohttp
from bs4 import BeautifulSoup

URL = "https://wzstats.gg/fr"

async def get_meta():

    async with aiohttp.ClientSession() as session:
        async with session.get(URL, headers={
            "User-Agent":"Mozilla/5.0"
        }) as r:

            html = await r.text()

    soup = BeautifulSoup(html,"lxml")

    weapons=[]

    for h3 in soup.find_all("h3"):

        name=h3.get_text(strip=True)

        if len(name)>2:
            weapons.append(name)

    return list(dict.fromkeys(weapons))
