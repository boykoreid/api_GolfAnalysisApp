from fastapi import FastAPI
from .database import Base, engine
from .routers import auth, admin, users, rounds, stats
from .models import Rounds

app = FastAPI()

@app.get("/")
def healthy():
    return {"status": "ok"}

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(rounds.router)
app.include_router(stats.router)