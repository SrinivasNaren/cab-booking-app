# ── Base Image ────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ── Set Working Directory ─────────────────────────────────────────────────────
WORKDIR /app

# ── Install System Dependencies ───────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Copy Requirements ─────────────────────────────────────────────────────────
COPY requirements.txt .

# ── Install Python Dependencies ───────────────────────────────────────────────
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy Application Code ─────────────────────────────────────────────────────
COPY . .

# ── Create Receipts Directory ─────────────────────────────────────────────────
RUN mkdir -p receipts

# ── Expose Port ───────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Start Application ─────────────────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
