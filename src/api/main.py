import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.api.database import Base, engine
from src.api.routers import auth, images, dashboard

# Initialize Database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RA-MIE Image Encryption API (Production)", version="2.0.0")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def read_root():
    return RedirectResponse(url="/static/personal.html")

@app.get("/hospital")
def read_hospital():
    return RedirectResponse(url="/static/hospital_login.html")

# Include Routers
app.include_router(auth.router)
app.include_router(images.router)
app.include_router(dashboard.router)
