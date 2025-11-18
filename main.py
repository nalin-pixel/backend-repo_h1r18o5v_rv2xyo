import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Room, Dish, Experience, Preference, BookingRequest

app = FastAPI(title="AR-Infused Hotel Universe API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AR Hotel Universe Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
            except Exception as e:
                response["database"] = f"⚠️ Connected but error listing collections: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response

# ----- Content seed endpoints (idempotent) -----
class SeedResponse(BaseModel):
    inserted: int

@app.post("/seed/rooms", response_model=SeedResponse)
def seed_rooms():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    existing = db["room"].count_documents({})
    if existing > 0:
        return SeedResponse(inserted=0)
    rooms = [
        Room(
            name="Sky Suite",
            description="Penthouse with panoramic skyline views and holographic ambient lighting.",
            price_per_night=899,
            view="city",
            capacity=2,
            features=["holographic desk", "smart glass walls", "immersive audio"],
            images=["/images/rooms/sky-suite-1.jpg"],
        ),
        Room(
            name="Ocean Nebula",
            description="Futuristic ocean-facing room with neon wave lighting and AR balcony guide.",
            price_per_night=659,
            view="ocean",
            capacity=3,
            features=["neon wave lights", "ar balcony guide", "ai butler"],
            images=["/images/rooms/ocean-nebula-1.jpg"],
        ),
    ]
    inserted = 0
    for r in rooms:
        create_document("room", r)
        inserted += 1
    return SeedResponse(inserted=inserted)

@app.post("/seed/dishes", response_model=SeedResponse)
def seed_dishes():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    existing = db["dish"].count_documents({})
    if existing > 0:
        return SeedResponse(inserted=0)
    dishes = [
        Dish(
            name="Galactic Nigiri",
            category="main",
            description="Bluefin with edible stardust and yuzu nebula gel.",
            price=42.0,
            calories=320,
            allergens=["fish", "soy"],
            ingredients=["tuna", "rice", "yuzu", "soy"],
            models=["/models/dishes/nigiri.glb"],
        ),
        Dish(
            name="Quantum Mousse",
            category="dessert",
            description="Dark chocolate sphere with liquid light core.",
            price=18.0,
            calories=540,
            allergens=["dairy"],
            ingredients=["cacao", "cream", "sugar"],
            models=["/models/dishes/mousse.glb"],
        ),
    ]
    inserted = 0
    for d in dishes:
        create_document("dish", d)
        inserted += 1
    return SeedResponse(inserted=inserted)

@app.post("/seed/experiences", response_model=SeedResponse)
def seed_experiences():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    existing = db["experience"].count_documents({})
    if existing > 0:
        return SeedResponse(inserted=0)
    exps = [
        Experience(
            title="Zero-Gravity Spa",
            description="Float therapy with ambient galaxy soundscapes.",
            category="spa",
            duration_minutes=60,
            images=["/images/experiences/spa-zerog.jpg"],
        ),
        Experience(
            title="Sky Lounge VR Tour",
            description="360° tour of the sky lounge with sunrise simulation.",
            category="sky lounge",
            duration_minutes=15,
            images=["/images/experiences/sky-lounge.jpg"],
        ),
    ]
    inserted = 0
    for e in exps:
        create_document("experience", e)
        inserted += 1
    return SeedResponse(inserted=inserted)

# ----- Public content APIs -----
@app.get("/rooms")
def list_rooms(view: Optional[str] = Query(None), capacity: Optional[int] = Query(None)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt = {}
    if view:
        filt["view"] = view
    if capacity:
        filt["capacity"] = {"$gte": capacity}
    return get_documents("room", filt)

@app.get("/menu")
def list_menu(category: Optional[str] = Query(None)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt = {"category": category} if category else {}
    return get_documents("dish", filt)

@app.get("/experiences")
def list_experiences(category: Optional[str] = Query(None)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt = {"category": category} if category else {}
    return get_documents("experience", filt)

# ----- Concierge suggestion (very simple rule-based placeholder) -----
class ConciergeResponse(BaseModel):
    greeting: str
    suggestions: List[dict]

@app.post("/concierge", response_model=ConciergeResponse)
def concierge(pref: Preference):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Basic filtering based on mood/dietary; real system would use embeddings
    menu = list(db["dish"].find({}))
    exps = list(db["experience"].find({}))

    suggested_dishes = []
    if pref.dietary:
        avoid = set(a.lower() for a in pref.dietary)
        for d in menu:
            if not any(a.lower() in avoid for a in d.get("allergens", [])):
                suggested_dishes.append(d)
    else:
        suggested_dishes = menu[:3]

    suggested_exps = exps[:3]

    return ConciergeResponse(
        greeting=f"Welcome to the AR Hotel Universe{', ' + pref.language if pref.language else ''}!",
        suggestions=[
            {"type": "dish", "items": suggested_dishes},
            {"type": "experience", "items": suggested_exps},
        ],
    )

# ----- Booking quote (simple price calc with AI-price-like optimization) -----
class QuoteRequest(BookingRequest):
    pass

class QuoteResponse(BaseModel):
    nightly_rate: float
    nights: int
    addons: List[dict]
    total: float
    suggestion: Optional[str] = None

@app.post("/booking/quote", response_model=QuoteResponse)
def booking_quote(req: QuoteRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    from datetime import datetime
    d1 = datetime.fromisoformat(req.check_in)
    d2 = datetime.fromisoformat(req.check_out)
    nights = max(1, (d2 - d1).days)

    base_rate = 500.0
    if req.room_id:
        room = db["room"].find_one({"_id": {"$eq": db["room"].find_one({"_id": {"$exists": True}})["_id"]}}) if False else None
    # Simplified demand-based adjustment: weekends +10%
    weekend_boost = 1.1 if d1.weekday() >= 4 else 1.0
    nightly_rate = round(base_rate * weekend_boost, 2)

    addon_map = {
        "flowers": 60,
        "wine": 120,
        "candlelight": 200,
    }
    addons = [{"name": a, "price": addon_map.get(a, 50)} for a in (req.addons or [])]

    total = round(nightly_rate * nights + sum(a["price"] for a in addons), 2)
    suggestion = "Consider arriving Sunday night for better rates" if d1.weekday() == 5 else None

    return QuoteResponse(nightly_rate=nightly_rate, nights=nights, addons=addons, total=total, suggestion=suggestion)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
