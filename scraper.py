import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

from playwright.async_api import (
    Browser,
    Error as PlaywrightError,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)


logger = logging.getLogger("cod-meta-bot.scraper")


@dataclass(slots=True)
class Weapon:
    name: str
    tier: str
    weapon_type: str
    image_url: str
    url: str
    rank: int
    attachments: list[str] = field(default_factory=list)

    @property
    def identity(self) -> str:
        if self.url:
            return self.url.rstrip("/").casefold()
        return re.sub(r"\s+", "-", self.name.strip().casefold())


class WZStatsScraper:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    async def fetch_meta_weapons(self) -> list[Weapon]:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=self._browser_args(),
            )
            try:
                page = await self._new_page(browser, width=1365, height=900)
                try:
                    await page.goto(self.base_url, wait_until="domcontentloaded", timeout=45_000)
                    await self._wait_for_dynamic_content(page)

                    raw_weapons = await self._extract_from_page(page)
                    weapons = self._normalize_weapons(raw_weapons)

                    if not weapons:
                        logger.warning("No weapons extracted from WZStats")
                        return []

                    return weapons
                finally:
                    await page.context.close()
            finally:
                await browser.close()

    async def enrich_weapon(self, weapon: Weapon) -> Weapon:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=self._browser_args(),
            )
            try:
                page = await self._new_page(browser, width=1280, height=900)
                try:
                    await page.goto(weapon.url, wait_until="domcontentloaded", timeout=30_000)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=15_000)
                    except (PlaywrightTimeoutError, PlaywrightError):
                        logger.info("Detail page did not reach network idle for %s", weapon.name)
                    weapon.attachments = await self._extract_attachments(page)
                finally:
                    await page.context.close()
            finally:
                await browser.close()

        return weapon

    def _browser_args(self) -> list[str]:
        return [
            "--disable-background-networking",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-sync",
            "--disable-web-security",
            "--js-flags=--max-old-space-size=128",
            "--no-first-run",
            "--no-sandbox",
        ]

    async def _new_page(self, browser: Browser, width: int, height: int) -> Page:
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
        )
        async def block_heavy_resources(route):
            if route.request.resource_type in {"font", "image", "media"}:
                await route.abort()
                return
            await route.continue_()

        await context.route("**/*", block_heavy_resources)
        return await context.new_page()

    async def _wait_for_dynamic_content(self, page: Page) -> None:
        try:
            await page.wait_for_load_state("networkidle", timeout=30_000)
        except PlaywrightTimeoutError:
            logger.info("Network idle timeout reached; continuing with visible content")
        except PlaywrightError:
            logger.info("Network idle wait failed; continuing with loaded DOM", exc_info=True)

        candidates = [
            "a[href*='loadout']",
            "a[href*='weapon']",
            "a[href*='arme']",
            "img",
            "text=/META|Meta|meta/",
        ]

        for selector in candidates:
            try:
                await page.wait_for_selector(selector, timeout=8_000)
                return
            except (PlaywrightTimeoutError, PlaywrightError):
                continue

    async def _extract_from_page(self, page: Page) -> list[dict[str, Any]]:
        return await page.evaluate(
            """
            () => {
              const absoluteUrl = (value) => {
                if (!value) return "";
                try { return new URL(value, window.location.href).toString(); }
                catch { return ""; }
              };

              const clean = (value) => (value || "").replace(/\\s+/g, " ").trim();
              const tierMatch = (text) => {
                const value = clean(text);
                if (/^Warzone Meta$/i.test(value)) return "META";
                const match = value.match(/\\b(S\\+?|A\\+?|B\\+?|C\\+?|D\\+?)\\s*Tier\\b/i)
                  || value.match(/(?:Tier|Niveau|Rang)\\s*[:\\-]?\\s*(S\\+?|A\\+?|B\\+?|C\\+?|D\\+?)/i);
                if (match) return match[1].toUpperCase();
                return "";
              };

              const typeWords = [
                "Fusil d'assaut", "Mitraillette", "Fusil de précision", "Fusil tactique",
                "Fusil de combat", "Fusil à pompe", "Mitrailleuse", "Pistolet",
                "Assault Rifle", "SMG", "Sniper Rifle", "Marksman Rifle", "Battle Rifle",
                "Shotgun", "LMG", "Handgun", "Melee"
              ];
              const findType = (text) => typeWords.find((word) => clean(text).toLowerCase().includes(word.toLowerCase())) || "";

              const headings = [...document.querySelectorAll("h1, h2, h3")].filter((heading) => {
                const text = clean(heading.innerText || heading.textContent || "");
                return /^Warzone Meta$/i.test(text) || /\\b(S\\+?|A\\+?|B\\+?|C\\+?|D\\+?)\\s*Tier\\b/i.test(text);
              });

              const tierFor = (element) => {
                let tier = "";
                for (const heading of headings) {
                  const position = heading.compareDocumentPosition(element);
                  if (position & Node.DOCUMENT_POSITION_FOLLOWING) {
                    tier = tierMatch(heading.innerText || heading.textContent || "");
                  }
                }
                return tier;
              };

              const bestContainerFor = (anchor) => {
                let node = anchor;
                let best = anchor;
                for (let depth = 0; node && depth < 8; depth += 1) {
                  const text = clean(node.innerText || node.textContent || "");
                  const hasImage = Boolean(node.querySelector?.("img"));
                  const hasRank = /#\\d+\\s+/.test(text);
                  const hasType = Boolean(findType(text));
                  if (hasImage && (hasRank || hasType) && text.length < 900) best = node;
                  node = node.parentElement;
                }
                return best;
              };

              const nameFromLines = (lines, imageAlt) => {
                const blacklist = /^(mise à jour|new|nouveau|###)$/i;
                const candidates = lines.filter((line) => (
                  line.length > 1 &&
                  line.length < 48 &&
                  !blacklist.test(line) &&
                  !/^#\\d+/.test(line) &&
                  !/meilleures configurations/i.test(line) &&
                  !findType(line)
                ));
                const fromText = candidates.find((line) => /[A-Za-zÀ-ÿ0-9]/.test(line));
                if (fromText) return fromText;
                if (imageAlt) {
                  return imageAlt
                    .split("-")
                    .filter(Boolean)
                    .map((part) => part.length <= 3 ? part.toUpperCase() : part[0].toUpperCase() + part.slice(1))
                    .join(" ");
                }
                return "";
              };

              const cards = [];
              const anchors = [...document.querySelectorAll("a[href]")];
              for (const anchor of anchors) {
                const href = anchor.getAttribute("href") || "";
                const surrounding = bestContainerFor(anchor);
                const text = clean(surrounding.innerText || anchor.innerText || "");
                const image = surrounding.querySelector("img") || anchor.querySelector("img");
                const imageUrl = absoluteUrl(image?.currentSrc || image?.src || image?.getAttribute("src") || "");
                const nameFromImage = clean(image?.alt || "");
                const lines = text.split("\\n").map(clean).filter(Boolean);
                const name = nameFromLines(lines, nameFromImage);
                const url = absoluteUrl(href);
                const tier = tierMatch(text) || tierFor(surrounding);
                const weaponType = findType(text);

                if (!name || !url) continue;
                if (!imageUrl && !tier && !weaponType) continue;
                if (/(discord|twitter|x\\.com|youtube|privacy|login|connexion)/i.test(url)) continue;

                cards.push({ name, tier, weaponType, imageUrl, url, text });
              }

              return cards;
            }
            """
        )

    def _normalize_weapons(self, raw_weapons: list[dict[str, Any]]) -> list[Weapon]:
        weapons: list[Weapon] = []
        seen: set[str] = set()

        for item in raw_weapons:
            name = self._clean_name(str(item.get("name", "")))
            url = urljoin(self.base_url, str(item.get("url", ""))).split("#", 1)[0]
            if not name or not url:
                continue

            identity = url.rstrip("/").casefold()
            if identity in seen:
                continue

            tier = self._clean_tier(str(item.get("tier", "")))
            if tier and tier not in {"META", "S+", "S", "A+", "A", "B+", "B", "C+", "C", "D+", "D"}:
                tier = ""

            weapon = Weapon(
                name=name,
                tier=tier,
                weapon_type=self._clean_text(str(item.get("weaponType", ""))),
                image_url=urljoin(self.base_url, str(item.get("imageUrl", ""))),
                url=url,
                rank=len(weapons) + 1,
            )

            seen.add(identity)
            weapons.append(weapon)

        return weapons

    async def _enrich_weapon_details(self, browser: Browser, weapons: list[Weapon]) -> None:
        for weapon in weapons:
            try:
                await self._enrich_weapon_with_browser(browser, weapon)
            except Exception:
                logger.info("Unable to enrich weapon details for %s", weapon.name, exc_info=True)
            await asyncio.sleep(0.2)

    async def _enrich_weapon_with_browser(self, browser: Browser, weapon: Weapon) -> None:
        page = await self._new_page(browser, width=1280, height=900)
        try:
            await page.goto(weapon.url, wait_until="domcontentloaded", timeout=30_000)
            try:
                await page.wait_for_load_state("networkidle", timeout=15_000)
            except (PlaywrightTimeoutError, PlaywrightError):
                logger.info("Detail page did not reach network idle for %s", weapon.name)
            weapon.attachments = await self._extract_attachments(page)
        finally:
            await page.context.close()

    async def _extract_attachments(self, page: Page) -> list[str]:
        values = await page.evaluate(
            """
            () => {
              const clean = (value) => (value || "").replace(/\\s+/g, " ").trim();
              const labels = [
                "bouche", "canon", "laser", "lunette", "crosse", "chargeur",
                "munitions", "poignée", "accessoire", "muzzle", "barrel", "optic",
                "stock", "magazine", "ammunition", "underbarrel", "rear grip"
              ];
              const blocks = [...document.querySelectorAll("li, article, section, div, span, p")];
              const found = [];
              for (const block of blocks) {
                const text = clean(block.innerText || block.textContent || "");
                if (text.length < 3 || text.length > 90) continue;
                if (!labels.some((label) => text.toLowerCase().includes(label))) continue;
                if (!found.includes(text)) found.push(text);
              }
              return found.slice(0, 10);
            }
            """
        )
        return [self._clean_text(value) for value in values if self._clean_text(value)]

    def _clean_name(self, value: str) -> str:
        value = self._clean_text(value)
        value = re.sub(r"^(meta|tier|rang|niveau)\s+", "", value, flags=re.IGNORECASE)
        return value[:80]

    def _clean_tier(self, value: str) -> str:
        value = self._clean_text(value).upper()
        match = re.search(r"\b(S\+?|A\+?|B\+?|C\+?|D\+?)\b", value)
        return match.group(1) if match else ""

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()
