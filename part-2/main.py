from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.api.routes import maps, payments, ratings, admin, receipts
from app.websockets.routes import router as ws_router

# ── Create App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## 🚖 Cab Booking API — Part 2

    ### New Features in Part 2:
    - 🗺️ **Maps & Location** — Google Maps distance, geocoding, ETA
    - ⚡ **WebSockets** — Real-time ride updates, driver tracking, SOS
    - 💳 **Stripe Payments** — PaymentIntent, webhooks, refunds
    - ⭐ **Ratings & Reviews** — Rate driver/rider after ride
    - 📄 **PDF Receipts** — Download or email ride receipts
    - 🛡️ **Admin Dashboard** — Stats, user management, revenue
    - 🐳 **Docker Ready** — docker-compose.yml included

    ### WebSocket Endpoints:
    - `ws://localhost:8000/ws/rider/{user_id}?token=JWT`
    - `ws://localhost:8000/ws/driver/{user_id}?token=JWT`
    - `ws://localhost:8000/ws/ride/{ride_id}?token=JWT`
    - `ws://localhost:8000/ws/admin?token=JWT`
    """,
    version="2.0.0",
    debug=settings.DEBUG,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Create receipts folder ────────────────────────────────────────────────────
os.makedirs("receipts", exist_ok=True)

# ── Register REST Routes ──────────────────────────────────────────────────────
app.include_router(maps.router,     prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(ratings.router,  prefix="/api")
app.include_router(admin.router,    prefix="/api")
app.include_router(receipts.router, prefix="/api")

# ── Register WebSocket Routes ─────────────────────────────────────────────────
app.include_router(ws_router)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "websocket_docs": "See /docs for WebSocket endpoint details",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
