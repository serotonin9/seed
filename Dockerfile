FROM python:3.10.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    --use-deprecated=legacy-resolver \
    -r requirements.txt

COPY . .

CMD ["python", "seed.py"]
