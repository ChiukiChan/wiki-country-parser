from pydantic import BaseModel


class CapitalInfo(BaseModel):
    country: str
    capital: str
    description: str | None


class CapitalInfoNoDesc(BaseModel):
    country: str
    capital: str
    description_href: str | None
