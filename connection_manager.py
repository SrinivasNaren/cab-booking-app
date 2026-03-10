from fastapi import WebSocket
from typing import Dict, List
import json


class ConnectionManager:
    """
    Manages all active WebSocket connections.

    Connections are stored by category:
    - ride_{ride_id}  → rider and driver of that specific ride
    - driver_{user_id} → individual driver connection
    - rider_{user_id}  → individual rider connection
    - admin            → all admin connections
    """

    def __init__(self):
        # room_id → list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    # ── Connect ───────────────────────────────────────────────────────────────
    async def connect(self, websocket: WebSocket, room_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        print(f"WebSocket connected: room={room_id} | total={len(self.active_connections[room_id])}")

    # ── Disconnect ────────────────────────────────────────────────────────────
    def disconnect(self, websocket: WebSocket, room_id: str):
        """Remove a WebSocket connection from its room."""
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        print(f"WebSocket disconnected: room={room_id}")

    # ── Send to a Specific Room ───────────────────────────────────────────────
    async def send_to_room(self, room_id: str, message: dict):
        """Broadcast a message to all connections in a room."""
        if room_id not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[room_id]:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection)

        # Clean up dead connections
        for conn in disconnected:
            self.active_connections[room_id].remove(conn)

    # ── Send to a Specific User ───────────────────────────────────────────────
    async def send_to_user(self, user_id: int, role: str, message: dict):
        """Send a message to a specific user's personal room."""
        room_id = f"{role}_{user_id}"
        await self.send_to_room(room_id, message)

    # ── Broadcast to All Admins ───────────────────────────────────────────────
    async def broadcast_to_admins(self, message: dict):
        """Send a message to all connected admins."""
        await self.send_to_room("admin", message)

    # ── Ride Room Helpers ─────────────────────────────────────────────────────
    async def notify_ride_update(self, ride_id: int, event: str, data: dict):
        """
        Broadcast ride status update to everyone in the ride room.
        Used for: ride accepted, driver arriving, ride started, ride completed.
        """
        message = {
            "event": event,
            "ride_id": ride_id,
            "data": data,
        }
        await self.send_to_room(f"ride_{ride_id}", message)

    async def notify_driver_new_ride(self, driver_user_id: int, ride_data: dict):
        """Notify a specific driver about a new ride request."""
        await self.send_to_user(driver_user_id, "driver", {
            "event": "new_ride_request",
            "data": ride_data,
        })

    async def broadcast_sos(self, ride_id: int, rider_name: str, location: dict):
        """Broadcast SOS alert to all admins."""
        await self.broadcast_to_admins({
            "event": "sos_alert",
            "ride_id": ride_id,
            "rider_name": rider_name,
            "location": location,
            "message": f"SOS ALERT from {rider_name} on ride #{ride_id}",
        })


# ── Global singleton instance ─────────────────────────────────────────────────
manager = ConnectionManager()
