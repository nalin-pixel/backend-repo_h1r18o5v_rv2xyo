"""
Database Schemas for AR-Infused Hotel Universe

Each Pydantic model maps to a MongoDB collection (lowercased class name).
Use these schemas for validation and to power the concierge and content APIs.
"""
from pydantic import BaseModel, Field
from typing import Optional, List

class Room(BaseModel):
    name: str = Field(..., description="Room name, e.g., Sky Suite")
    description: Optional[str] = Field(None)
    price_per_night: float = Field(..., ge=0)
    view: Optional[str] = Field(None, description="e.g., ocean, city, garden")
    capacity: int = Field(2, ge=1)
    features: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)

class Dish(BaseModel):
    name: str
    category: str = Field(..., description="e.g., appetizer, main, dessert")
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    calories: Optional[int] = None
    allergens: List[str] = Field(default_factory=list)
    ingredients: List[str] = Field(default_factory=list)
    models: List[str] = Field(default_factory=list, description="URLs/ids for 3D models")

class Experience(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = Field(..., description="spa, pool, gym, restaurant, sky lounge")
    duration_minutes: Optional[int] = None
    images: List[str] = Field(default_factory=list)

class Preference(BaseModel):
    dietary: Optional[List[str]] = None
    mood: Optional[str] = Field(None, description="calm, energetic, romantic, etc.")
    budget_level: Optional[str] = Field(None, description="low, medium, high")
    language: Optional[str] = Field(None)
    sleep_time: Optional[str] = Field(None)

class BookingRequest(BaseModel):
    room_id: Optional[str] = None
    check_in: str
    check_out: str
    guests: int = Field(1, ge=1)
    addons: List[str] = Field(default_factory=list)

# Example legacy schemas retained for backward-compat
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
