from fastapi import FastAPI
from .database import engine, Base
from .routers import auth, user

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(user.router)
