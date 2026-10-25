from datetime import datetime, timezone
from typing import Annotated

from pydantic import HttpUrl, StringConstraints
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


CustomCode = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{3,30}$")]


# ---------- database table ----------
class URL(SQLModel, table=True):
    __tablename__ = "urls"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=30)
    original_url: str
    count: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    last_visited: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )


# ---------- API models (not tables) ----------
class ShortenRequest(SQLModel):
    """JSON body for POST /shorten."""
    url: HttpUrl                    
    custom_code: CustomCode | None = None


class URLRead(SQLModel):
    """What the API returns for a link."""
    code: str
    short_url: str                   
    original_url: str
    count: int
    created_at: datetime
    last_visited: datetime | None