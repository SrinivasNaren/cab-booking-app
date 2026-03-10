# 🚖 Cab Booking App — Part 1 (FastAPI + PostgreSQL)

## Project Structure

```
cab_booking/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py          # Login, Register, Profile
│   │       ├── rides.py         # Book, Cancel, History
│   │       └── driver.py        # Accept, Complete, Earnings
│   ├── core/
│   │   ├── config.py            # Environment settings
│   │   └── security.py          # JWT, BCrypt, RBAC
│   ├── db/
│   │   └── database.py          # PostgreSQL connection
│   ├── models/
│   │   ├── user.py              # User table
│   │   ├── driver.py            # Driver table
│   │   └── ride.py              # Ride table
│   ├── schemas/
│   │   ├── auth.py              # Request/Response models (auth)
│   │   └── ride.py              # Request/Response models (rides)
│   ├── services/
│   │   ├── auth_service.py      # Auth business logic
│   │   ├── ride_service.py      # Ride + fare logic
│   │   └── driver_service.py    # Driver dashboard logic
│   └── main.py                  # App entry point
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone and create virtual environment
```bash
git clone <your-repo>
cd cab_booking
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup PostgreSQL
```sql
CREATE DATABASE cab_booking_db;
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env with your database credentials and secret key
```

### 5. Run the server
```bash
uvicorn app.main:app --reload
```

### 6. Open API docs
```
http://localhost:8000/docs
```

---

## API Endpoints — Part 1

### 🔐 Authentication
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/auth/register/rider | Register as rider | ❌ |
| POST | /api/auth/register/driver | Register as driver | ❌ |
| POST | /api/auth/login | Login and get token | ❌ |
| POST | /api/auth/refresh | Refresh access token | ❌ |
| GET | /api/auth/me | Get my profile | ✅ |
| PATCH | /api/auth/me | Update my profile | ✅ |

### 🚗 Ride Booking (Rider)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/rides/estimate | Estimate fare | ❌ |
| POST | /api/rides/book | Book a ride | ✅ Rider |
| GET | /api/rides/{id} | Get ride details | ✅ |
| POST | /api/rides/{id}/cancel | Cancel a ride | ✅ Rider |
| GET | /api/rides/history/me | My ride history | ✅ Rider |

### 🧑‍✈️ Driver Dashboard
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| PATCH | /api/driver/status | Go online/offline | ✅ Driver |
| PATCH | /api/driver/location | Update GPS location | ✅ Driver |
| GET | /api/driver/rides/available | View ride requests | ✅ Driver |
| POST | /api/driver/rides/{id}/accept | Accept a ride | ✅ Driver |
| POST | /api/driver/rides/{id}/reject | Reject a ride | ✅ Driver |
| POST | /api/driver/rides/{id}/start | Start the ride | ✅ Driver |
| POST | /api/driver/rides/{id}/complete | Complete the ride | ✅ Driver |
| GET | /api/driver/rides/history | Past rides | ✅ Driver |
| GET | /api/driver/earnings | Earnings summary | ✅ Driver |

---

## Ride Status Flow
```
REQUESTED → ACCEPTED → ONGOING → COMPLETED
                              ↘ CANCELLED
```

## Fare Calculation
```
Total Fare = Base Fare + (Distance × Per KM Rate) + (Duration × Per Min Rate)

Vehicle    Base    Per KM   Per Min
bike       ₹15     ₹7       ₹0.5
auto       ₹25     ₹12      ₹1.0
mini       ₹40     ₹15      ₹1.5
sedan      ₹60     ₹18      ₹2.0
suv        ₹100    ₹25      ₹2.5
```

---

## Part 2 Preview (Coming Next)
- 🗺️ Google Maps Integration
- ⚡ Real-Time WebSockets
- 💳 Stripe Payments
- ⭐ Ratings & Reviews
- 🐳 Docker & Deployment
