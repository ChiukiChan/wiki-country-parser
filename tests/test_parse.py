from pathlib import Path

import aiohttp
import pytest

import src.main
from src.models import CapitalInfo

INDEX_HTML = """
<html><body>
<table class="wikitable">
  <tr><th>Государство</th><th>Столица</th></tr>
  <tr>
    <td>Нидерланды</td>
    <td><a href="/wiki/%D0%90%D0%BC%D1%81%D1%82%D0%B5%D1%80%D0%B4%D0%B0%D0%BC">Амстердам</a></td>
  </tr>
</table>
</body></html>
"""


CAPITAL_HTML = Path(__file__).with_name("capital.html").read_text(encoding="utf-8")


EXPECTED_DESC = (
    "Амстердам — столица и крупнейший город Нидерландов. "
    "Согласно конституции Нидерландов, с 1814 года является столицей королевства, "
    "при этом правительство, парламент и верховный суд располагаются в Гааге."
)


@pytest.mark.asyncio
async def test_parse_capitals_monkeypatched(monkeypatch):
    async def fake_fetch_html(session: aiohttp.ClientSession, url: str) -> str:
        if "Список_столиц_государств" in url:
            return INDEX_HTML
        return CAPITAL_HTML

    class _DummyConn:
        async def close(self): ...

    async def fake_open_db():
        return _DummyConn()

    async def fake_get_cached(conn, country, capital):
        return None

    async def fake_upsert(conn, country, capital, description): ...

    monkeypatch.setattr(src.main, "fetch_html", fake_fetch_html)
    monkeypatch.setattr(src.main, "open_db", fake_open_db)
    monkeypatch.setattr(src.main, "get_cached", fake_get_cached)
    monkeypatch.setattr(src.main, "upsert", fake_upsert)

    out = await src.main.parse_capitals()
    assert isinstance(out, list) and all(isinstance(x, CapitalInfo) for x in out)
    ams = next(x for x in out if x.capital == "Амстердам")
    assert ams.description == EXPECTED_DESC
