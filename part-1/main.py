from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import create_tables
from app.api.routes import auth, rides, driver

# ─── Create FastAPI App ───────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## 🚖 Cab Booking API — Part 1

    ### Features included in Part 1:
    - ✅ **Authentication** — Register, Login, JWT tokens, Role-based access
    - ✅ **Ride Booking** — Book rides, Fare estimate, Cancel rides, Ride history
    - ✅ **Driver Dashboard** — Go online/offline, Accept/reject rides, Earnings

    ### Roles:
    - **rider** — Can book rides
    - **driver** — Can accept/complete rides
    - **admin** — Full access

    ### How to use:
    1. Register as a rider or driver
    2. Login to get your JWT token
    3. Click **Authorize** button above and paste your token
    4. Use the APIs!
    """,
    version="1.0.0",
    debug=settings.DEBUG,
)

# ─── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routes ─────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api")
app.include_router(rides.router, prefix="/api")
app.include_router(driver.router, prefix="/api")


# ─── Startup Event ────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    """Create database tables on startup."""
    create_tables()
    print("✅ Database tables created")
    print(f"✅ {settings.APP_NAME} started successfully")


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
