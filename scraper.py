from playwright.async_api import async_playwright

URL = "https://wzstats.gg/fr"

async def get_meta():

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=True)

        page = await browser.new_page()

        await page.goto(URL, wait_until="networkidle")

        text = await page.locator("body").inner_text()

        await browser.close()

        weapons = []

        for line in text.split("\n"):

            line = line.strip()

            if len(line) > 2:
                weapons.append(line)

        return weapons
