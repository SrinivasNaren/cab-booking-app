from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
import json

from app.websockets.connection_manager import manager
from app.db.database import SessionLocal
from app.core.security import decode_token

router = APIRouter(tags=["WebSockets"])


def get_user_from_token(token: str):
    """Authenticate WebSocket connection using JWT token."""
    try:
        payload = decode_token(token)
        return {"user_id": int(payload["sub"]), "role": payload["role"]}
    except Exception:
        return None


# ── Rider WebSocket ───────────────────────────────────────────────────────────
@router.websocket("/ws/rider/{user_id}")
async def rider_websocket(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...),
):
    """
    WebSocket endpoint for riders.
    Riders receive:
    - ride_accepted      → A driver accepted your ride
    - driver_location    → Real-time driver GPS position
    - driver_arriving    → Driver is nearly at pickup
    - ride_started       → Ride has started
    - ride_completed     → Ride is done, fare summary
    """
    user = get_user_from_token(token)
    if not user or user["user_id"] != user_id:
        await websocket.close(code=4001)
        return

    room_id = f"rider_{user_id}"
    await manager.connect(websocket, room_id)

    try:
        while True:
            # Keep connection alive, listen for SOS from rider
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("event") == "sos":
                await manager.broadcast_sos(
                    ride_id=message.get("ride_id"),
                    rider_name=message.get("rider_name", "Unknown"),
                    location=message.get("location", {})
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)


# ── Driver WebSocket ──────────────────────────────────────────────────────────
@router.websocket("/ws/driver/{user_id}")
async def driver_websocket(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...),
):
    """
    WebSocket endpoint for drivers.
    Drivers receive:
    - new_ride_request   → A new ride is available nearby
    - ride_cancelled     → Rider cancelled after acceptance

    Drivers send:
    - location_update    → Driver broadcasts their GPS position
    """
    user = get_user_from_token(token)
    if not user or user["user_id"] != user_id:
        await websocket.close(code=4001)
        return

    room_id = f"driver_{user_id}"
    await manager.connect(websocket, room_id)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Driver sends location update → forward to rider in the ride room
            if message.get("event") == "location_update":
                ride_id = message.get("ride_id")
                if ride_id:
                    await manager.notify_ride_update(
                        ride_id=ride_id,
                        event="driver_location",
                        data={
                            "latitude": message.get("latitude"),
                            "longitude": message.get("longitude"),
                            "speed_kmh": message.get("speed_kmh", 0),
                        }
                    )

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)


# ── Ride Room WebSocket ────────────────────────────────────────────────────────
@router.websocket("/ws/ride/{ride_id}")
async def ride_websocket(
    websocket: WebSocket,
    ride_id: int,
    token: str = Query(...),
):
    """
    Shared ride room for both rider and driver.
    Both parties join this room when a ride is active.
    All ride lifecycle events are broadcast here.
    """
    user = get_user_from_token(token)
    if not user:
        await websocket.close(code=4001)
        return

    room_id = f"ride_{ride_id}"
    await manager.connect(websocket, room_id)

    # Announce someone joined
    await manager.send_to_room(room_id, {
        "event": "user_joined",
        "user_id": user["user_id"],
        "role": user["role"],
    })

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Echo chat messages within ride room
            if message.get("event") == "chat":
                await manager.send_to_room(room_id, {
                    "event": "chat",
                    "from_user_id": user["user_id"],
                    "role": user["role"],
                    "message": message.get("message", ""),
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)


# ── Admin WebSocket ───────────────────────────────────────────────────────────
@router.websocket("/ws/admin")
async def admin_websocket(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    Admin WebSocket room.
    Admins receive all SOS alerts and platform-wide events.
    """
    user = get_user_from_token(token)
    if not user or user["role"] != "admin":
        await websocket.close(code=4003)
        return

    await manager.connect(websocket, "admin")

    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, "admin")
