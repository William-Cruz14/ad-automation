from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from decouple import config

SQLALCHEMY_DATABASE_URL = config("DATABASE_URL")
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)



async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()
