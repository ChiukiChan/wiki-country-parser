from aiohttp import ClientError
from fastapi import FastAPI, HTTPException, Query, Request, status
from loguru import logger

from .main import CapitalInfo, parse_capitals

app = FastAPI()


@app.get(
    "/capitals",
    responses={
        200: {
            "description": "OK",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "country": "Нидерланды",
                            "capital": "Амстердам",
                            "description": (
                                "Амстердам — столица и крупнейший город Нидерландов. "
                                "Согласно конституции Нидерландов, с 1814 года является столицей королевства, при этом "
                                "правительство, парламент и верховный суд располагаются в Гааге."
                            ),
                        }
                    ]
                }
            },
        },
        404: {
            "description": "Not Found",
            "content": {"application/json": {"example": {"detail": "No results for country: Австрия"}}},
        },
        502: {
            "description": "Bad Gateway",
            "content": {"application/json": {"example": {"detail": "Upstream HTTP error while fetching data"}}},
        },
        504: {
            "description": "Gateway Timeout",
            "content": {"application/json": {"example": {"detail": "Timeout while fetching data"}}},
        },
        500: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Unexpected error"}}},
        },
    },
)
async def get_capitals(request: Request, country: str | None = Query(None)) -> list[CapitalInfo]:
    """
    Возвращает список столиц в формате JSON.

    Источник данных — страница Википедии "Список столиц государств". Для каждой столицы
    дополнительно извлекается её описание.
    """
    try:
        data = await parse_capitals()
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout while fetching data",
        )
    except ClientError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream HTTP error while fetching data",
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error")
    if not data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error")
    if country:
        key = country.casefold().strip()
        data = [x for x in data if key in x.country.casefold()]
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No results for country: {country}",
            )
    return data
