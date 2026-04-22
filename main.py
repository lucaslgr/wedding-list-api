from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.admin import router as admin_router
from api.user import router as user_router
from infra.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Wedding List API", lifespan=lifespan)


app.include_router(user_router)
app.include_router(admin_router)
