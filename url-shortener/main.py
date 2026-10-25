import secrets
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.config.setting import settings
from app.db.database import create_db_and_tables, get_session
from app.model.url import URL, ShortenRequest, URLRead, utc_now

CODE_LENGTH = 6
MAX_RETRIES = 5

RESERVED_CODES = {"shorten", "stats", "docs", "redoc", "openapi.json"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
SessionDep = Annotated[Session, Depends(get_session)]


# ---------- helpers ----------
def to_read(url: URL) -> URLRead:
    return URLRead(**url.model_dump(), short_url=f"{settings.BASE_URL}/{url.code}")


def get_url_or_404(session: Session, code: str) -> URL:
    url = session.exec(select(URL).where(URL.code == code)).first()
    if url is None:
        raise HTTPException(status_code=404, detail=f"Short link '{code}' not found")
    return url


def code_exists(session: Session, code: str) -> bool:
    return session.exec(select(URL.id).where(URL.code == code)).first() is not None


def generate_code(session: Session) -> str:
    """Random 6-character code (letters and digits), retried until unused."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    for _ in range(MAX_RETRIES):
        code = "".join(secrets.choice(alphabet) for _ in range(CODE_LENGTH))
        if code not in RESERVED_CODES and not code_exists(session, code):
            return code
    raise HTTPException(status_code=503, detail="Could not generate a unique code, try again")


# ---------- routes ----------
@app.get("/")
def home():
    return {"message": settings.APP_NAME}


@app.post("/shorten", response_model=URLRead, status_code=status.HTTP_201_CREATED)
def shorten(body: ShortenRequest, session: SessionDep):
    if body.custom_code:
        code = body.custom_code
        if code.lower() in RESERVED_CODES or code_exists(session, code):
            raise HTTPException(status_code=409, detail=f"Code '{code}' is already taken")
    else:
        code = generate_code(session)

    url = URL(code=code, original_url=str(body.url))
    session.add(url)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"Code '{code}' is already taken")
    session.refresh(url)
    return to_read(url)


@app.get("/stats/{code}", response_model=URLRead)
def get_stats(code: str, session: SessionDep):
    return to_read(get_url_or_404(session, code))


@app.get("/{code}")
def redirect(code: str, session: SessionDep):
    url = get_url_or_404(session, code)
    session.execute(
        update(URL)
        .where(URL.id == url.id)
        .values(count=URL.count + 1, last_visited=utc_now())
    )
    session.commit()
    return RedirectResponse(url.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_url(code: str, session: SessionDep):
    url = get_url_or_404(session, code)
    session.delete(url)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)