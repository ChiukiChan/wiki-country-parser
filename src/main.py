import asyncio
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from .db import get_cached, open_db, upsert
from .models import CapitalInfo, CapitalInfoNoDesc
from .settings import settings
from .utils import clean_desc, clean_name

WIKI_LIST_URL = "https://ru.wikipedia.org/wiki/Список_столиц_государств"
WIKI_BASE = "https://ru.wikipedia.org"


async def fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as r:
        r.raise_for_status()
        return await r.text()


def extract_rows_from_table(table) -> list[CapitalInfoNoDesc]:
    head = table.find("tr")
    if not head:
        return []
    ths = [clean_name(th.get_text(" ", strip=True)) for th in head.find_all(["th", "td"])]
    try:
        country_index = ths.index("Государство")
        capital_index = ths.index("Столица")
    except ValueError:
        if len(ths) >= 3:
            country_index, capital_index = 1, 2
        else:
            logger.warning("Skip table: unknown format of table {}", ths)
            return []
    out: list[CapitalInfoNoDesc] = []
    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all(["td", "th"])
        if len(tds) <= max(country_index, capital_index):
            continue
        country = clean_name(tds[country_index].get_text(" ", strip=True))
        ce = tds[capital_index]
        capital = clean_name(ce.get_text(" ", strip=True))
        a = ce.find("a", href=True)
        href = urljoin(WIKI_BASE, a["href"]) if a and not a["href"].startswith("#") else ""
        if country and capital:
            out.append(CapitalInfoNoDesc(country=country, capital=capital, description_href=href))
    return out


def extract_description_from_capital_soup(soup: BeautifulSoup) -> str | None:
    root = soup.select_one("#mw-content-text .mw-parser-output") or soup
    p = root.find("p", recursive=False) or root.find("p")
    return clean_desc(p.get_text(" ", strip=True)) if p else None


async def fetch_capital_description(
    session: aiohttp.ClientSession, url: str | None, sem: asyncio.Semaphore, conn, country: str, capital: str
) -> str | None:
    cached = await get_cached(conn, country, capital)
    if cached is not None:
        return cached
    if not url:
        return None
    async with sem:
        html = await fetch_html(session, url)
    if not html:
        return None

    soup = BeautifulSoup(html, "lxml")
    desc = extract_description_from_capital_soup(soup)
    await upsert(conn, country, capital, desc)
    return desc


async def parse_capitals_html(session: aiohttp.ClientSession) -> list[CapitalInfoNoDesc]:
    """Сбор стран и столиц с главной страницы"""
    html = await fetch_html(session, WIKI_LIST_URL)
    soup = BeautifulSoup(html, "lxml")
    rows: list[CapitalInfoNoDesc] = []
    tables = soup.select("table.wikitable")
    if not tables:
        logger.warning("No wikitable found on index page")
    for table in tables:
        rows.extend(extract_rows_from_table(table))
    if not rows:
        logger.warning("No rows extracted from index page")
    return rows


async def parse_capitals() -> list[CapitalInfo]:
    headers = {"User-Agent": settings.REQUEST_USER_AGENT}
    timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT_SECONDS)
    conn = await open_db()
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            pre_model = await parse_capitals_html(session)
            sem = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)

            results: list[CapitalInfo] = []

            async def worker(item: CapitalInfoNoDesc) -> None:
                desc = await fetch_capital_description(
                    session, item.description_href, sem, conn, item.country, item.capital
                )
                results.append(CapitalInfo(country=item.country, capital=item.capital, description=desc))

            async with asyncio.TaskGroup() as tg:
                for item in pre_model:
                    tg.create_task(worker(item))

            return results
    finally:
        await conn.close()
