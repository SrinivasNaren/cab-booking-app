import math
import googlemaps
from typing import Optional
from app.core.config import settings


# ── Initialize Google Maps Client ─────────────────────────────────────────────
def get_gmaps_client():
    if not settings.GOOGLE_MAPS_API_KEY:
        return None
    return googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)


class MapsService:

    # ── Haversine Fallback (when no API key) ──────────────────────────────────
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate straight-line distance between two coordinates in km."""
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return round(R * 2 * math.asin(math.sqrt(a)), 2)

    # ── Get Distance & Duration via Google Maps ───────────────────────────────
    @staticmethod
    def get_distance_and_duration(
        origin_lat: float, origin_lng: float,
        dest_lat: float, dest_lng: float
    ) -> dict:
        """
        Get road distance and ETA between two points.
        Falls back to Haversine formula if no API key is configured.
        """
        gmaps = get_gmaps_client()

        if gmaps:
            try:
                result = gmaps.distance_matrix(
                    origins=[(origin_lat, origin_lng)],
                    destinations=[(dest_lat, dest_lng)],
                    mode="driving",
                    units="metric"
                )
                element = result["rows"][0]["elements"][0]

                if element["status"] == "OK":
                    distance_m = element["distance"]["value"]
                    duration_s = element["duration"]["value"]
                    return {
                        "distance_km": round(distance_m / 1000, 2),
                        "duration_minutes": round(duration_s / 60),
                        "source": "google_maps",
                    }
            except Exception as e:
                print(f"Google Maps API error: {e}. Falling back to Haversine.")

        # Fallback to Haversine
        distance = MapsService.haversine_distance(origin_lat, origin_lng, dest_lat, dest_lng)
        return {
            "distance_km": distance,
            "duration_minutes": int(distance * 3),   # ~3 min per km estimate
            "source": "haversine_fallback",
        }

    # ── Geocode Address to Coordinates ────────────────────────────────────────
    @staticmethod
    def geocode(address: str) -> Optional[dict]:
        """Convert a text address to lat/lng coordinates."""
        gmaps = get_gmaps_client()
        if not gmaps:
            return None

        try:
            result = gmaps.geocode(address)
            if result:
                location = result[0]["geometry"]["location"]
                return {
                    "latitude": location["lat"],
                    "longitude": location["lng"],
                    "formatted_address": result[0]["formatted_address"],
                }
        except Exception as e:
            print(f"Geocoding error: {e}")
        return None

    # ── Reverse Geocode (Coordinates → Address) ───────────────────────────────
    @staticmethod
    def reverse_geocode(lat: float, lng: float) -> Optional[str]:
        """Convert lat/lng to a human-readable address."""
        gmaps = get_gmaps_client()
        if not gmaps:
            return f"{lat}, {lng}"

        try:
            result = gmaps.reverse_geocode((lat, lng))
            if result:
                return result[0]["formatted_address"]
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
        return None

    # ── Find Nearby Drivers ───────────────────────────────────────────────────
    @staticmethod
    def find_nearby_drivers(
        pickup_lat: float,
        pickup_lng: float,
        drivers: list,
        radius_km: float = 5.0
    ) -> list:
        """
        Filter drivers within a given radius of the pickup point.
        Returns drivers sorted by distance (nearest first).
        """
        nearby = []
        for driver in drivers:
            if driver.current_latitude is None or driver.current_longitude is None:
                continue

            distance = MapsService.haversine_distance(
                pickup_lat, pickup_lng,
                driver.current_latitude, driver.current_longitude
            )

            if distance <= radius_km:
                nearby.append({
                    "driver": driver,
                    "distance_km": distance,
                })

        # Sort by nearest first
        nearby.sort(key=lambda x: x["distance_km"])
        return nearby
