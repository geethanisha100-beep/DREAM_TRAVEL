"""FastAPI service powering the Home page data. Run: uvicorn api:app --port 8001"""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dreamtravel.settings")
django.setup()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.models import Package, Vehicle, Hotel

app = FastAPI(title="Dream Travel API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])

@app.get("/api/packages")
def packages():
    return list(Package.objects.filter(available=True).values("id", "destination", "title", "amount", "duration", "seats"))

@app.get("/api/vehicles")
def vehicles(type: str | None = None):
    qs = Vehicle.objects.filter(available=True)
    return list(qs.filter(vehicle_type=type).values() if type else qs.values("id", "name", "model_name", "vehicle_type", "amount"))

@app.get("/api/hotels")
def hotels():
    return list(Hotel.objects.filter(available=True).values("id", "name", "location", "room_type", "rating", "amount"))

@app.get("/api/home")
def home():
    return {"packages": packages()[:3], "vehicles": vehicles()[:3], "hotels": hotels()[:3]}
