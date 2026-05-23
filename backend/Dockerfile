FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose FastAPI port (configurable via PORT env var)
EXPOSE 8000

# Default port
ENV PORT=8000

# Run the FastAPI application with uvicorn using shell form for env var substitution
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
