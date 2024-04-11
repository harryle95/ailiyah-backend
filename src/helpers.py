from collections.abc import AsyncGenerator

from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import (
    autocommit_before_send_handler,
)
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyAsyncConfig
from litestar.exceptions import ClientException
from litestar.status_codes import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from sqlalchemy import Engine, event
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from src.model.base import Base

__all__ = (
    "create_db_config",
    "provide_transaction",
    "set_sqlite_pragma",
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def provide_transaction(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    try:
        async with db_session.begin():
            yield db_session
    except IntegrityError as exc:
        raise ClientException(
            status_code=HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except NoResultFound as exc:
        raise ClientException(status_code=HTTP_404_NOT_FOUND, detail="No database result matching query") from exc


def create_db_config(sqlite_db: str) -> SQLAlchemyAsyncConfig:
    return SQLAlchemyAsyncConfig(
        connection_string=f"sqlite+aiosqlite:///{sqlite_db}",
        metadata=Base.metadata,
        create_all=True,
        before_send_handler=autocommit_before_send_handler,
    )
