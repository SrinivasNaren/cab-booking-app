# 🚖 Cab Booking App — Part 2 (Advanced Features + Deployment)

## What's New in Part 2

| Feature | File | Description |
|---|---|---|
| 🗺️ Google Maps | `services/maps_service.py` | Distance, ETA, geocoding |
| ⚡ WebSockets | `websockets/` | Real-time tracking, SOS alerts |
| 💳 Stripe Payments | `services/payment_service.py` | PaymentIntent, webhooks, refunds |
| ⭐ Ratings | `services/rating_service.py` | Rate driver/rider, avg calculation |
| 📄 PDF Receipt | `services/pdf_service.py` | ReportLab PDF generation |
| 📧 Email | `services/email_service.py` | HTML email + PDF attachment |
| 🛡️ Admin | `services/admin_service.py` | Stats, user mgmt, revenue |
| 🐳 Docker | `Dockerfile` + `docker-compose.yml` | Full containerization |
| 🌐 Nginx | `nginx/nginx.conf` | Reverse proxy + WS support |
| 🚀 CI/CD | `.github/workflows/deploy.yml` | Auto test → build → deploy |

---

## Project Structure

```
cab_booking_part2/
├── app/
│   ├── api/routes/
│   │   ├── maps.py           # Maps & geocoding endpoints
│   │   ├── payments.py       # Stripe payment endpoints
│   │   ├── ratings.py        # Rating endpoints
│   │   ├── admin.py          # Admin dashboard endpoints
│   │   └── receipts.py       # PDF download & email endpoints
│   ├── core/
│   │   └── config.py         # All environment settings
│   ├── db/
│   │   └── database.py       # PostgreSQL connection
│   ├── models/
│   │   ├── rating.py         # Rating table
│   │   └── payment.py        # Payment table
│   ├── services/
│   │   ├── maps_service.py   # Google Maps + Haversine fallback
│   │   ├── payment_service.py# Stripe integration
│   │   ├── pdf_service.py    # ReportLab PDF generation
│   │   ├── email_service.py  # SMTP email sender
│   │   ├── rating_service.py # Rating logic + avg calculation
│   │   └── admin_service.py  # Admin operations
│   ├── websockets/
│   │   ├── connection_manager.py  # WS room management
│   │   └── routes.py              # WS endpoints
│   └── main.py               # App entry point
├── nginx/
│   └── nginx.conf            # Reverse proxy config
├── .github/workflows/
│   └── deploy.yml            # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Quick Start

### Option A — Local Development
```bash
pip install -r requirements.txt
cp .env.example .env        # Fill in your API keys
uvicorn app.main:app --reload
```

### Option B — Docker (Recommended)
```bash
cp .env.example .env        # Fill in your API keys
docker compose up --build
```
App will be live at `http://localhost` (via Nginx)

---

## API Endpoints — Part 2

### 🗺️ Maps
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/maps/distance | Get distance & ETA between 2 points |
| POST | /api/maps/geocode | Address → coordinates |
| GET | /api/maps/reverse-geocode | Coordinates → address |

### 💳 Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/payments/create-intent/{ride_id} | Create Stripe payment |
| POST | /api/payments/webhook | Stripe webhook (auto-called) |
| GET | /api/payments/status/{ride_id} | Check payment status |
| POST | /api/payments/refund/{ride_id} | Issue refund (Admin) |

### ⭐ Ratings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/ratings/ride/{id}/rate-driver | Rider rates driver |
| POST | /api/ratings/ride/{id}/rate-rider | Driver rates rider |
| GET | /api/ratings/ride/{id} | Get ride's ratings |
| GET | /api/ratings/driver/{id} | Get driver's all ratings |

### 📄 Receipts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/receipts/download/{ride_id} | Download PDF receipt |
| POST | /api/receipts/email/{ride_id} | Email receipt to rider |

### 🛡️ Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/admin/stats | Platform overview stats |
| GET | /api/admin/users | All users (filter by role) |
| PATCH | /api/admin/users/{id}/toggle-status | Suspend/activate user |
| PATCH | /api/admin/drivers/{id}/verify | Verify a driver |
| GET | /api/admin/rides | All rides (filter by status) |
| GET | /api/admin/payments | All transactions |
| GET | /api/admin/revenue | Revenue report |

### ⚡ WebSockets
| Endpoint | Who | Receives |
|----------|-----|---------|
| `ws://host/ws/rider/{id}?token=JWT` | Rider | ride updates, driver location |
| `ws://host/ws/driver/{id}?token=JWT` | Driver | new ride requests |
| `ws://host/ws/ride/{id}?token=JWT` | Both | all ride room events |
| `ws://host/ws/admin?token=JWT` | Admin | SOS alerts |

---

## WebSocket Events Reference

### Events Rider Receives:
```json
{ "event": "ride_accepted",   "ride_id": 1, "data": {...} }
{ "event": "driver_location", "ride_id": 1, "data": { "latitude": 19.07, "longitude": 72.87 } }
{ "event": "ride_started",    "ride_id": 1, "data": {...} }
{ "event": "ride_completed",  "ride_id": 1, "data": { "fare": 245.50 } }
```

### Events Driver Receives:
```json
{ "event": "new_ride_request", "data": { "pickup": "...", "drop": "...", "fare": 200 } }
{ "event": "ride_cancelled",   "data": { "ride_id": 1, "reason": "..." } }
```

### SOS (Rider Sends):
```json
{ "event": "sos", "ride_id": 1, "rider_name": "John", "location": { "lat": 19.07, "lng": 72.87 } }
```

---

## CI/CD Secrets Required (GitHub)
Add these in GitHub → Settings → Secrets:
- `DOCKER_USERNAME` / `DOCKER_PASSWORD`
- `SERVER_HOST` / `SERVER_USER` / `SERVER_SSH_KEY`
