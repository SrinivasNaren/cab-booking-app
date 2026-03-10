from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

from app.services.maps_service import MapsService

router = APIRouter(prefix="/maps", tags=["Maps & Location"])


class DistanceRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float


class GeocodeRequest(BaseModel):
    address: str


# ── Get Distance & ETA ────────────────────────────────────────────────────────
@router.post("/distance")
def get_distance(data: DistanceRequest):
    """
    Get road distance and estimated travel time between two coordinates.
    Uses Google Maps Distance Matrix API (falls back to Haversine if no API key).
    """
    return MapsService.get_distance_and_duration(
        data.origin_lat, data.origin_lng,
        data.dest_lat, data.dest_lng
    )


# ── Geocode Address ───────────────────────────────────────────────────────────
@router.post("/geocode")
def geocode_address(data: GeocodeRequest):
    """
    Convert a text address to latitude/longitude coordinates.
    Example: "Bandra West, Mumbai" → {lat: 19.054, lng: 72.840}
    """
    result = MapsService.geocode(data.address)
    if not result:
        return {"error": "Could not geocode address. Check your Google Maps API key."}
    return result


# ── Reverse Geocode ───────────────────────────────────────────────────────────
@router.get("/reverse-geocode")
def reverse_geocode(
    lat: float = Query(..., example=19.0760),
    lng: float = Query(..., example=72.8777)
):
    """
    Convert coordinates to a human-readable address.
    Example: {lat: 19.076, lng: 72.877} → "Mumbai, Maharashtra, India"
    """
    address = MapsService.reverse_geocode(lat, lng)
    return {"address": address, "latitude": lat, "longitude": lng}
